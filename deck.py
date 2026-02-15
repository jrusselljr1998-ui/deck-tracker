import json
import os
import difflib
from typing import Optional

from card import CardEntry, normalize_name


class Deck:
    def __init__(self) -> None:
        # key -> CardEntry (unique by normalized name)
        self._cards: dict[str, CardEntry] = {}

    # ---------- Core CRUD ----------
    def add_card(self, name: str, mana_cost: str, card_type: str, qty: int = 1) -> None:
        if qty <= 0:
            return
        entry = CardEntry(
            name=name.strip(),
            mana_cost_raw=mana_cost.strip(),
            card_type=card_type.strip(),
            qty=qty,
        )
        key = entry.key
        if key in self._cards:
            self._cards[key].qty += qty
        else:
            self._cards[key] = entry

    def remove_one(self, name: str) -> bool:
        key = normalize_name(name)
        if key not in self._cards:
            return False
        self._cards[key].qty -= 1
        if self._cards[key].qty <= 0:
            del self._cards[key]
        return True

    def set_quantity(self, name: str, qty: int) -> bool:
        key = normalize_name(name)
        if key not in self._cards:
            return False
        if qty <= 0:
            del self._cards[key]
        else:
            self._cards[key].qty = qty
        return True

    def update_card(
        self, name: str, *, mana_cost: Optional[str] = None, card_type: Optional[str] = None
    ) -> bool:
        key = normalize_name(name)
        if key not in self._cards:
            return False
        if mana_cost is not None:
            self._cards[key].mana_cost_raw = mana_cost.strip()
        if card_type is not None:
            self._cards[key].card_type = card_type.strip()
        return True

    def rename_card(self, old_name: str, new_name: str) -> bool:
        old_key = normalize_name(old_name)
        if old_key not in self._cards:
            return False

        entry = self._cards.pop(old_key)
        entry.name = new_name.strip()
        new_key = entry.key

        # If collision, merge qty into existing entry
        if new_key in self._cards:
            self._cards[new_key].qty += entry.qty
        else:
            self._cards[new_key] = entry
        return True

    def get(self, name: str) -> Optional[CardEntry]:
        return self._cards.get(normalize_name(name))

    def all_entries(self) -> list[CardEntry]:
        return list(self._cards.values())

    def deck_size(self) -> int:
        return sum(e.qty for e in self._cards.values())

    # ---------- Stats ----------
    def type_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for e in self._cards.values():
            t = (e.card_type or "Unknown").strip()
            counts[t] = counts.get(t, 0) + e.qty
        return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower())))

    def cost_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for e in self._cards.values():
            if e.has_x:
                bucket = "X"
            else:
                nc = e.numeric_cost
                bucket = str(nc) if nc is not None else "?"
            counts[bucket] = counts.get(bucket, 0) + e.qty
        return dict(sorted(counts.items(), key=lambda kv: (kv[0] != "X", kv[0] == "?", kv[0])))

    # ---------- Search / Filter ----------
    def filter_entries(
        self,
        *,
        name_contains: Optional[str] = None,
        type_contains: Optional[str] = None,
        cost_eq: Optional[int] = None,
        cost_lte: Optional[int] = None,
        cost_gte: Optional[int] = None,
        has_x: Optional[bool] = None,
        sort_by: str = "name",  # name|type|cost
    ) -> list[CardEntry]:
        """
        UX rule:
        - If a card has X in its cost, it DOES NOT match numeric cost filters (eq/lte/gte).
          You find X-cost cards using has_x=True.
        """
        results: list[CardEntry] = []
        nc = normalize_name(name_contains) if name_contains else None
        tc = type_contains.strip().lower() if type_contains else None

        cost_filter_used = (cost_eq is not None) or (cost_lte is not None) or (cost_gte is not None)

        for e in self._cards.values():
            if nc and nc not in normalize_name(e.name):
                continue
            if tc and tc not in (e.card_type or "").lower():
                continue
            if has_x is not None and e.has_x != has_x:
                continue

            # If numeric cost filters are used, ignore X-cost cards entirely
            if cost_filter_used and e.has_x:
                continue

            if cost_eq is not None:
                if e.numeric_cost != cost_eq:
                    continue
            if cost_lte is not None:
                if e.numeric_cost is None or e.numeric_cost > cost_lte:
                    continue
            if cost_gte is not None:
                if e.numeric_cost is None or e.numeric_cost < cost_gte:
                    continue

            results.append(e)

        if sort_by == "type":
            results.sort(key=lambda x: ((x.card_type or "").lower(), normalize_name(x.name)))
        elif sort_by == "cost":

            def cost_key(e: CardEntry):
                if e.has_x:
                    return (2, 0, normalize_name(e.name))
                if e.numeric_cost is None:
                    return (1, 999, normalize_name(e.name))
                return (0, e.numeric_cost, normalize_name(e.name))

            results.sort(key=cost_key)
        else:
            results.sort(key=lambda x: normalize_name(x.name))

        return results

    # ---------- Typo suggestions ----------
    def suggest_names(self, name: str, n: int = 3) -> list[str]:
        keys = list(self._cards.keys())
        target = normalize_name(name)
        matches = difflib.get_close_matches(target, keys, n=n, cutoff=0.6)
        return [self._cards[k].name for k in matches]

    # ---------- Persistence ----------
    def to_dict(self) -> dict:
        return {"cards": [e.to_dict() for e in self._cards.values()]}

    def save(self, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @staticmethod
    def load(filepath: str) -> "Deck":
        """
        Supports BOTH persistence formats:
        - New: {"cards": [ ... ]}
        - Old: [ ... ]
        """
        deck = Deck()
        if not os.path.exists(filepath):
            return deck

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # NEW format
            if isinstance(data, dict):
                cards = data.get("cards", [])
            # OLD format
            elif isinstance(data, list):
                cards = data
            else:
                return Deck()

            if not isinstance(cards, list):
                return Deck()

            for item in cards:
                if isinstance(item, dict):
                    entry = CardEntry.from_dict(item)
                    deck._cards[entry.key] = entry

        except (json.JSONDecodeError, OSError, ValueError, TypeError):
            return Deck()

        return deck

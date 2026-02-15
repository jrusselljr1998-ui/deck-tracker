from dataclasses import dataclass
from typing import Optional


def normalize_name(name: str) -> str:
    # Lowercase + collapse whitespace for consistent lookups
    return " ".join(name.strip().lower().split())


def parse_mana_cost(raw: str) -> tuple[Optional[int], bool, str]:
    """
    Returns (numeric_cost, has_x, display_cost)

    - numeric_cost is an int for numeric input (e.g. "3" -> 3)
    - numeric_cost is int part for X+number forms (e.g. "X3" -> 3, has_x=True)
    - numeric_cost is None for pure X or non-numeric
    - has_x True if 'X' present (case-insensitive)
    - display_cost preserves a cleaned-up representation
    """
    s = raw.strip()
    if not s:
        return None, False, ""

    upper = s.upper()
    has_x = "X" in upper

    # Common simple cases:
    # "X" -> (None, True)
    if upper == "X":
        return None, True, "X"

    # If user enters a pure number
    if s.isdigit():
        return int(s), False, s

    # If user enters something like "X3" or "3X" or "X 3"
    digits = "".join(ch for ch in s if ch.isdigit())
    numeric_cost = int(digits) if digits else None

    # Keep a reasonable display form
    display = upper.replace(" ", "")
    return numeric_cost, has_x, display


@dataclass
class CardEntry:
    name: str  # display name
    mana_cost_raw: str  # what user typed (cleaned)
    card_type: str
    qty: int = 1

    @property
    def key(self) -> str:
        return normalize_name(self.name)

    @property
    def has_x(self) -> bool:
        _, has_x, _ = parse_mana_cost(self.mana_cost_raw)
        return has_x

    @property
    def numeric_cost(self) -> Optional[int]:
        numeric, _, _ = parse_mana_cost(self.mana_cost_raw)
        return numeric

    def pretty(self) -> str:
        qty_part = f"{self.qty}x " if self.qty > 1 else ""
        cost_part = self.mana_cost_raw if self.mana_cost_raw else "?"
        type_part = self.card_type if self.card_type else "?"
        return f"{qty_part}{self.name} ({type_part}) - Cost: {cost_part}"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "mana_cost": self.mana_cost_raw,
            "card_type": self.card_type,
            "qty": self.qty,
        }

    @staticmethod
    def from_dict(d: dict) -> "CardEntry":
        name = str(d.get("name", "")).strip()
        mana_cost = str(d.get("mana_cost", "")).strip()
        card_type = str(d.get("card_type", "")).strip()
        qty = int(d.get("qty", 1))
        if qty < 1:
            qty = 1
        return CardEntry(name=name, mana_cost_raw=mana_cost, card_type=card_type, qty=qty)

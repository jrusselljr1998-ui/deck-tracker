from __future__ import annotations

import re
from collections.abc import Iterable

from deck import Deck

_QTY_LINE = re.compile(r"^\s*(\d+)\s*x?\s+(.+?)\s*$", re.IGNORECASE)


def parse_decklist_lines(lines: Iterable[str]) -> list[tuple[int, str]]:
    """
    Parses common decklist formats:
      - "2 Sol Ring"
      - "2x Sol Ring"
      - "Sol Ring"
    Ignores:
      - blank lines
      - comments starting with # or //
    Returns list of (qty, name).
    """
    results: list[tuple[int, str]] = []

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#") or line.startswith("//"):
            continue

        m = _QTY_LINE.match(line)
        if m:
            qty = int(m.group(1))
            name = m.group(2).strip()
            if qty > 0 and name:
                results.append((qty, name))
        else:
            # No qty provided => qty=1
            results.append((1, line))

    return results


def import_decklist_text(deck: Deck, text: str) -> dict:
    """
    Adds parsed cards to deck (name + qty). Costs/types are unknown from text,
    so we add with mana_cost="", card_type="Unknown".
    Returns summary dict.
    """
    lines = text.splitlines()
    parsed = parse_decklist_lines(lines)

    added_lines = 0
    added_cards_total = 0
    for qty, name in parsed:
        deck.add_card(name=name, mana_cost="", card_type="Unknown", qty=qty)
        added_lines += 1
        added_cards_total += qty

    return {
        "lines_processed": len(lines),
        "entries_added": added_lines,
        "cards_added_total": added_cards_total,
    }


def export_decklist_text(deck: Deck, include_ones: bool = False) -> str:
    """
    Exports as:
      - "2 Sol Ring"
      - "Command Tower" (if qty==1 and include_ones=False)
    """
    entries = deck.filter_entries(sort_by="name")
    out_lines: list[str] = []
    for e in entries:
        if e.qty == 1 and not include_ones:
            out_lines.append(f"{e.name}")
        else:
            out_lines.append(f"{e.qty} {e.name}")
    return "\n".join(out_lines) + ("\n" if out_lines else "")

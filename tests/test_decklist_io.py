from deck import Deck
from decklist_io import parse_decklist_lines, import_decklist_text, export_decklist_text


def test_parse_decklist_lines_supports_qty_x_and_singletons_and_ignores_comments():
    lines = [
        "2 Sol Ring",
        "3x Lightning Bolt",
        "Command Tower",
        "# this is a comment",
        "// another comment",
        "",
        "   4    Arcane Signet   ",
    ]

    parsed = parse_decklist_lines(lines)
    assert parsed == [
        (2, "Sol Ring"),
        (3, "Lightning Bolt"),
        (1, "Command Tower"),
        (4, "Arcane Signet"),
    ]


def test_import_decklist_text_accumulates_duplicates():
    d = Deck()
    text = "\n".join([
        "2 Sol Ring",
        "Sol Ring",
        "3x Sol Ring",
        "Command Tower",
    ])

    summary = import_decklist_text(d, text)
    assert summary["entries_added"] == 4
    assert summary["cards_added_total"] == 2 + 1 + 3 + 1

    e = d.get("Sol Ring")
    assert e is not None
    assert e.qty == 6

    ct = d.get("Command Tower")
    assert ct is not None
    assert ct.qty == 1
    assert ct.card_type == "Unknown"


def test_export_decklist_text_formats_singletons_and_multiples():
    d = Deck()
    d.add_card("Sol Ring", "1", "Artifact", qty=2)
    d.add_card("Command Tower", "", "Land", qty=1)

    out = export_decklist_text(d, include_ones=False).strip().splitlines()
    # Sorted by name in export
    assert out == ["Command Tower", "2 Sol Ring"]

    out2 = export_decklist_text(d, include_ones=True).strip().splitlines()
    assert out2 == ["1 Command Tower", "2 Sol Ring"]

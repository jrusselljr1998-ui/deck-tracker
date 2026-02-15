from deck import Deck


def test_add_increments_quantity_for_same_name_case_insensitive():
    d = Deck()
    d.add_card("Sol Ring", "1", "Artifact", qty=1)
    d.add_card("sol ring", "1", "Artifact", qty=2)

    entry = d.get("SOL RING")
    assert entry is not None
    assert entry.qty == 3
    assert d.deck_size() == 3
    assert len(d.all_entries()) == 1


def test_remove_one_decrements_and_removes_at_zero():
    d = Deck()
    d.add_card("Command Tower", "", "Land", qty=2)

    assert d.remove_one("command tower") is True
    assert d.get("Command Tower").qty == 1

    assert d.remove_one("Command Tower") is True
    assert d.get("Command Tower") is None
    assert d.deck_size() == 0


def test_set_quantity_updates_or_removes():
    d = Deck()
    d.add_card("Arcane Signet", "2", "Artifact", qty=1)

    assert d.set_quantity("arcane signet", 5) is True
    assert d.get("Arcane Signet").qty == 5

    assert d.set_quantity("Arcane Signet", 0) is True
    assert d.get("Arcane Signet") is None


def test_update_card_cost_and_type():
    d = Deck()
    d.add_card("Lightning Bolt", "1", "Instant", qty=1)

    assert d.update_card("lightning bolt", mana_cost="R") is True
    assert d.update_card("LIGHTNING BOLT", card_type="Instant — Burn") is True

    e = d.get("Lightning Bolt")
    assert e.mana_cost_raw == "R"
    assert e.card_type == "Instant — Burn"


def test_rename_merges_on_collision():
    d = Deck()
    d.add_card("Sol Ring", "1", "Artifact", qty=2)
    d.add_card("Mana Crypt", "0", "Artifact", qty=1)

    # Rename "Mana Crypt" -> "Sol Ring" should merge qty
    assert d.rename_card("Mana Crypt", "Sol Ring") is True
    e = d.get("sol ring")
    assert e is not None
    assert e.qty == 3
    assert len(d.all_entries()) == 1


def test_type_counts_respects_quantities():
    d = Deck()
    d.add_card("A", "1", "Creature", qty=3)
    d.add_card("B", "2", "Creature", qty=2)
    d.add_card("C", "3", "Land", qty=5)

    counts = d.type_counts()
    assert counts["Land"] == 5
    assert counts["Creature"] == 5


def test_cost_counts_buckets_numeric_unknown_and_x():
    d = Deck()
    d.add_card("A", "2", "Creature", qty=2)     # bucket "2"
    d.add_card("B", "", "Instant", qty=1)       # bucket "?"
    d.add_card("C", "X", "Sorcery", qty=3)      # bucket "X"
    d.add_card("D", "X3", "Sorcery", qty=1)     # bucket "X" (has X)

    counts = d.cost_counts()
    assert counts["2"] == 2
    assert counts["?"] == 1
    assert counts["X"] == 4


def test_filter_by_name_type_cost_and_has_x():
    d = Deck()
    d.add_card("Fireball", "X1", "Sorcery", qty=1)
    d.add_card("Lightning Bolt", "1", "Instant", qty=1)
    d.add_card("Shock", "1", "Instant", qty=2)
    d.add_card("Mountain", "", "Land", qty=10)

    # name contains
    res = d.filter_entries(name_contains="bolt")
    assert len(res) == 1
    assert res[0].name == "Lightning Bolt"

    # type contains
    res = d.filter_entries(type_contains="inst")
    names = sorted([x.name for x in res])
    assert names == ["Lightning Bolt", "Shock"]

    # cost_eq applies to numeric_cost only
    res = d.filter_entries(cost_eq=1)
    names = sorted([x.name for x in res])
    assert names == ["Lightning Bolt", "Shock"]

    # has_x filter
    res = d.filter_entries(has_x=True)
    assert len(res) == 1
    assert res[0].name == "Fireball"


def test_suggest_names_returns_close_matches():
    d = Deck()
    d.add_card("Command Tower", "", "Land", qty=1)
    d.add_card("Sol Ring", "1", "Artifact", qty=1)

    sugg = d.suggest_names("comand towr")
    assert "Command Tower" in sugg

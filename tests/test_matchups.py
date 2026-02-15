from matchups import MatchupTracker


def test_add_match_and_overall_record_and_winrate():
    t = MatchupTracker()
    t.add_match("Azorius Control", "W")
    t.add_match("Azorius Control", "L")
    t.add_match("Mono-Red Aggro", "D")

    w, l, d = t.overall_record()
    assert (w, l, d) == (1, 1, 1)

    # winrate counts draw as half-win: (1 + 0.5) / 3 = 0.5 = 50%
    assert abs(t.winrate_overall() - 50.0) < 1e-6


def test_record_by_opponent_groups_case_insensitively():
    t = MatchupTracker()
    t.add_match("Gholdengo", "W")
    t.add_match("gholdengo", "W")
    t.add_match("Gholdengo  ", "L")
    t.add_match("Charizard", "L")

    by = t.record_by_opponent()
    # Should have 2 opponents grouped
    assert len(by) == 2

    # Find the gholdengo row regardless of display casing
    g_row = None
    for opp, rec in by.items():
        if opp.strip().lower() == "gholdengo":
            g_row = rec
            break
    assert g_row is not None
    assert g_row == (2, 1, 0)


def test_recent_filter_by_opponent_contains():
    t = MatchupTracker()
    t.add_match("Azorius Control", "W")
    t.add_match("Mono-Red Aggro", "L")
    t.add_match("Azorius Control", "L")

    recent_az = t.recent(n=10, opponent_filter="azorius")
    assert len(recent_az) == 2
    assert all("azorius" in m.opponent.lower() for m in recent_az)

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


def _now_iso() -> str:
    # Local time, ISO-like string (sortable and readable)
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def normalize_text(s: str) -> str:
    return " ".join(s.strip().lower().split())


@dataclass
class Match:
    opponent: str          # e.g. "Mono-Red Aggro", "Azorius Control", "Gholdengo"
    result: str            # "W", "L", or "D"
    played_at: str         # timestamp string
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "opponent": self.opponent,
            "result": self.result,
            "played_at": self.played_at,
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(d: dict) -> "Match":
        opponent = str(d.get("opponent", "")).strip()
        result = str(d.get("result", "")).strip().upper()
        played_at = str(d.get("played_at", "")).strip()
        notes = str(d.get("notes", "")).strip()

        if result not in ("W", "L", "D"):
            result = "L"
        if not played_at:
            played_at = _now_iso()
        return Match(opponent=opponent, result=result, played_at=played_at, notes=notes)


class MatchupTracker:
    """
    Tracks match-level results vs opponent archetypes.
    Stored as a list (history), newest last.
    """

    def __init__(self) -> None:
        self._matches: list[Match] = []

    def add_match(self, opponent: str, result: str, notes: str = "") -> None:
        opponent = opponent.strip()
        result = result.strip().upper()
        if result not in ("W", "L", "D"):
            raise ValueError("Result must be W, L, or D.")
        if not opponent:
            raise ValueError("Opponent cannot be blank.")
        self._matches.append(Match(opponent=opponent, result=result, played_at=_now_iso(), notes=notes.strip()))

    def all_matches(self) -> list[Match]:
        return list(self._matches)

    def recent(self, n: int = 10, opponent_filter: Optional[str] = None) -> list[Match]:
        items = self._matches
        if opponent_filter:
            key = normalize_text(opponent_filter)
            items = [m for m in items if key in normalize_text(m.opponent)]
        return items[-n:]

    def overall_record(self) -> tuple[int, int, int]:
        w = sum(1 for m in self._matches if m.result == "W")
        l = sum(1 for m in self._matches if m.result == "L")
        d = sum(1 for m in self._matches if m.result == "D")
        return w, l, d

    @staticmethod
    def _winrate(w: int, l: int, d: int) -> float:
        total = w + l + d
        if total == 0:
            return 0.0
        # count draw as half-win (common in stats)
        return (w + 0.5 * d) / total * 100.0

    def winrate_overall(self) -> float:
        w, l, d = self.overall_record()
        return self._winrate(w, l, d)

    def record_by_opponent(self) -> dict[str, tuple[int, int, int]]:
        """
        Returns: {opponent_display_name: (W, L, D)}
        Uses normalized key for grouping, but preserves a representative display name.
        """
        bucket: dict[str, tuple[str, int, int, int]] = {}
        # key -> (display, w, l, d)

        for m in self._matches:
            key = normalize_text(m.opponent)
            if key not in bucket:
                bucket[key] = (m.opponent, 0, 0, 0)
            display, w, l, d = bucket[key]
            if m.result == "W":
                w += 1
            elif m.result == "L":
                l += 1
            else:
                d += 1
            bucket[key] = (display, w, l, d)

        out: dict[str, tuple[int, int, int]] = {}
        for _key, (display, w, l, d) in bucket.items():
            out[display] = (w, l, d)

        # Sort by total games desc, then name
        out_sorted = dict(
            sorted(
                out.items(),
                key=lambda kv: (-(kv[1][0] + kv[1][1] + kv[1][2]), kv[0].lower()),
            )
        )
        return out_sorted

    def winrate_by_opponent(self) -> list[tuple[str, int, int, int, float]]:
        """
        Returns a list of tuples:
        (opponent, W, L, D, winrate_percent)
        """
        rows = []
        for opp, (w, l, d) in self.record_by_opponent().items():
            rows.append((opp, w, l, d, self._winrate(w, l, d)))
        return rows

    # ---------- Persistence ----------
    def to_dict(self) -> dict:
        return {"matches": [m.to_dict() for m in self._matches]}

    def save(self, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @staticmethod
    def load(filepath: str) -> "MatchupTracker":
        t = MatchupTracker()
        if not os.path.exists(filepath):
            return t

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                matches = data.get("matches", [])
            elif isinstance(data, list):
                # old/simple format support if you ever saved as list
                matches = data
            else:
                return MatchupTracker()

            if not isinstance(matches, list):
                return MatchupTracker()

            for item in matches:
                if isinstance(item, dict):
                    t._matches.append(Match.from_dict(item))

        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return MatchupTracker()

        return t

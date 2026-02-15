from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime


def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def normalize_text(s: str) -> str:
    return " ".join(s.strip().lower().split())


@dataclass
class Match:
    opponent: str
    result: str  # "W", "L", "D"
    played_at: str
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "opponent": self.opponent,
            "result": self.result,
            "played_at": self.played_at,
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(d: dict) -> Match:
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
    def __init__(self) -> None:
        self._matches: list[Match] = []

    def add_match(self, opponent: str, result: str, notes: str = "") -> None:
        opponent = opponent.strip()
        result = result.strip().upper()
        if result not in ("W", "L", "D"):
            raise ValueError("Result must be W, L, or D.")
        if not opponent:
            raise ValueError("Opponent cannot be blank.")
        self._matches.append(
            Match(opponent=opponent, result=result, played_at=_now_iso(), notes=notes.strip())
        )

    def all_matches(self) -> list[Match]:
        return list(self._matches)

    def recent(self, n: int = 10, opponent_filter: str | None = None) -> list[Match]:
        items = self._matches
        if opponent_filter:
            key = normalize_text(opponent_filter)
            items = [m for m in items if key in normalize_text(m.opponent)]
        return items[-n:]

    def overall_record(self) -> tuple[int, int, int]:
        wins = sum(1 for m in self._matches if m.result == "W")
        losses = sum(1 for m in self._matches if m.result == "L")
        draws = sum(1 for m in self._matches if m.result == "D")
        return wins, losses, draws

    @staticmethod
    def _winrate(wins: int, losses: int, draws: int) -> float:
        total = wins + losses + draws
        if total == 0:
            return 0.0
        return (wins + 0.5 * draws) / total * 100.0

    def winrate_overall(self) -> float:
        wins, losses, draws = self.overall_record()
        return self._winrate(wins, losses, draws)

    def record_by_opponent(self) -> dict[str, tuple[int, int, int]]:
        bucket: dict[str, tuple[str, int, int, int]] = {}
        for m in self._matches:
            key = normalize_text(m.opponent)
            if key not in bucket:
                bucket[key] = (m.opponent, 0, 0, 0)
            display, wins, losses, draws = bucket[key]
            if m.result == "W":
                wins += 1
            elif m.result == "L":
                losses += 1
            else:
                draws += 1
            bucket[key] = (display, wins, losses, draws)

        out: dict[str, tuple[int, int, int]] = {}
        for _key, (display, wins, losses, draws) in bucket.items():
            out[display] = (wins, losses, draws)

        return dict(
            sorted(
                out.items(),
                key=lambda kv: (-(kv[1][0] + kv[1][1] + kv[1][2]), kv[0].lower()),
            )
        )

    def winrate_by_opponent(self) -> list[tuple[str, int, int, int, float]]:
        rows: list[tuple[str, int, int, int, float]] = []
        for opp, (wins, losses, draws) in self.record_by_opponent().items():
            rows.append((opp, wins, losses, draws, self._winrate(wins, losses, draws)))
        return rows

    def to_dict(self) -> dict:
        return {"matches": [m.to_dict() for m in self._matches]}

    def save(self, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @staticmethod
    def load(filepath: str) -> MatchupTracker:
        t = MatchupTracker()
        if not os.path.exists(filepath):
            return t

        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                matches = data.get("matches", [])
            elif isinstance(data, list):
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

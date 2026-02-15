from deck import Deck
from decklist_io import import_decklist_text, export_decklist_text
from matchups import MatchupTracker


DECK_FILE = "deck.json"
MATCHUPS_FILE = "matchups.json"


def prompt_int(prompt: str, *, allow_blank: bool = False) -> int | None:
    while True:
        s = input(prompt).strip()
        if allow_blank and s == "":
            return None
        if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
            return int(s)
        print("Please enter a valid integer.")


def prompt_yes_no(prompt: str, default_no: bool = True) -> bool:
    s = input(prompt).strip().lower()
    if not s:
        return not default_no
    return s in ("y", "yes")


def print_deck(entries, deck_size: int) -> None:
    print(f"\nDeck size: {deck_size}")
    if not entries:
        print("(empty)")
        return
    for e in entries:
        print(e.pretty())


def print_match_history(matches) -> None:
    if not matches:
        print("(no matches yet)")
        return
    for m in matches:
        notes_part = f" — {m.notes}" if m.notes else ""
        print(f"{m.played_at} | {m.result} | vs {m.opponent}{notes_part}")


def menu() -> None:
    deck = Deck.load(DECK_FILE)
    tracker = MatchupTracker.load(MATCHUPS_FILE)

    while True:
        print("\n1. Add card")
        print("2. View deck")
        print("3. Delete card")
        print("4. Stats")
        print("5. Edit card")
        print("6. Search / filter")
        print("7. Import decklist text")
        print("8. Export decklist text")
        print("9. Record matchup result")
        print("10. Matchup stats (overall + by opponent)")
        print("11. Match history")
        print("12. Save and exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            name = input("Card name: ").strip()
            mana_cost = input("Mana cost (number, X, or X+number like X3): ").strip()
            card_type = input("Card type: ").strip()
            qty = prompt_int("Quantity (default 1): ", allow_blank=True)
            qty = 1 if qty is None else qty
            if qty <= 0:
                print("Quantity must be >= 1.")
                continue
            deck.add_card(name=name, mana_cost=mana_cost, card_type=card_type, qty=qty)
            print("Card added.")

        elif choice == "2":
            entries = deck.filter_entries(sort_by="name")
            print_deck(entries, deck.deck_size())

        elif choice == "3":
            name = input("Enter card name to delete (removes 1): ").strip()
            ok = deck.remove_one(name)
            if ok:
                print("Card removed (qty decremented).")
            else:
                suggestions = deck.suggest_names(name)
                if suggestions:
                    print("Card not found. Did you mean:")
                    for s in suggestions:
                        print(f" - {s}")
                else:
                    print("Card not found.")

        elif choice == "4":
            print("\n--- Stats ---")
            print(f"Total cards (with quantities): {deck.deck_size()}")
            print(f"Unique cards: {len(deck.all_entries())}")

            print("\nType counts:")
            for t, c in deck.type_counts().items():
                print(f"  {t}: {c}")

            print("\nCost buckets:")
            for b, c in deck.cost_counts().items():
                print(f"  {b}: {c}")

        elif choice == "5":
            name = input("Card name to edit: ").strip()
            entry = deck.get(name)
            if not entry:
                suggestions = deck.suggest_names(name)
                if suggestions:
                    print("Card not found. Did you mean:")
                    for s in suggestions:
                        print(f" - {s}")
                else:
                    print("Card not found.")
                continue

            print("\nCurrent:")
            print(entry.pretty())
            print("\nEdit what?")
            print("1) Mana cost")
            print("2) Card type")
            print("3) Quantity (set exact)")
            print("4) Rename card")
            sub = input("Choose: ").strip()

            if sub == "1":
                new_cost = input("New mana cost: ").strip()
                deck.update_card(entry.name, mana_cost=new_cost)
                print("Updated.")
            elif sub == "2":
                new_type = input("New card type: ").strip()
                deck.update_card(entry.name, card_type=new_type)
                print("Updated.")
            elif sub == "3":
                new_qty = prompt_int("New quantity (0 removes): ")
                if new_qty is None:
                    continue
                deck.set_quantity(entry.name, new_qty)
                print("Updated.")
            elif sub == "4":
                new_name = input("New name: ").strip()
                if not new_name:
                    print("Name cannot be blank.")
                    continue
                deck.rename_card(entry.name, new_name)
                print("Renamed.")
            else:
                print("Invalid choice.")

        elif choice == "6":
            print("\n--- Search / Filter ---")
            name_contains = input("Name contains (blank for any): ").strip()
            type_contains = input("Type contains (blank for any): ").strip()

            has_x_raw = input("Has X cost? (y/n/blank for any): ").strip().lower()
            if has_x_raw in ("y", "yes"):
                has_x = True
            elif has_x_raw in ("n", "no"):
                has_x = False
            else:
                has_x = None

            cost_eq = prompt_int("Cost equals (blank for any): ", allow_blank=True)
            cost_lte = prompt_int("Cost <= (blank for any): ", allow_blank=True)
            cost_gte = prompt_int("Cost >= (blank for any): ", allow_blank=True)

            sort_by = input("Sort by (name/type/cost) [name]: ").strip().lower() or "name"
            if sort_by not in ("name", "type", "cost"):
                sort_by = "name"

            results = deck.filter_entries(
                name_contains=name_contains or None,
                type_contains=type_contains or None,
                has_x=has_x,
                cost_eq=cost_eq,
                cost_lte=cost_lte,
                cost_gte=cost_gte,
                sort_by=sort_by,
            )
            print_deck(results, sum(e.qty for e in results))

        elif choice == "7":
            print("\nPaste decklist text. Enter a blank line to finish.")
            lines = []
            while True:
                line = input()
                if line.strip() == "":
                    break
                lines.append(line)

            text = "\n".join(lines)
            summary = import_decklist_text(deck, text)
            print("\nImported.")
            print(f"Lines processed: {summary['lines_processed']}")
            print(f"Entries added: {summary['entries_added']}")
            print(f"Total cards added: {summary['cards_added_total']}")
            print("Note: imported cards use type 'Unknown' and empty cost; edit them later.")

        elif choice == "8":
            include_ones = prompt_yes_no(
                "Include '1 ' prefix on singletons? (y/n) [n]: ", default_no=True
            )
            out = export_decklist_text(deck, include_ones=include_ones)
            print("\n--- Exported Decklist ---")
            print(out if out.strip() else "(empty)")
            print("------------------------")

        elif choice == "9":
            print("\n--- Record Matchup ---")
            opponent = input("Opponent archetype/deck (e.g. 'Azorius Control'): ").strip()
            result = input("Result (W/L/D): ").strip().upper()
            notes = input("Notes (optional): ").strip()

            try:
                tracker.add_match(opponent=opponent, result=result, notes=notes)
                print("Match recorded.")
            except ValueError as e:
                print(f"Error: {e}")

        elif choice == "10":
            print("\n--- Matchup Stats ---")
            w, l, d = tracker.overall_record()
            total = w + l + d
            print(f"Overall: {w}-{l}-{d} (Total: {total})")
            print(f"Winrate (D = half-win): {tracker.winrate_overall():.1f}%")

            rows = tracker.winrate_by_opponent()
            if not rows:
                print("\nBy opponent: (no matches yet)")
            else:
                print("\nBy opponent:")
                for opp, ow, ol, od, wr in rows:
                    t = ow + ol + od
                    print(f"  {opp}: {ow}-{ol}-{od} | {wr:.1f}% | {t} matches")

        elif choice == "11":
            print("\n--- Match History ---")
            filt = input("Filter by opponent contains (blank for all): ").strip()
            n = prompt_int("How many recent matches? (default 10): ", allow_blank=True)
            n = 10 if n is None else n
            if n <= 0:
                n = 10

            matches = tracker.recent(n=n, opponent_filter=filt or None)
            print_match_history(matches)

        elif choice == "12":
            deck.save(DECK_FILE)
            tracker.save(MATCHUPS_FILE)
            print("Saved deck + matchups. Goodbye!")
            break

        else:
            print("Invalid option. Try again.")


def main() -> None:
    # Entry point used by `deck-tracker` console script
    menu()


if __name__ == "__main__":
    main()

# scripts/manage_wants.py
# interactive wants manager

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzers.wants_manager import WantsManager

def print_menu():
    """print main menu"""
    print("\n--- wants manager ---")
    print("1. list wants")
    print("2. add want")
    print("3. cancel want")
    print("4. purchase want")
    print("5. perform check-ins")
    print("6. show report")
    print("7. exit")
    print()

def list_wants(manager: WantsManager):
    """list all wants by status"""
    pending = manager.get_pending_wants()
    ready = manager.get_ready_wants()
    completed = manager.get_completed_wants()
    cancelled = manager.get_cancelled_wants()

    print("\n--- ready to purchase ---")
    if ready:
        for i, want in enumerate(ready, 1):
            print(f"{i}. {want.name:.<30} ${want.price:>8,.2f}")
    else:
        print("(none)")

    print("\n--- pending wants ---")
    if pending:
        for i, want in enumerate(pending, 1):
            check_status = f"({want.check_ins_completed}/3)"
            days_left = want.days_until_next_check_in
            print(
                f"{i}. {want.name:.<30} "
                f"${want.price:>8,.2f} "
                f"{check_status} next in {days_left} days"
            )
    else:
        print("(none)")

    print("\n--- purchased wants ---")
    if completed:
        for i, want in enumerate(completed, 1):
            print(f"{i}. {want.name:.<30} ${want.price:>8,.2f}")
    else:
        print("(none)")

    print("\n--- cancelled wants ---")
    if cancelled:
        for i, want in enumerate(cancelled, 1):
            print(f"{i}. {want.name:.<30} ${want.price:>8,.2f}")
    else:
        print("(none)")

def add_want(manager: WantsManager):
    """add new want"""
    print("\n--- add want ---")
    name = input("item name: ").strip()
    price = float(input("price: $"))
    category = input("category (e.g., 'Electronics'): ").strip()
    reason = input("why do you want this? ").strip()
    notes = input("notes (optional): ").strip()

    manager.add_want(
        name=name,
        price=price,
        category=category,
        reason=reason,
        notes=notes,
    )

def cancel_want(manager: WantsManager):
    """cancel a want"""
    pending = manager.get_pending_wants()
    if not pending:
        print("no pending wants")
        return

    print("\n--- cancel want ---")
    for i, want in enumerate(pending, 1):
        print(f"{i}. {want.name}")

    choice = input("select want to cancel (number): ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(pending):
            manager.cancel_want(pending[idx].name)
        else:
            print("invalid selection")
    except ValueError:
        print("invalid input")

def purchase_want(manager: WantsManager):
    """mark a want as purchased"""
    ready = manager.get_ready_wants()
    if not ready:
        print("no wants ready for purchase")
        return

    print("\n--- purchase want ---")
    for i, want in enumerate(ready, 1):
        print(f"{i}. {want.name} - ${want.price:.2f}")

    choice = input("select want to purchase (number): ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(ready):
            manager.purchase_want(ready[idx].name)
        else:
            print("invalid selection")
    except ValueError:
        print("invalid input")

def perform_check_ins(manager: WantsManager):
    """perform check-ins for due wants"""
    print("\n--- performing check-ins ---")
    updated = manager.perform_check_ins()
    if not updated:
        print("no check-ins due today")

def show_report(manager: WantsManager):
    """show detailed report"""
    print(manager.want_report())

def main():
    """main loop"""
    manager = WantsManager("data/wants.json")

    while True:
        print_menu()
        choice = input("select option: ").strip()

        if choice == "1":
            list_wants(manager)
        elif choice == "2":
            add_want(manager)
        elif choice == "3":
            cancel_want(manager)
        elif choice == "4":
            purchase_want(manager)
        elif choice == "5":
            perform_check_ins(manager)
        elif choice == "6":
            show_report(manager)
        elif choice == "7":
            print("👋 bye!")
            break
        else:
            print("invalid option")

if __name__ == "__main__":
    main()
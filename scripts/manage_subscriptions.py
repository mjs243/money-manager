# scripts/manage_subscriptions.py
# interactive subscription manager

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzers.subscription_manager import SubscriptionManager

def print_menu():
    """print main menu"""
    print("\n--- subscription manager ---")
    print("1. list subscriptions")
    print("2. add subscription")
    print("3. cancel subscription")
    print("4. reactivate subscription")
    print("5. update subscription")
    print("6. show report")
    print("7. exit")
    print()

def list_subscriptions(manager: SubscriptionManager):
    """list all subscriptions"""
    active = manager.get_active_manual()
    inactive = [s for s in manager.get_all_manual() if not s.is_active]

    print("\n--- active subscriptions ---")
    if active:
        for i, sub in enumerate(active, 1):
            print(
                f"{i}. {sub.name:.<30} "
                f"${sub.amount:>8,.2f} ({sub.interval_type}) "
                f"→ ${sub.monthly_cost():>8,.2f}/mo"
            )
    else:
        print("(none)")

    if inactive:
        print("\n--- cancelled subscriptions ---")
        for i, sub in enumerate(inactive, 1):
            print(f"{i}. {sub.name} (cancelled)")

def add_subscription(manager: SubscriptionManager):
    """add new subscription"""
    print("\n--- add subscription ---")
    name = input("subscription name: ").strip()
    merchant = input("merchant: ").strip()
    amount = float(input("amount: $"))
    category = input("category (e.g., 'Software & Tech'): ").strip()

    print("\ninterval options:")
    print("  7: weekly")
    print("  14: bi-weekly")
    print("  30: monthly")
    print("  365: annual")
    interval_input = input("interval days (or custom): ").strip()
    interval_days = int(interval_input) if interval_input else 30

    notes = input("notes (optional): ").strip()

    manager.add_subscription(
        name=name,
        merchant=merchant,
        amount=amount,
        category=category,
        interval_days=interval_days,
        start_date=datetime.now(),
        notes=notes,
    )

def cancel_subscription(manager: SubscriptionManager):
    """cancel a subscription"""
    active = manager.get_active_manual()
    if not active:
        print("no active subscriptions")
        return

    print("\n--- cancel subscription ---")
    for i, sub in enumerate(active, 1):
        print(f"{i}. {sub.name}")

    choice = input("select subscription to cancel (number): ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(active):
            manager.cancel_subscription(active[idx].name)
        else:
            print("invalid selection")
    except ValueError:
        print("invalid input")

def reactivate_subscription(manager: SubscriptionManager):
    """reactivate a cancelled subscription"""
    inactive = [s for s in manager.get_all_manual() if not s.is_active]
    if not inactive:
        print("no cancelled subscriptions")
        return

    print("\n--- reactivate subscription ---")
    for i, sub in enumerate(inactive, 1):
        print(f"{i}. {sub.name}")

    choice = input("select subscription to reactivate (number): ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(inactive):
            manager.reactivate_subscription(inactive[idx].name)
        else:
            print("invalid selection")
    except ValueError:
        print("invalid input")

def update_subscription(manager: SubscriptionManager):
    """update subscription details"""
    active = manager.get_active_manual()
    if not active:
        print("no active subscriptions")
        return

    print("\n--- update subscription ---")
    for i, sub in enumerate(active, 1):
        print(f"{i}. {sub.name}")

    choice = input("select subscription to update (number): ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(active):
            sub = active[idx]
            print(f"\nupdating: {sub.name}")
            print("(leave blank to skip)")

            amount_input = input(f"amount (${sub.amount:.2f}): ").strip()
            interval_input = input(f"interval days ({sub.interval_days}): ").strip()
            notes_input = input(f"notes ({sub.notes}): ").strip()

            manager.update_subscription(
                sub.name,
                amount=float(amount_input) if amount_input else None,
                interval_days=int(interval_input) if interval_input else None,
                notes=notes_input if notes_input else None,
            )
        else:
            print("invalid selection")
    except ValueError:
        print("invalid input")

def show_report(manager: SubscriptionManager):
    """show detailed report"""
    print(manager.subscription_report())

def main():
    """main loop"""
    manager = SubscriptionManager("data/subscriptions.json")

    while True:
        print_menu()
        choice = input("select option: ").strip()

        if choice == "1":
            list_subscriptions(manager)
        elif choice == "2":
            add_subscription(manager)
        elif choice == "3":
            cancel_subscription(manager)
        elif choice == "4":
            reactivate_subscription(manager)
        elif choice == "5":
            update_subscription(manager)
        elif choice == "6":
            show_report(manager)
        elif choice == "7":
            print("👋 bye!")
            break
        else:
            print("invalid option")

if __name__ == "__main__":
    main()
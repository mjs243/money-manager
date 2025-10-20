# scripts/manage_recurring_purchases.py
# interactive recurring purchases manager

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzers.recurring_purchases_manager import RecurringPurchasesManager
from models.recurring_purchase import PurchaseFrequency

def print_menu():
    """print main menu"""
    print("\n--- recurring purchases manager ---")
    print("1. list purchases")
    print("2. add purchase")
    print("3. record purchase")
    print("4. snooze purchase")
    print("5. deactivate/reactivate purchase")
    print("6. show report")
    print("7. exit")
    print()

def list_purchases(manager: RecurringPurchasesManager):
    """list all purchases"""
    active = manager.get_active_purchases()
    due_soon = manager.get_due_soon()
    overdue = manager.get_overdue()

    print("\n--- overdue purchases ---")
    if overdue:
        for i, purchase in enumerate(overdue, 1):
            print(f"{i}. {purchase.name:.<30} ${purchase.amount:>8,.2f}")
    else:
        print("(none)")

    print("\n--- due soon ---")
    if due_soon:
        for i, purchase in enumerate(due_soon, 1):
            print(f"{i}. {purchase.name:.<30} ${purchase.amount:>8,.2f} (in {purchase.days_until_next} days)")
    else:
        print("(none)")

    print("\n--- all active purchases ---")
    if active:
        for i, purchase in enumerate(active, 1):
            status = "⏰" if purchase.is_due_soon else "⏳"
            print(f"{i}. {status} {purchase.name:.<30} ${purchase.amount:>8,.2f} ({purchase.frequency.value})")
    else:
        print("(none)")

def add_purchase(manager: RecurringPurchasesManager):
    """add new recurring purchase"""
    print("\n--- add recurring purchase ---")
    name = input("item name: ").strip()
    merchant = input("merchant: ").strip()
    amount = float(input("amount: $"))
    category = input("category: ").strip()

    print("\nfrequency options:")
    print("  1: weekly")
    print("  2: bi-weekly")
    print("  3: monthly")
    print("  4: quarterly")
    print("  5: semi-annual")
    print("  6: annual")
    print("  7: custom")

    freq_choice = input("select frequency (1-7): ").strip()
    freq_map = {
        "1": PurchaseFrequency.WEEKLY,
        "2": PurchaseFrequency.BI_WEEKLY,
        "3": PurchaseFrequency.MONTHLY,
        "4": PurchaseFrequency.QUARTERLY,
        "5": PurchaseFrequency.SEMI_ANNUAL,
        "6": PurchaseFrequency.ANNUAL,
        "7": PurchaseFrequency.CUSTOM,
    }

    if freq_choice in freq_map:
        frequency = freq_map[freq_choice]

        if freq_choice == "7":
            interval_days = int(input("custom interval in days: "))
        else:
            interval_days_map = {
                PurchaseFrequency.WEEKLY: 7,
                PurchaseFrequency.BI_WEEKLY: 14,
                PurchaseFrequency.MONTHLY: 30,
                PurchaseFrequency.QUARTERLY: 90,
                PurchaseFrequency.SEMI_ANNUAL: 180,
                PurchaseFrequency.ANNUAL: 365,
            }
            interval_days = interval_days_map[frequency]
    else:
        print("invalid selection, defaulting to monthly")
        frequency = PurchaseFrequency.MONTHLY
        interval_days = 30

    last_purchase_str = input("last purchase date (YYYY-MM-DD) or leave blank for today: ").strip()
    if last_purchase_str:
        last_purchase = datetime.strptime(last_purchase_str, "%Y-%m-%d")
    else:
        last_purchase = datetime.now()

    notes = input("notes (optional): ").strip()

    manager.add_purchase(
        name=name,
        merchant=merchant,
        amount=amount,
        category=category,
        frequency=frequency,
        interval_days=interval_days,
        last_purchase=last_purchase,
        notes=notes,
    )

def record_purchase(manager: RecurringPurchasesManager):
    """record a new purchase"""
    active = manager.get_active_purchases()
    if not active:
        print("no active purchases")
        return

    print("\n--- record purchase ---")
    for i, purchase in enumerate(active, 1):
        print(f"{i}. {purchase.name}")

    choice = input("select purchase to record (number): ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(active):
            purchase = active[idx]
            amount_input = input(f"amount (${purchase.amount:.2f}, press enter to use default): ").strip()
            amount = float(amount_input) if amount_input else None

            manager.record_purchase(purchase.name, amount)
        else:
            print("invalid selection")
    except ValueError:
        print("invalid input")

def snooze_purchase(manager: RecurringPurchasesManager):
    """snooze a purchase"""
    active = manager.get_active_purchases()
    if not active:
        print("no active purchases")
        return

    print("\n--- snooze purchase ---")
    for i, purchase in enumerate(active, 1):
        print(f"{i}. {purchase.name} (next in {purchase.days_until_next} days)")

    choice = input("select purchase to snooze (number): ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(active):
            days = int(input("snooze for how many days? "))
            manager.snooze_purchase(active[idx].name, days)
        else:
            print("invalid selection")
    except ValueError:
        print("invalid input")

def toggle_purchase(manager: RecurringPurchasesManager):
    """activate/deactivate a purchase"""
    all_purchases = manager.purchases
    if not all_purchases:
        print("no purchases")
        return

    print("\n--- toggle purchase status ---")
    for i, purchase in enumerate(all_purchases, 1):
        status = "active" if purchase.is_active else "inactive"
        print(f"{i}. {purchase.name} ({status})")

    choice = input("select purchase to toggle (number): ").strip()
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(all_purchases):
            purchase = all_purchases[idx]
            if purchase.is_active:
                manager.deactivate_purchase(purchase.name)
            else:
                manager.reactivate_purchase(purchase.name)
        else:
            print("invalid selection")
    except ValueError:
        print("invalid input")

def show_report(manager: RecurringPurchasesManager):
    """show detailed report"""
    print(manager.purchases_report())

def main():
    """main loop"""
    manager = RecurringPurchasesManager("data/recurring_purchases.json")

    while True:
        print_menu()
        choice = input("select option: ").strip()

        if choice == "1":
            list_purchases(manager)
        elif choice == "2":
            add_purchase(manager)
        elif choice == "3":
            record_purchase(manager)
        elif choice == "4":
            snooze_purchase(manager)
        elif choice == "5":
            toggle_purchase(manager)
        elif choice == "6":
            show_report(manager)
        elif choice == "7":
            print("👋 bye!")
            break
        else:
            print("invalid option")

if __name__ == "__main__":
    main()
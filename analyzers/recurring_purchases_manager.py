# analyzers/recurring_purchases_manager.py
# manage recurring purchases (not subscriptions)

import json
from pathlib import Path
from datetime import datetime, timedelta
from models.recurring_purchase import RecurringPurchase, PurchaseFrequency

class RecurringPurchasesManager:
    """manage recurring purchases (not subscriptions)"""

    def __init__(self, config_path: str = "data/recurring_purchases.json"):
        self.config_path = Path(config_path)
        self.purchases = []
        self._load_purchases()

    def _load_purchases(self):
        """load purchases from file"""
        if not self.config_path.exists():
            self.purchases = []
            return

        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)

            self.purchases = [
                RecurringPurchase(
                    name=purchase['name'],
                    merchant=purchase['merchant'],
                    amount=purchase['amount'],
                    category=purchase['category'],
                    frequency=PurchaseFrequency(purchase['frequency']),
                    interval_days=purchase['interval_days'],
                    last_purchase=datetime.fromisoformat(purchase['last_purchase']),
                    next_expected=datetime.fromisoformat(purchase['next_expected']),
                    notes=purchase.get('notes', ''),
                    is_active=purchase.get('is_active', True),
                    purchase_history=[
                        datetime.fromisoformat(d)
                        for d in purchase.get('purchase_history', [])
                    ],
                )
                for purchase in data
            ]
            print(f"✅ loaded {len(self.purchases)} recurring purchases")
        except Exception as e:
            print(f"⚠️  error loading purchases: {e}")
            self.purchases = []

    def _save_purchases(self):
        """save purchases to file"""
        data = [
            {
                "name": purchase.name,
                "merchant": purchase.merchant,
                "amount": purchase.amount,
                "category": purchase.category,
                "frequency": purchase.frequency.value,
                "interval_days": purchase.interval_days,
                "last_purchase": purchase.last_purchase.isoformat(),
                "next_expected": purchase.next_expected.isoformat(),
                "notes": purchase.notes,
                "is_active": purchase.is_active,
                "purchase_history": [
                    d.isoformat() for d in purchase.purchase_history
                ],
            }
            for purchase in self.purchases
        ]

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✅ saved {len(self.purchases)} recurring purchases")

    def add_purchase(
        self,
        name: str,
        merchant: str,
        amount: float,
        category: str,
        frequency: PurchaseFrequency,
        interval_days: int,
        last_purchase: datetime,
        notes: str = ""
    ) -> RecurringPurchase:
        """add a new recurring purchase"""
        next_expected = last_purchase + timedelta(days=interval_days)

        purchase = RecurringPurchase(
            name=name,
            merchant=merchant,
            amount=amount,
            category=category,
            frequency=frequency,
            interval_days=interval_days,
            last_purchase=last_purchase,
            next_expected=next_expected,
            notes=notes,
        )

        self.purchases.append(purchase)
        self._save_purchases()
        print(f"✅ added recurring purchase: {name}")
        return purchase

    def record_purchase(self, name: str, amount: float = None):
        """record a new purchase for a recurring item"""
        for purchase in self.purchases:
            if purchase.name.lower() == name.lower():
                purchase.record_purchase(amount)
                self._save_purchases()
                print(f"✅ recorded purchase: {name}")
                return

        print(f"❌ recurring purchase not found: {name}")

    def snooze_purchase(self, name: str, days: int):
        """delay next expected purchase"""
        for purchase in self.purchases:
            if purchase.name.lower() == name.lower():
                purchase.snooze(days)
                self._save_purchases()
                print(f"✅ snoozed {name} for {days} days")
                return

        print(f"❌ recurring purchase not found: {name}")

    def deactivate_purchase(self, name: str):
        """deactivate a recurring purchase"""
        for purchase in self.purchases:
            if purchase.name.lower() == name.lower():
                purchase.is_active = False
                self._save_purchases()
                print(f"✅ deactivated: {name}")
                return

        print(f"❌ recurring purchase not found: {name}")

    def reactivate_purchase(self, name: str):
        """reactivate a deactivated recurring purchase"""
        for purchase in self.purchases:
            if purchase.name.lower() == name.lower():
                purchase.is_active = True
                self._save_purchases()
                print(f"✅ reactivated: {name}")
                return

        print(f"❌ recurring purchase not found: {name}")

    def get_active_purchases(self) -> list[RecurringPurchase]:
        """get all active recurring purchases"""
        return [p for p in self.purchases if p.is_active]

    def get_due_soon(self, days: int = 7) -> list[RecurringPurchase]:
        """get purchases due soon"""
        return [
            p for p in self.get_active_purchases()
            if p.is_due_soon
        ]

    def get_overdue(self) -> list[RecurringPurchase]:
        """get overdue purchases"""
        return [
            p for p in self.get_active_purchases()
            if p.is_overdue
        ]

    def get_by_category(self) -> dict[str, list[RecurringPurchase]]:
        """organize purchases by category"""
        result = {}
        for purchase in self.get_active_purchases():
            if purchase.category not in result:
                result[purchase.category] = []
            result[purchase.category].append(purchase)
        return result

    def total_monthly_cost(self) -> float:
        """total monthly cost of all active purchases"""
        return sum(p.monthly_cost for p in self.get_active_purchases())

    def total_annual_cost(self) -> float:
        """total annual cost of all active purchases"""
        return sum(p.annual_cost for p in self.get_active_purchases())

    def purchases_report(self) -> str:
        """generate detailed recurring purchases report"""
        active = self.get_active_purchases()
        due_soon = self.get_due_soon()
        overdue = self.get_overdue()
        by_category = self.get_by_category()

        output = []
        output.append("=" * 70)
        output.append("RECURRING PURCHASES REPORT")
        output.append("=" * 70)

        # stats
        output.append(f"\n--- overview ---")
        output.append(f"active recurring purchases: {len(active)}")
        output.append(f"monthly cost: ${self.total_monthly_cost():,.2f}")
        output.append(f"annual cost: ${self.total_annual_cost():,.2f}")

        # overdue
        if overdue:
            output.append(f"\n--- ⚠️  overdue purchases ({len(overdue)}) ---")
            for purchase in overdue:
                output.append(
                    f"  {purchase.name:.<35} "
                    f"${purchase.amount:>8,.2f} "
                    f"({purchase.frequency.value})"
                )
                output.append(f"    last: {purchase.last_purchase.date()}")

        # due soon
        if due_soon:
            output.append(f"\n--- 📅 due soon ({len(due_soon)}) ---")
            for purchase in due_soon:
                output.append(
                    f"  {purchase.name:.<35} "
                    f"${purchase.amount:>8,.2f} "
                    f"in {purchase.days_until_next} days"
                )
                output.append(f"    expected: {purchase.next_expected.date()}")

        # by category
        if by_category:
            output.append(f"\n--- by category ---")
            for category, purchases in sorted(by_category.items()):
                category_monthly = sum(p.monthly_cost for p in purchases)
                output.append(
                    f"  {category}: {len(purchases)} items, "
                    f"${category_monthly:,.2f}/mo"
                )

        # all active purchases
        if active:
            output.append(f"\n--- all active purchases ---")
            for purchase in sorted(active, key=lambda x: x.days_until_next):
                status = "⏰" if purchase.is_due_soon else "⏳"
                output.append(
                    f"  {status} {purchase.name:.<35} "
                    f"${purchase.amount:>8,.2f} "
                    f"({purchase.frequency.value}) "
                    f"next in {purchase.days_until_next} days"
                )
                if purchase.notes:
                    output.append(f"    note: {purchase.notes}")

        output.append("\n" + "=" * 70)
        return "\n".join(output)
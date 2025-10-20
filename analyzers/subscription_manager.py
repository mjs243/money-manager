# analyzers/subscription_manager.py
# manage both auto-detected + manual subscriptions

import json
from pathlib import Path
from datetime import datetime
from models.subscription import ManualSubscription
from analyzers.subscriptions import SubscriptionDetector

class SubscriptionManager:
    """manage manual + detected subscriptions"""

    def __init__(self, config_path: str = "data/subscriptions.json"):
        self.config_path = Path(config_path)
        self.manual_subscriptions = []
        self._load_manual()

    def _load_manual(self):
        """load manual subscriptions from file"""
        if not self.config_path.exists():
            self.manual_subscriptions = []
            return

        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)

            self.manual_subscriptions = [
                ManualSubscription(
                    name=sub['name'],
                    merchant=sub['merchant'],
                    amount=sub['amount'],
                    category=sub['category'],
                    interval_days=sub['interval_days'],
                    start_date=datetime.fromisoformat(sub['start_date']),
                    end_date=(
                        datetime.fromisoformat(sub['end_date'])
                        if sub.get('end_date')
                        else None
                    ),
                    notes=sub.get('notes', ''),
                    is_active=sub.get('is_active', True),
                )
                for sub in data
            ]
            print(f"✅ loaded {len(self.manual_subscriptions)} manual subscriptions")
        except Exception as e:
            print(f"⚠️  error loading subscriptions: {e}")
            self.manual_subscriptions = []

    def _save_manual(self):
        """save manual subscriptions to file"""
        data = [
            {
                "name": sub.name,
                "merchant": sub.merchant,
                "amount": sub.amount,
                "category": sub.category,
                "interval_days": sub.interval_days,
                "start_date": sub.start_date.isoformat(),
                "end_date": sub.end_date.isoformat() if sub.end_date else None,
                "notes": sub.notes,
                "is_active": sub.is_active,
            }
            for sub in self.manual_subscriptions
        ]

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✅ saved {len(self.manual_subscriptions)} subscriptions")

    def add_subscription(
        self,
        name: str,
        merchant: str,
        amount: float,
        category: str,
        interval_days: int,
        start_date: datetime,
        notes: str = ""
    ) -> ManualSubscription:
        """add a manual subscription"""
        sub = ManualSubscription(
            name=name,
            merchant=merchant,
            amount=amount,
            category=category,
            interval_days=interval_days,
            start_date=start_date,
            notes=notes,
            is_active=True,
        )

        self.manual_subscriptions.append(sub)
        self._save_manual()
        print(f"✅ added subscription: {name}")
        return sub

    def cancel_subscription(self, name: str):
        """cancel a subscription (mark as inactive)"""
        for sub in self.manual_subscriptions:
            if sub.name.lower() == name.lower():
                sub.is_active = False
                sub.end_date = datetime.now()
                self._save_manual()
                print(f"✅ cancelled: {name}")
                return

        print(f"❌ subscription not found: {name}")

    def reactivate_subscription(self, name: str):
        """reactivate a cancelled subscription"""
        for sub in self.manual_subscriptions:
            if sub.name.lower() == name.lower():
                sub.is_active = True
                sub.end_date = None
                self._save_manual()
                print(f"✅ reactivated: {name}")
                return

        print(f"❌ subscription not found: {name}")

    def update_subscription(
        self,
        name: str,
        amount: float = None,
        interval_days: int = None,
        notes: str = None
    ):
        """update subscription details"""
        for sub in self.manual_subscriptions:
            if sub.name.lower() == name.lower():
                if amount is not None:
                    sub.amount = amount
                if interval_days is not None:
                    sub.interval_days = interval_days
                if notes is not None:
                    sub.notes = notes

                self._save_manual()
                print(f"✅ updated: {name}")
                return

        print(f"❌ subscription not found: {name}")

    def get_active_manual(self) -> list[ManualSubscription]:
        """get all active manual subscriptions"""
        return [sub for sub in self.manual_subscriptions if sub.is_active]

    def get_all_manual(self) -> list[ManualSubscription]:
        """get all manual subscriptions (including inactive)"""
        return self.manual_subscriptions

    def combined_recurring(
        self,
        detected_subscriptions: dict
    ) -> dict:
        """
        combine detected + manual subscriptions.
        manual takes precedence (overwrites detections).
        """
        # start with detected
        combined = {k: v for k, v in detected_subscriptions.items()}

        # add manual subscriptions
        active_manual = self.get_active_manual()
        for sub in active_manual:
            # create dict matching detected format
            combined[sub.name] = {
                "merchant": sub.merchant,
                "amount": sub.amount,
                "category": sub.category,
                "interval_days": sub.interval_days,
                "interval_type": sub.interval_type,
                "source": "manual",
                "monthly_cost": sub.monthly_cost,
                "annual_cost": sub.annual_cost,
                "start_date": sub.start_date,
                "is_active": sub.is_active,
                "notes": sub.notes,
            }

        return combined

    def total_monthly_cost(
        self,
        detected_subscriptions: dict = None
    ) -> float:
        """total monthly cost (manual + detected)"""
        # manual only
        manual_total = sum(
            sub.monthly_cost for sub in self.get_active_manual()
        )

        # add detected if provided
        detected_total = 0
        if detected_subscriptions:
            for merchant, data in detected_subscriptions.items():
                # skip if we have a manual override
                if not any(
                    m.merchant == merchant
                    for m in self.get_active_manual()
                ):
                    interval_days = data.get("interval_days", 30)
                    amount = data.get("amount", 0)
                    detected_total += amount * (30 / interval_days)

        return manual_total + detected_total

    def total_annual_cost(
        self,
        detected_subscriptions: dict = None
    ) -> float:
        """total annual cost (manual + detected)"""
        return self.total_monthly_cost(detected_subscriptions) * 12

    def subscription_report(
        self,
        detected_subscriptions: dict = None
    ) -> str:
        """generate detailed subscription report"""
        combined = self.combined_recurring(detected_subscriptions or {})
        active_manual = self.get_active_manual()
        inactive_manual = [
            s for s in self.manual_subscriptions if not s.is_active
        ]

        output = []
        output.append("=" * 70)
        output.append("SUBSCRIPTION REPORT")
        output.append("=" * 70)

        # manual subscriptions
        if active_manual:
            output.append(f"\n--- manual subscriptions ({len(active_manual)}) ---")
            for sub in sorted(active_manual, key=lambda x: x.monthly_cost, reverse=True):
                output.append(
                    f"  {sub.name:.<35} "
                    f"${sub.amount:>8,.2f} "
                    f"({sub.interval_type}) "
                    f"→ ${sub.monthly_cost:>8,.2f}/mo"
                )
                if sub.notes:
                    output.append(f"    note: {sub.notes}")

        # detected subscriptions
        if detected_subscriptions:
            detected_only = [
                (k, v) for k, v in detected_subscriptions.items()
                if not any(
                    m.merchant == v.get('merchant')
                    for m in active_manual
                )
            ]

            if detected_only:
                output.append(f"\n--- detected subscriptions ({len(detected_only)}) ---")
                for merchant, data in sorted(
                    detected_only,
                    key=lambda x: x[1].get('amount', 0),
                    reverse=True
                )[:10]:
                    output.append(
                        f"  {merchant:.<35} "
                        f"${data['amount']:>8,.2f} "
                        f"({data['interval_type']}) "
                        f"[confidence: {data.get('confidence', 0):.0f}%]"
                    )

        # inactive subscriptions
        if inactive_manual:
            output.append(f"\n--- cancelled subscriptions ({len(inactive_manual)}) ---")
            for sub in inactive_manual:
                output.append(
                    f"  {sub.name:.<35} "
                    f"cancelled {sub.end_date.date()}"
                )

        # totals
        output.append(f"\n--- totals ---")
        monthly = self.total_monthly_cost(detected_subscriptions)
        annual = self.total_annual_cost(detected_subscriptions)
        output.append(f"monthly recurring: ${monthly:,.2f}")
        output.append(f"annual recurring: ${annual:,.2f}")

        output.append("\n" + "=" * 70)
        return "\n".join(output)
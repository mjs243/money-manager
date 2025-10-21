# analyzers/credit_card_tracker.py
# track credit card charges and payment deadlines

import json
from pathlib import Path
from datetime import datetime
from models.credit_card_charge import CreditCardCharge, ChargeStatus
from models.transaction import Transaction


class CreditCardTracker:
    """track credit card charges and ensure timely payment"""

    def __init__(self, config_path: str = "data/credit_card_charges.json"):
        self.config_path = Path(config_path)
        self.charges = []
        self._load_charges()

    def _load_charges(self):
        """load tracked charges from file"""
        if not self.config_path.exists():
            self.charges = []
            return

        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)

            self.charges = [
                CreditCardCharge(
                    date=datetime.fromisoformat(charge["date"]),
                    merchant=charge["merchant"],
                    amount=charge["amount"],
                    category=charge["category"],
                    card_name=charge["card_name"],
                    status=ChargeStatus(
                        charge.get("status", ChargeStatus.DETECTED.value)
                    ),
                    payment_date=(
                        datetime.fromisoformat(charge["payment_date"])
                        if charge.get("payment_date")
                        else None
                    ),
                    notes=charge.get("notes", ""),
                )
                for charge in data
            ]
            print(f"✅ loaded {len(self.charges)} credit card charges")
        except Exception as e:
            print(f"⚠️  error loading charges: {e}")
            self.charges = []

    def _save_charges(self):
        """save charges to file"""
        data = [
            {
                "date": charge.date.isoformat(),
                "merchant": charge.merchant,
                "amount": charge.amount,
                "category": charge.category,
                "card_name": charge.card_name,
                "status": charge.status.value,
                "payment_date": (
                    charge.payment_date.isoformat() if charge.payment_date else None
                ),
                "notes": charge.notes,
            }
            for charge in self.charges
        ]

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)

    def add_charge_from_transaction(
        self, transaction: Transaction, card_name: str
    ) -> CreditCardCharge:
        """create charge from transaction"""
        charge = CreditCardCharge(
            date=transaction.date,
            merchant=transaction.merchant,
            amount=transaction.amount,
            category=transaction.category,
            card_name=card_name,
        )

        self.charges.append(charge)
        self._save_charges()
        return charge

    def detect_unpaid_charges(self) -> list[CreditCardCharge]:
        """find charges that need payment"""
        unpaid = [
            c
            for c in self.charges
            if c.status != ChargeStatus.PAID and c.is_due_for_payment
        ]
        return sorted(unpaid, key=lambda x: x.date)

    def get_charges_by_status(self, status: ChargeStatus) -> list[CreditCardCharge]:
        """get charges by status"""
        return [c for c in self.charges if c.status == status]

    def get_pending_charges(self) -> list[CreditCardCharge]:
        """get all pending/unpaid charges"""
        return [
            c
            for c in self.charges
            if c.status in [ChargeStatus.DETECTED, ChargeStatus.PENDING_PAYMENT]
        ]

    def get_charges_due_soon(self, days: int = 15) -> list[CreditCardCharge]:
        """get charges due within N days"""
        return [
            c
            for c in self.charges
            if c.status != ChargeStatus.PAID and c.days_since_charge <= days
        ]

    def get_usage_health(self) -> dict:
        """Provides a behavioral metric for credit card usage this month."""
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)

        new_charges_this_month = [
            c
            for c in self.charges
            if c.date >= month_start and c.status != ChargeStatus.IGNORED
        ]

        num_charges = len(new_charges_this_month)
        total_spent = sum(c.amount for c in new_charges_this_month)

        status = "🟢 Low Usage"
        recommendation = "Great job keeping card usage low! Keep paying it off."
        if num_charges > 20:
            status = "🟡 Moderate Usage"
            recommendation = "Card usage is increasing. Be mindful of each swipe."
        if num_charges > 40:
            status = "🔴 High Usage"
            recommendation = (
                "High transaction volume risks overspending. Consider using debit/cash."
            )

        # sort charges by date (most recent first)
        sorted_charges = sorted(new_charges_this_month, key=lambda x: x.date, reverse=True)

        return {
            "New Charges This Month": num_charges,
            "Total Spent on Card This Month": total_spent,
            "Usage Status": status,
            "Recommendation": recommendation,
            "Charges List": sorted_charges,
        }

    def total_unpaid(self) -> float:
        """total unpaid amount"""
        return sum(c.amount for c in self.get_pending_charges())

    def total_paid_this_month(self) -> float:
        """total paid this month"""
        from datetime import datetime, timedelta

        month_start = datetime.now().replace(day=1)
        paid_this_month = [
            c
            for c in self.charges
            if c.status == ChargeStatus.PAID and c.payment_date >= month_start
        ]
        return sum(c.amount for c in paid_this_month)

    def payment_schedule(self) -> dict:
        """recommended payment schedule"""
        pending = self.get_pending_charges()

        if not pending:
            return {
                "next_check_15th": 0,
                "next_check_eom": 0,
                "total": 0,
            }

        # split into 15th and end-of-month payments
        charges_15th = [c for c in pending if c.days_since_charge <= 15]
        charges_eom = [c for c in pending if c.days_since_charge > 15]

        return {
            "next_check_15th": {
                "charges": charges_15th,
                "total": sum(c.amount for c in charges_15th),
                "count": len(charges_15th),
            },
            "next_check_eom": {
                "charges": charges_eom,
                "total": sum(c.amount for c in charges_eom),
                "count": len(charges_eom),
            },
            "grand_total": sum(c.amount for c in pending),
        }

    def mark_paid(self, merchant: str, amount: float = None):
        """mark charges as paid"""
        matched = []
        for charge in self.charges:
            if (
                charge.merchant.lower() == merchant.lower()
                and charge.status != ChargeStatus.PAID
            ):
                if amount is None or charge.amount == amount:
                    charge.mark_paid()
                    matched.append(charge)

        if matched:
            self._save_charges()
            print(f"✅ marked {len(matched)} charge(s) as paid")
        else:
            print(f"❌ no matching charges found")

    def payment_reminder_report(self) -> str:
        """generate payment reminder report"""
        schedule = self.payment_schedule()
        charges_15th = schedule.get("next_check_15th", {})
        charges_eom = schedule.get("next_check_eom", {})

        output = []
        output.append("=" * 70)
        output.append("CREDIT CARD PAYMENT REMINDER")
        output.append("=" * 70)

        output.append(f"\n--- payment schedule ---")
        output.append(f"total unpaid: ${schedule['grand_total']:,.2f}")

        # 15th check
        if charges_15th.get("charges"):
            output.append(f"\n--- due by 15th ({charges_15th['count']} charges) ---")
            output.append(f"total: ${charges_15th['total']:,.2f}")
            for charge in charges_15th["charges"]:
                output.append(
                    f"  {charge.date.date()} | "
                    f"{charge.merchant:.<25} | "
                    f"${charge.amount:>8,.2f}"
                )

        # end-of-month check
        if charges_eom.get("charges"):
            output.append(
                f"\n--- due by end of month ({charges_eom['count']} charges) ---"
            )
            output.append(f"total: ${charges_eom['total']:,.2f}")
            for charge in charges_eom["charges"]:
                output.append(
                    f"  {charge.date.date()} | "
                    f"{charge.merchant:.<25} | "
                    f"${charge.amount:>8,.2f}"
                )

        output.append("\n" + "=" * 70)
        return "\n".join(output)

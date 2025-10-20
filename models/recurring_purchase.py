# models/recurring_purchase.py
# track recurring purchases (not subscriptions)

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

class PurchaseFrequency(Enum):
    WEEKLY = "weekly"
    BI_WEEKLY = "bi_weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"
    CUSTOM = "custom"

@dataclass
class RecurringPurchase:
    """a recurring physical purchase (not subscription)"""
    name: str
    merchant: str
    amount: float
    category: str
    frequency: PurchaseFrequency
    interval_days: int
    last_purchase: datetime
    next_expected: datetime
    notes: str = ""
    is_active: bool = True
    purchase_history: list[datetime] = None

    def __post_init__(self):
        if self.purchase_history is None:
            self.purchase_history = [self.last_purchase]

    @property
    def days_until_next(self) -> int:
        """days until next expected purchase"""
        return max(0, (self.next_expected - datetime.now()).days)

    @property
    def is_due_soon(self) -> bool:
        """is purchase due in next 7 days?"""
        return self.days_until_next <= 7

    @property
    def is_overdue(self) -> bool:
        """is purchase overdue?"""
        return self.days_until_next == 0

    @property
    def monthly_cost(self) -> float:
        """estimate monthly cost"""
        return self.amount * (30 / self.interval_days)

    @property
    def annual_cost(self) -> float:
        """estimate annual cost"""
        return self.amount * (365 / self.interval_days)

    def record_purchase(self, amount: float = None, date: datetime = None):
        """record a new purchase and update next expected date"""
        purchase_date = date or datetime.now()
        purchase_amount = amount or self.amount

        self.purchase_history.append(purchase_date)
        self.last_purchase = purchase_date
        self.next_expected = purchase_date + timedelta(days=self.interval_days)

        # update amount if different
        if amount and amount != self.amount:
            self.amount = purchase_amount

    def snooze(self, days: int):
        """delay next expected purchase"""
        self.next_expected += timedelta(days=days)

    def __repr__(self) -> str:
        return (
            f"RecurringPurchase("
            f"name={self.name}, "
            f"amount=${self.amount:.2f}, "
            f"frequency={self.frequency.value}, "
            f"next={self.next_expected.date()}"
            ")"
        )
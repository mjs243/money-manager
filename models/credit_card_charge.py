# models/credit_card_charge.py
# track credit card charges for payment tracking

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class ChargeStatus(Enum):
    DETECTED = "detected"           # just found
    PENDING_PAYMENT = "pending"     # added to payoff plan
    PAID = "paid"                   # payment made
    IGNORED = "ignored"             # user chose not to track

@dataclass
class CreditCardCharge:
    """individual credit card charge for tracking"""
    date: datetime
    merchant: str
    amount: float
    category: str
    card_name: str
    status: ChargeStatus = ChargeStatus.DETECTED
    payment_date: datetime = None
    notes: str = ""

    @property
    def days_since_charge(self) -> int:
        """days since charge appeared"""
        return (datetime.now() - self.date).days

    @property
    def is_due_for_payment(self) -> bool:
        """should be paid within 30 days"""
        return self.days_since_charge >= 15 and self.status != ChargeStatus.PAID

    @property
    def days_until_due(self) -> int:
        """days until due (30 day window)"""
        return max(0, 30 - self.days_since_charge)

    def mark_paid(self, payment_date: datetime = None):
        """mark charge as paid"""
        self.status = ChargeStatus.PAID
        self.payment_date = payment_date or datetime.now()

    def __repr__(self) -> str:
        return (
            f"CreditCardCharge("
            f"date={self.date.date()}, "
            f"merchant={self.merchant}, "
            f"amount=${self.amount:.2f}, "
            f"status={self.status.value}"
            ")"
        )
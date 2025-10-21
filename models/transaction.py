# models/transaction.py
# transaction data model

from datetime import datetime
from dataclasses import dataclass

@dataclass
class Transaction:
    """represents a single transaction"""
    date: datetime
    account_type: str
    account_name: str
    institution: str
    merchant: str
    amount: float
    description: str
    category: str
    notes: str = ""
    source: str = "csv"  # "ynab" or "csv" - tracks where transaction came from

    @property
    def is_income(self) -> bool:
        """check if transaction is income (negative amount in export)"""
        return self.amount < 0 and self.category == "Income"

    @property
    def is_expense(self) -> bool:
        """check if this is actual spending"""
        return self.amount > 0

    def __repr__(self) -> str:
        return (
            f"Transaction("
            f"date={self.date.date()}, "
            f"merchant={self.merchant}, "
            f"amount=${abs(self.amount):.2f}, "
            f"category={self.category}"
            ")"
        )
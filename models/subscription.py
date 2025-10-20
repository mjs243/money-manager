# models/subscription.py
# manual subscription tracking

from dataclasses import dataclass
from datetime import datetime

@dataclass
class ManualSubscription:
    """manually tracked subscription"""
    name: str
    merchant: str
    amount: float
    category: str
    interval_days: int  # 7, 14, 30, 365, etc
    start_date: datetime
    end_date: datetime = None
    notes: str = ""
    is_active: bool = True

    @property
    def interval_type(self) -> str:
        """classify interval"""
        if 6 <= self.interval_days <= 8:
            return "weekly"
        elif 13 <= self.interval_days <= 15:
            return "bi-weekly"
        elif 27 <= self.interval_days <= 31:
            return "monthly"
        elif 89 <= self.interval_days <= 92:
            return "quarterly"
        elif 364 <= self.interval_days <= 366:
            return "annual"
        else:
            return f"every {self.interval_days} days"

    def monthly_cost(self) -> float:
        """estimate monthly cost"""
        return self.amount * (30 / self.interval_days)

    def annual_cost(self) -> float:
        """estimate annual cost"""
        return self.monthly_cost() * 12

    def __repr__(self) -> str:
        return (
            f"ManualSubscription("
            f"name={self.name}, "
            f"amount=${self.amount:.2f}, "
            f"interval={self.interval_type}"
            ")"
        )
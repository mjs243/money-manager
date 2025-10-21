# models/sinking_fund.py

from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class SinkingFund:
    """Represents a dedicated savings goal (e.g., house down payment)."""
    name: str
    goal_amount: float
    current_balance: float = 0.0
    monthly_contribution: float = 0.0
    target_date: datetime = None
    created_date: datetime = field(default_factory=datetime.now)

    @property
    def percentage_complete(self) -> float:
        """Calculates the completion percentage of the goal."""
        if self.goal_amount == 0:
            return 100.0
        return (self.current_balance / self.goal_amount) * 100

    @property
    def remaining_amount(self) -> float:
        """Calculates the amount still needed to reach the goal."""
        return max(0, self.goal_amount - self.current_balance)

    @property
    def months_to_goal(self) -> float | None:
        """Estimates the number of months to reach the goal at the current contribution rate."""
        if self.monthly_contribution == 0:
            return None
        return self.remaining_amount / self.monthly_contribution

    def contribute(self, amount: float):
        """Adds funds to the current balance."""
        self.current_balance += amount
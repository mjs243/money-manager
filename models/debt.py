from datetime import datetime
from dataclasses import dataclass

@dataclass
class DebtAccount:
    """represents a debt account (credit card, loan, etc)"""
    name: str
    account_type: str
    current_balance: float
    credit_limit: float = None
    interest_rate: float = 0.0
    minimum_payment: float = 0.0
    last_payment_date: datetime = None
    total_interest_paid: float = 0.0
    
    @property
    def utilization(self) -> float:
        """credit utilization %"""
        if not self.credit_limit:
            return 0
        return (self.current_balance / self.credit_limit) * 100
    
    @property
    def monthly_interest_rate(self) -> float:
        """convert annual aptr to monthly"""
        return self.interest_rate / 12
    
    def interest_accrued_monthly(self) -> float:
        """estimate interest accrued this month"""
        return self.current_balance * self.monthly_interest_rate
    
    def __repr__(self) -> str:
        return (
            f"DebtAccount("
            f"name={self.name}, "
            f"balance=${self.current_balance:,.2f}, "
            f"rate={self.interest_rate*100:.1f}%, "
            f"utilization={self.utilization:.1f}%"
            ")"
        )
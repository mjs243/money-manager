# models/want.py
# track wanted items with cooling-off period

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

class WantStatus(Enum):
    PENDING = "pending"          # initial entry
    CONFIRMED = "confirmed"      # passed check-ins
    CANCELLED = "cancelled"      # user cancelled
    PURCHASED = "purchased"      # bought

@dataclass
class Want:
    """a wanted item with cooling-off period"""
    name: str
    price: float
    category: str
    reason: str                  # why you want it
    created: datetime
    status: WantStatus = WantStatus.PENDING
    check_in_dates: list[datetime] = None
    purchased_date: datetime = None
    notes: str = ""

    def __post_init__(self):
        if self.check_in_dates is None:
            self.check_in_dates = []

    @property
    def days_since_creation(self) -> int:
        """days since want was created"""
        return (datetime.now() - self.created).days

    @property
    def next_check_in(self) -> datetime:
        """when next check-in is due (30 days after last)"""
        if not self.check_in_dates:
            return self.created + timedelta(days=30)
        return max(self.check_in_dates) + timedelta(days=30)

    @property
    def days_until_next_check_in(self) -> int:
        """days until next check-in"""
        return max(0, (self.next_check_in - datetime.now()).days)

    @property
    def check_ins_completed(self) -> int:
        """how many check-ins completed"""
        return len(self.check_in_dates)

    @property
    def is_ready_to_purchase(self) -> bool:
        """has passed 3 check-ins?"""
        return self.check_ins_completed >= 3 and self.status == WantStatus.PENDING

    def add_check_in(self):
        """add a check-in (called monthly)"""
        self.check_in_dates.append(datetime.now())
        if self.check_ins_completed >= 3:
            self.status = WantStatus.CONFIRMED

    def cancel(self):
        """cancel the want"""
        self.status = WantStatus.CANCELLED

    def purchase(self):
        """mark as purchased"""
        self.status = WantStatus.PURCHASED
        self.purchased_date = datetime.now()

    def __repr__(self) -> str:
        return (
            f"Want("
            f"name={self.name}, "
            f"price=${self.price:.2f}, "
            f"status={self.status.value}, "
            f"check_ins={self.check_ins_completed}/3"
            ")"
        )
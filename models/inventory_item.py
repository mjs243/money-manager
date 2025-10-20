# models/inventory_item.py
# track inventory items with expiration dates

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

class ItemStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    USED_UP = "used_up"
    DISCARDED = "discarded"

@dataclass
class InventoryItem:
    """item with expiration tracking"""
    name: str
    category: str
    purchase_date: datetime
    expiration_date: datetime
    quantity: int = 1
    unit: str = "units"  # units, liters, oz, etc
    location: str = ""  # where stored
    status: ItemStatus = ItemStatus.ACTIVE
    notes: str = ""

    @property
    def days_until_expiration(self) -> int:
        """days until expiration"""
        return max(0, (self.expiration_date - datetime.now()).days)

    @property
    def is_expired(self) -> bool:
        """is item expired?"""
        return self.days_until_expiration == 0

    @property
    def is_expiring_soon(self) -> bool:
        """expiring in next 7 days?"""
        return self.days_until_expiration <= 7 and self.days_until_expiration > 0

    @property
    def days_since_purchase(self) -> int:
        """days since purchased"""
        return (datetime.now() - self.purchase_date).days

    @property
    def shelf_life_days(self) -> int:
        """total shelf life in days"""
        return (self.expiration_date - self.purchase_date).days

    @property
    def shelf_life_remaining_percent(self) -> float:
        """% of shelf life remaining"""
        if self.shelf_life_days == 0:
            return 0
        return (self.days_until_expiration / self.shelf_life_days) * 100

    def mark_used(self, quantity: int = None):
        """mark item as used/consumed"""
        if quantity:
            self.quantity -= quantity
            if self.quantity <= 0:
                self.status = ItemStatus.USED_UP
        else:
            self.status = ItemStatus.USED_UP

    def mark_expired(self):
        """mark as expired"""
        self.status = ItemStatus.EXPIRED

    def __repr__(self) -> str:
        return (
            f"InventoryItem("
            f"name={self.name}, "
            f"expires={self.expiration_date.date()}, "
            f"days_left={self.days_until_expiration}"
            ")"
        )
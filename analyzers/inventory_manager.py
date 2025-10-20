# analyzers/inventory_manager.py
# manage inventory with expiration tracking

import json
from pathlib import Path
from datetime import datetime
from models.inventory_item import InventoryItem, ItemStatus

class InventoryManager:
    """manage inventory items with expiration dates"""

    def __init__(self, config_path: str = "data/inventory.json"):
        self.config_path = Path(config_path)
        self.items = []
        self._load_inventory()

    def _load_inventory(self):
        """load inventory from file"""
        if not self.config_path.exists():
            self.items = []
            return

        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)

            self.items = [
                InventoryItem(
                    name=item['name'],
                    category=item['category'],
                    purchase_date=datetime.fromisoformat(item['purchase_date']),
                    expiration_date=datetime.fromisoformat(item['expiration_date']),
                    quantity=item.get('quantity', 1),
                    unit=item.get('unit', 'units'),
                    location=item.get('location', ''),
                    status=ItemStatus(item.get('status', ItemStatus.ACTIVE.value)),
                    notes=item.get('notes', ''),
                )
                for item in data
            ]
            print(f"✅ loaded {len(self.items)} inventory items")
        except Exception as e:
            print(f"⚠️  error loading inventory: {e}")
            self.items = []

    def _save_inventory(self):
        """save inventory to file"""
        data = [
            {
                "name": item.name,
                "category": item.category,
                "purchase_date": item.purchase_date.isoformat(),
                "expiration_date": item.expiration_date.isoformat(),
                "quantity": item.quantity,
                "unit": item.unit,
                "location": item.location,
                "status": item.status.value,
                "notes": item.notes,
            }
            for item in self.items
        ]

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)

    def add_item(
        self,
        name: str,
        category: str,
        purchase_date: datetime,
        expiration_date: datetime,
        quantity: int = 1,
        unit: str = "units",
        location: str = "",
        notes: str = ""
    ) -> InventoryItem:
        """add inventory item"""
        item = InventoryItem(
            name=name,
            category=category,
            purchase_date=purchase_date,
            expiration_date=expiration_date,
            quantity=quantity,
            unit=unit,
            location=location,
            notes=notes,
        )

        self.items.append(item)
        self._save_inventory()
        print(f"✅ added item: {name}")
        return item

    def mark_used(self, name: str, quantity: int = None):
        """mark item as used"""
        for item in self.items:
            if item.name.lower() == name.lower():
                item.mark_used(quantity)
                self._save_inventory()
                print(f"✅ marked used: {name}")
                return

        print(f"❌ item not found: {name}")

    def get_active_items(self) -> list[InventoryItem]:
        """get all active items"""
        return [i for i in self.items if i.status == ItemStatus.ACTIVE]

    def get_expired(self) -> list[InventoryItem]:
        """get expired items"""
        return [i for i in self.get_active_items() if i.is_expired]

    def get_expiring_soon(self, days: int = 7) -> list[InventoryItem]:
        """get items expiring soon"""
        return [
            i for i in self.get_active_items()
            if i.is_expiring_soon
        ]

    def get_by_category(self) -> dict[str, list[InventoryItem]]:
        """organize by category"""
        result = {}
        for item in self.get_active_items():
            if item.category not in result:
                result[item.category] = []
            result[item.category].append(item)
        return result

    def inventory_report(self) -> str:
        """generate inventory report"""
        active = self.get_active_items()
        expired = self.get_expired()
        expiring_soon = self.get_expiring_soon()

        output = []
        output.append("=" * 70)
        output.append("INVENTORY REPORT")
        output.append("=" * 70)

        # stats
        output.append(f"\n--- overview ---")
        output.append(f"total active items: {len(active)}")
        output.append(f"expired items: {len(expired)}")
        output.append(f"expiring soon: {len(expiring_soon)}")

        # expired
        if expired:
            output.append(f"\n--- 🚨 expired items ({len(expired)}) ---")
            for item in expired:
                output.append(
                    f"  {item.name:.<35} "
                    f"expired {abs(item.days_until_expiration)} days ago"
                )

        # expiring soon
        if expiring_soon:
            output.append(f"\n--- ⚠️  expiring soon ({len(expiring_soon)}) ---")
            for item in expiring_soon:
                output.append(
                    f"  {item.name:.<35} "
                    f"expires {item.expiration_date.date()} "
                    f"({item.days_until_expiration} days)"
                )

        # all items by category
        by_category = self.get_by_category()
        if by_category:
            output.append(f"\n--- items by category ---")
            for category, items in sorted(by_category.items()):
                output.append(f"\n  {category}:")
                for item in sorted(items, key=lambda x: x.days_until_expiration):
                    status_icon = "🚨" if item.is_expired else "⚠️ " if item.is_expiring_soon else "✅"
                    output.append(
                        f"    {status_icon} {item.name:.<28} "
                        f"{item.quantity}{item.unit} "
                        f"expires {item.expiration_date.date()}"
                    )

        output.append("\n" + "=" * 70)
        return "\n".join(output)
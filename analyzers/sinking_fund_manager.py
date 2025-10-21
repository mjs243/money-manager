# analyzers/sinking_fund_manager.py

import json
from pathlib import Path
from datetime import datetime
from models.sinking_fund import SinkingFund

class SinkingFundManager:
    """Manages all sinking fund savings goals."""

    def __init__(self, config_path: str = "data/sinking_funds.json"):
        self.config_path = Path(config_path)
        self.funds = []
        self._load_funds()

    def _load_funds(self):
        """Loads sinking funds from a JSON file."""
        if not self.config_path.exists():
            return
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
            self.funds = [SinkingFund(**fund_data) for fund_data in data]
            print(f"✅ Loaded {len(self.funds)} sinking funds.")
        except Exception as e:
            print(f"⚠️ Error loading sinking funds: {e}")

    def _save_funds(self):
        """Saves sinking funds to a JSON file."""
        data = [fund.__dict__ for fund in self.funds]
        for item in data:
            # convert datetime objects to isoformat strings for json serialization
            for key, value in item.items():
                if isinstance(value, datetime):
                    item[key] = value.isoformat()
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)

    def add_fund(self, name: str, goal_amount: float, monthly_contribution: float, current_balance: float = 0.0):
        """Adds a new sinking fund."""
        fund = SinkingFund(
            name=name,
            goal_amount=goal_amount,
            monthly_contribution=monthly_contribution,
            current_balance=current_balance
        )
        self.funds.append(fund)
        self._save_funds()
        print(f"✅ Added sinking fund: {name}")

    def get_total_monthly_contribution(self) -> float:
        """Returns the total amount to be saved across all funds each month."""
        return sum(fund.monthly_contribution for fund in self.funds)

    def get_total_saved(self) -> float:
        """Returns the total amount currently saved across all funds."""
        return sum(fund.current_balance for fund in self.funds)
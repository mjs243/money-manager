# analyzers/spending.py
# analyze spending patterns

from models.transaction import Transaction
from datetime import datetime, timedelta
import config

class SpendingAnalyzer:
    """analyze spending by category, time period, etc"""

    def __init__(self, transactions: list[Transaction]):
        self.transactions = transactions
        self.expenses = [
            t for t in transactions
            if t.is_expense and t.amount > 0
        ]

    def total_spent(self) -> float:
        """total spending (all time)"""
        return sum(t.amount for t in self.expenses)

    def by_category(self) -> dict[str, float]:
        """spending breakdown by category"""
        result = {}
        for txn in self.expenses:
            result[txn.category] = result.get(txn.category, 0) + txn.amount
        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))

    def by_month(self) -> dict[str, float]:
        """spending by month"""
        result = {}
        for txn in self.expenses:
            month_key = txn.date.strftime('%Y-%m')
            result[month_key] = result.get(month_key, 0) + txn.amount
        return dict(sorted(result.items()))

    def category_by_month(self) -> dict[str, dict[str, float]]:
        """spending by category per month (for tracking trends)"""
        result = {}
        for txn in self.expenses:
            month_key = txn.date.strftime('%Y-%m')
            if month_key not in result:
                result[month_key] = {}
            cat = txn.category
            result[month_key][cat] = result[month_key].get(cat, 0) + txn.amount
        return dict(sorted(result.items()))

    def average_monthly(self) -> float:
        """average monthly spend"""
        by_month = self.by_month()
        if not by_month:
            return 0
        return sum(by_month.values()) / len(by_month)

    def top_merchants(self, limit: int = 10) -> list[tuple]:
        """top spending by merchant"""
        merchant_totals = {}
        for txn in self.expenses:
            merchant_totals[txn.merchant] = (
                merchant_totals.get(txn.merchant, 0) + txn.amount
            )
        sorted_merchants = sorted(
            merchant_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_merchants[:limit]

    def get_date_range(self) -> tuple[datetime, datetime]:
        """get min and max date from transactions"""
        if not self.transactions:
            return None, None
        dates = [t.date for t in self.transactions]
        return min(dates), max(dates)
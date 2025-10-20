# analyzers/anomalies.py
# detect spending anomalies, large purchases, patterns

from models.transaction import Transaction
from statistics import mean, stdev
import config

class AnomalyDetector:
    """find outliers, unusual spending patterns"""

    def __init__(self, transactions: list[Transaction]):
        self.transactions = [
            t for t in transactions
            if t.is_expense and t.amount > 0
        ]

    def large_purchases(self, percentile: float = 90) -> list[dict]:
        """
        find unusually large purchases.
        percentile: use 90th percentile as "large"
        """
        if not self.transactions:
            return []

        amounts = [t.amount for t in self.transactions]
        amounts_sorted = sorted(amounts)
        idx = int(len(amounts_sorted) * (percentile / 100))
        threshold = amounts_sorted[idx]

        large = []
        for txn in self.transactions:
            if txn.amount >= threshold:
                large.append({
                    "date": txn.date,
                    "merchant": txn.merchant,
                    "amount": txn.amount,
                    "category": txn.category,
                    "description": txn.description,
                })

        return sorted(
            large,
            key=lambda x: x["amount"],
            reverse=True
        )

    def statistical_outliers(self, std_dev_threshold: float = 2.0) -> list[dict]:
        """
        find purchases that are statistical outliers
        (more than N standard deviations from mean)
        """
        if len(self.transactions) < 2:
            return []

        amounts = [t.amount for t in self.transactions]
        avg = mean(amounts)
        std = stdev(amounts)

        if std == 0:
            return []

        outliers = []
        for txn in self.transactions:
            z_score = abs((txn.amount - avg) / std)
            if z_score >= std_dev_threshold:
                outliers.append({
                    "date": txn.date,
                    "merchant": txn.merchant,
                    "amount": txn.amount,
                    "category": txn.category,
                    "z_score": z_score,
                    "description": txn.description,
                })

        return sorted(
            outliers,
            key=lambda x: x["z_score"],
            reverse=True
        )

    def unusual_categories(self) -> dict[str, dict]:
        """
        find unusual spending in typically small categories.
        e.g., a $500 purchase at "Dining & Drinks"
        """
        # category thresholds (amounts we'd flag as weird)
        category_alerts = {
            "Dining & Drinks": 100,
            "Shopping": 200,
            "Entertainment & Rec.": 150,
            "Groceries": 250,
            "Auto & Transport": 300,
        }

        unusual = {}
        for txn in self.transactions:
            threshold = category_alerts.get(txn.category)
            if threshold and txn.amount > threshold:
                key = txn.category
                if key not in unusual:
                    unusual[key] = []
                unusual[key].append({
                    "date": txn.date,
                    "merchant": txn.merchant,
                    "amount": txn.amount,
                    "description": txn.description,
                })

        # sort each category by amount
        for cat in unusual:
            unusual[cat] = sorted(
                unusual[cat],
                key=lambda x: x["amount"],
                reverse=True
            )

        return unusual

    def duplicate_transactions(self, tolerance: float = 0.01) -> list[list]:
        """
        find potential duplicate transactions
        (same merchant, similar amount, close dates)
        """
        duplicates = []

        for i, txn1 in enumerate(self.transactions):
            for txn2 in self.transactions[i+1:]:
                # same merchant
                if txn1.merchant != txn2.merchant:
                    continue

                # similar amount (within tolerance %)
                diff = abs(txn1.amount - txn2.amount)
                pct_diff = diff / max(txn1.amount, txn2.amount)
                if pct_diff > tolerance:
                    continue

                # within 7 days
                days_diff = abs((txn1.date - txn2.date).days)
                if days_diff > 7:
                    continue

                # found a match
                duplicates.append([
                    {
                        "date": txn1.date,
                        "merchant": txn1.merchant,
                        "amount": txn1.amount,
                        "description": txn1.description,
                    },
                    {
                        "date": txn2.date,
                        "merchant": txn2.merchant,
                        "amount": txn2.amount,
                        "description": txn2.description,
                    },
                ])

        return duplicates
# analyzers/subscriptions.py
# detect recurring/subscription charges based on actual transaction patterns

from models.transaction import Transaction
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


class SubscriptionDetector:
    """find recurring charges by analyzing transaction patterns"""

    def __init__(self, transactions: list[Transaction]):
        self.transactions = [t for t in transactions if t.is_expense and t.amount > 0]

    def find_recurring(
        self,
        min_occurrences: int = 3,
        amount_tolerance: float = 0.05,
        day_variance: int = 3,
    ) -> dict[str, dict]:
        """
        find transactions that repeat regularly.

        min_occurrences: minimum times charge appears
        amount_tolerance: allow ±5% variance in amount
        day_variance: allow ±3 days variance in day of month
        """
        # group transactions by merchant
        by_merchant = defaultdict(list)
        for txn in self.transactions:
            by_merchant[txn.merchant].append(txn)

        recurring = {}

        for merchant, txns in by_merchant.items():
            if len(txns) < min_occurrences:
                continue

            # sort by date
            txns_sorted = sorted(txns, key=lambda t: t.date)

            # analyze intervals between transactions
            intervals = []
            for i in range(len(txns_sorted) - 1):
                delta = (txns_sorted[i + 1].date - txns_sorted[i].date).days
                intervals.append(delta)

            # skip if no consistent pattern
            if not intervals:
                continue

            # check if intervals are consistent (within tolerance)
            avg_interval = statistics.mean(intervals)
            std_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0

            # recurring must have low variance in intervals
            # (allow up to 50% variance)
            if std_interval > avg_interval * 0.50:
                continue

            # check amount variance
            amounts = [t.amount for t in txns_sorted]
            avg_amount = statistics.mean(amounts)
            max_amount = max(amounts)
            min_amount = min(amounts)
            amount_variance = (max_amount - min_amount) / avg_amount

            # skip if amounts vary too much
            if amount_variance > amount_tolerance:
                continue

            # this is recurring!
            recurring[merchant] = {
                "merchant": merchant,
                "amount": avg_amount,
                "amount_min": min_amount,
                "amount_max": max_amount,
                "count": len(txns_sorted),
                "interval_days": avg_interval,
                "interval_type": self._classify_interval(avg_interval),
                "std_dev_days": std_interval,
                "category": txns_sorted[0].category,
                "first_date": txns_sorted[0].date,
                "last_date": txns_sorted[-1].date,
                "transactions": txns_sorted,
                "confidence": self._calculate_confidence(
                    len(txns_sorted), std_interval, amount_variance
                ),
            }

        # sort by confidence
        return dict(
            sorted(recurring.items(), key=lambda x: x[1]["confidence"], reverse=True)
        )

    @staticmethod
    def _classify_interval(days: float) -> str:
        """classify recurring pattern"""
        if 6 <= days <= 8:
            return "weekly"
        elif 13 <= days <= 15:
            return "bi-weekly"
        elif 27 <= days <= 31:
            return "monthly"
        elif 89 <= days <= 92:
            return "quarterly"
        elif 364 <= days <= 366:
            return "annual"
        else:
            return f"every {days:.0f} days"

    @staticmethod
    def _calculate_confidence(count: int, std_dev: float, amount_var: float) -> float:
        """
        calculate confidence score (0-100).
        higher = more confident it's actually recurring.
        """
        # more occurrences = higher confidence
        count_score = min(count / 10, 1.0) * 50

        # lower std dev = higher confidence
        std_score = (1 - min(std_dev / 10, 1.0)) * 30

        # lower amount variance = higher confidence
        amount_score = (1 - amount_var) * 20

        return count_score + std_score + amount_score

    def estimated_monthly_recurring(self) -> float:
        """estimate total monthly recurring charges"""
        recurring = self.find_recurring()
        total = 0

        for merchant, data in recurring.items():
            interval_days = data["interval_days"]
            monthly_occurrences = 30 / interval_days
            monthly_cost = data["amount"] * monthly_occurrences
            total += monthly_cost

        return total

    def estimated_annual_recurring(self) -> float:
        """estimate total annual recurring charges"""
        return self.estimated_monthly_recurring() * 12

    def recurring_by_category(self) -> dict[str, float]:
        """breakdown of recurring by category"""
        recurring = self.find_recurring()
        result = {}

        for merchant, data in recurring.items():
            cat = data["category"]
            interval_days = data["interval_days"]
            monthly_occurrences = 30 / interval_days
            monthly_cost = data["amount"] * monthly_occurrences

            if cat not in result:
                result[cat] = 0
            result[cat] += monthly_cost

        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))

    def analyze_gaps(self) -> list[dict]:
        """
        find subscriptions that might have been cancelled.
        (were recurring, now haven't appeared in a while)
        """
        recurring = self.find_recurring(min_occurrences=2)
        today = max(t.date for t in self.transactions).date()

        gaps = []
        for merchant, data in recurring.items():
            last_date = data["last_date"]
            expected_interval = data["interval_days"]

            # how long since last transaction?
            days_since = (today - last_date.date()).days

            # if it's been longer than 1.5x the normal interval
            if days_since > (expected_interval * 1.5):
                gaps.append(
                    {
                        "merchant": merchant,
                        "last_occurrence": last_date,
                        "days_since": days_since,
                        "expected_interval": expected_interval,
                        "status": "possibly cancelled",
                        "avg_monthly_impact": (
                            data["amount"] * (30 / expected_interval)
                        ),
                    }
                )

        return sorted(gaps, key=lambda x: x["days_since"], reverse=True)

    def potential_duplicates_in_recurring(self) -> list[dict]:
        """
        find recurring charges that might be duplicates
        (e.g., subscribed twice to same service)
        """
        recurring = self.find_recurring()
        duplicates = []

        # look for similar merchants with different names
        merchants = list(recurring.keys())
        for i, m1 in enumerate(merchants):
            for m2 in merchants[i + 1 :]:
                # check if merchant names are similar
                if self._merchants_similar(m1, m2):
                    data1 = recurring[m1]
                    data2 = recurring[m2]

                    # check if amounts are similar
                    amount_diff = abs(data1["amount"] - data2["amount"])
                    pct_diff = amount_diff / max(data1["amount"], data2["amount"])

                    if pct_diff < 0.10:  # within 10%
                        duplicates.append(
                            {
                                "merchant_1": m1,
                                "merchant_2": m2,
                                "amount_1": data1["amount"],
                                "amount_2": data2["amount"],
                                "total_monthly_duplicate": (
                                    data1["amount"] * (30 / data1["interval_days"])
                                    + data2["amount"] * (30 / data2["interval_days"])
                                ),
                                "recommendation": "verify if intentional",
                            }
                        )

        return duplicates

    @staticmethod
    def _merchants_similar(m1: str, m2: str) -> bool:
        """check if two merchant names are similar"""
        m1_lower = m1.lower()
        m2_lower = m2.lower()

        # exact match
        if m1_lower == m2_lower:
            return True

        # one contains the other
        if m1_lower in m2_lower or m2_lower in m1_lower:
            return True

        # check common keywords
        keywords = ["paypal", "amazon", "apple", "google", "spotify", "netflix"]
        for kw in keywords:
            if kw in m1_lower and kw in m2_lower:
                return True

        return False

    def subscription_health_check(self) -> dict:
        """
        overall health check on subscriptions.
        what's active, what might be cancelled, potential duplicates
        """
        recurring = self.find_recurring()
        gaps = self.analyze_gaps()
        dupes = self.potential_duplicates_in_recurring()

        active = len(recurring)
        possibly_cancelled = len(gaps)
        potential_duplicates = len(dupes)

        monthly_total = self.estimated_monthly_recurring()
        annual_total = self.estimated_annual_recurring()

        return {
            "active_subscriptions": active,
            "possibly_cancelled": possibly_cancelled,
            "potential_duplicates": potential_duplicates,
            "monthly_total": monthly_total,
            "annual_total": annual_total,
            "recommendation": (
                f"review {possibly_cancelled} possibly cancelled subscriptions "
                f"and {potential_duplicates} potential duplicates"
                if (possibly_cancelled > 0 or potential_duplicates > 0)
                else "subscriptions look clean"
            ),
        }

    def mark_as_subscription(
        self,
        merchant: str,
        amount: float,
        category: str,
        interval_days: int,
        start_date,
        subscription_manager=None,
    ) -> bool:
        """
        mark a transaction as subscription in manager.
        useful for first-time charges.
        """
        if not subscription_manager:
            return False

        # generate name from merchant
        name = f"{merchant} (Manual)"

        try:
            subscription_manager.add_subscription(
                name=name,
                merchant=merchant,
                amount=amount,
                category=category,
                interval_days=interval_days,
                start_date=start_date,
            )
            return True
        except Exception as e:
            print(f"❌ error marking subscription: {e}")
            return False

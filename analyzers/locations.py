# analyzers/locations.py
# analyze spending by location/merchant

from models.transaction import Transaction
from collections import Counter

class LocationAnalyzer:
    """find frequent spending locations and merchant patterns"""

    def __init__(self, transactions: list[Transaction]):
        self.transactions = [
            t for t in transactions
            if t.is_expense and t.amount > 0
        ]

    def extract_location(self, description: str) -> str | None:
        """
        extract city/state from description
        e.g., "POS Debit - ... Knightdale NC" -> "Knightdale, NC"
        """
        # look for patterns like "CITY STATE" at end
        parts = description.split()

        # try last two parts (state code + potential city)
        if len(parts) >= 2:
            potential_state = parts[-1].upper()
            # us state codes are 2 letters
            if len(potential_state) == 2 and potential_state.isalpha():
                # grab last city-like word before state
                potential_city = parts[-2].title()
                return f"{potential_city}, {potential_state}"

        return None

    def frequent_locations(self, limit: int = 10) -> list[tuple]:
        """find most frequent spending locations"""
        locations = []

        for txn in self.transactions:
            loc = self.extract_location(txn.description)
            if loc:
                locations.append(loc)

        counter = Counter(locations)
        return counter.most_common(limit)

    def spending_by_location(self) -> dict[str, float]:
        """total spending by location"""
        result = {}

        for txn in self.transactions:
            loc = self.extract_location(txn.description)
            if loc:
                result[loc] = result.get(loc, 0) + txn.amount

        return dict(sorted(
            result.items(),
            key=lambda x: x[1],
            reverse=True
        ))

    def merchant_frequency(self, limit: int = 15) -> list[tuple]:
        """
        find merchants you visit most often
        (by transaction count, not amount)
        """
        merchants = [t.merchant for t in self.transactions]
        counter = Counter(merchants)
        return counter.most_common(limit)

    def category_by_location(self) -> dict[str, dict[str, float]]:
        """
        see what categories you spend on at each location
        useful for identifying patterns
        """
        result = {}

        for txn in self.transactions:
            loc = self.extract_location(txn.description)
            if loc:
                if loc not in result:
                    result[loc] = {}
                cat = txn.category
                result[loc][cat] = result[loc].get(cat, 0) + txn.amount

        return result

    def commute_analysis(self) -> dict:
        """
        detect commute spending (gas, public transit)
        based on gas stations + transport merchants
        """
        commute_keywords = [
            "SUNOCO",
            "EXXON",
            "SHELL",
            "CHEVRON",
            "MOBIL",
            "UBER",
            "LYFT",
            "METRO",
            "TRANSIT",
        ]

        commute_txns = []
        for txn in self.transactions:
            if any(
                kw in txn.merchant.upper()
                for kw in commute_keywords
            ):
                commute_txns.append(txn)

        if not commute_txns:
            return {"total": 0, "transactions": 0}

        total = sum(t.amount for t in commute_txns)
        return {
            "total": total,
            "transactions": len(commute_txns),
            "monthly_avg": total / max(
                len(set(t.date.strftime('%Y-%m') for t in commute_txns)),
                1
            ),
            "top_merchant": Counter(
                [t.merchant for t in commute_txns]
            ).most_common(1)[0][0],
        }
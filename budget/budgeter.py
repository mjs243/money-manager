# budget/budgeter.py
# build personalized budget

from analyzers.spending import SpendingAnalyzer
import config

class Budgeter:
    """create budget recommendations based on spending"""

    def __init__(self, spending_analyzer: SpendingAnalyzer):
        self.analyzer = spending_analyzer
        self.avg_monthly = spending_analyzer.average_monthly()

    def get_budget_targets(self) -> dict:
        """recommended budget by category"""
        return config.budget_targets

    def vs_targets(self) -> dict[str, dict]:
        """compare actual spending to targets"""
        by_cat = self.analyzer.by_category()
        months = len(self.analyzer.by_month())
        months = max(months, 1)  # avoid division by zero

        result = {}
        for cat, total_spent in by_cat.items():
            avg_monthly = total_spent / months
            target = config.budget_targets.get(cat, avg_monthly)

            result[cat] = {
                "avg_monthly": avg_monthly,
                "target": target,
                "difference": target - avg_monthly,
                "over_under": "under" if avg_monthly <= target else "over",
            }

        return result

    def house_fund_projection(self, monthly_contribution: float = 500) -> dict:
        """
        project when you'll hit down payment goal
        """
        goal_data = config.house_down_payment
        current = goal_data["current_savings"]
        target = goal_data["target_amount"]
        gap = target - current

        if monthly_contribution <= 0:
            return {
                "status": "unreachable",
                "message": "need positive monthly contribution",
            }

        months_needed = gap / monthly_contribution
        years_needed = months_needed / 12

        return {
            "current_savings": current,
            "goal_amount": target,
            "gap": gap,
            "monthly_contribution": monthly_contribution,
            "months_to_goal": months_needed,
            "years_to_goal": years_needed,
            "status": "on_track",
        }
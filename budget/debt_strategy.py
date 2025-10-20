# budget/debt_strategy.py
# integrate debt payoff into overall budget

from analyzers.debt import DebtAnalyzer
from analyzers.spending import SpendingAnalyzer

class DebtStrategy:
    """create debt payoff strategy integrated with budget"""

    def __init__(
        self,
        debt_analyzer: DebtAnalyzer,
        spending_analyzer: SpendingAnalyzer
    ):
        self.debt = debt_analyzer
        self.spending = spending_analyzer

    def recommended_payoff_budget(self) -> dict:
        """
        based on spending, recommend debt payoff allocation.
        looks for "fat" in spending to redirect to debt.
        """
        avg_monthly_spend = self.spending.average_monthly()
        avg_monthly_income = 2300  # from your payroll deposits

        available_for_debt = avg_monthly_income - avg_monthly_spend

        return {
            "monthly_income": avg_monthly_income,
            "monthly_spending": avg_monthly_spend,
            "available_for_debt": available_for_debt,
            "recommendation": (
                "aggressive debt payoff possible" if available_for_debt > 500
                else "moderate debt payoff" if available_for_debt > 250
                else "minimal - need to cut spending first"
            ),
        }

    def spending_cuts_for_debt(self) -> list[dict]:
        """identify spending categories to cut for debt payoff"""
        by_cat = self.spending.by_category()
        months = len(self.spending.by_month())
        months = max(months, 1)

        cuts = []
        discretionary_categories = [
            "Dining & Drinks",
            "Entertainment & Rec.",
            "Shopping",
            "Software & Tech",
        ]

        for cat in discretionary_categories:
            if cat in by_cat:
                monthly_avg = by_cat[cat] / months
                potential_cut = monthly_avg * 0.30  # cut 30%

                cuts.append({
                    "category": cat,
                    "current_monthly": monthly_avg,
                    "potential_cut": potential_cut,
                    "remaining_budget": monthly_avg - potential_cut,
                })

        # sort by potential savings
        cuts = sorted(cuts, key=lambda x: x["potential_cut"], reverse=True)
        total_potential = sum(c["potential_cut"] for c in cuts)

        return {
            "cuts": cuts,
            "total_monthly_savings": total_potential,
            "annual_debt_payoff": total_potential * 12,
        }

    def debt_vs_savings_tradeoff(self) -> dict:
        """
        should you pay off debt or save for house?
        debt payoff vs down payment contribution
        """
        avg_monthly_spend = self.spending.average_monthly()
        avg_monthly_income = 2300

        # current situation
        current_surplus = avg_monthly_income - avg_monthly_spend
        total_debt = self.debt.total_debt()
        total_monthly_interest = self.debt.total_monthly_interest()

        # scenarios
        scenarios = []

        # scenario 1: aggressively pay debt (80% of surplus)
        debt_payment_1 = current_surplus * 0.80
        months_to_clear_1 = total_debt / debt_payment_1 if debt_payment_1 > 0 else float('inf')
        interest_cost_1 = total_monthly_interest * months_to_clear_1

        scenarios.append({
            "name": "aggressive debt payoff (80% to debt)",
            "monthly_to_debt": debt_payment_1,
            "monthly_to_savings": current_surplus - debt_payment_1,
            "months_to_debt_free": months_to_clear_1,
            "interest_cost": interest_cost_1,
            "down_payment_progress": (current_surplus - debt_payment_1) * months_to_clear_1,
        })

        # scenario 2: balanced (50/50)
        debt_payment_2 = current_surplus * 0.50
        months_to_clear_2 = total_debt / debt_payment_2 if debt_payment_2 > 0 else float('inf')
        interest_cost_2 = total_monthly_interest * months_to_clear_2

        scenarios.append({
            "name": "balanced (50% to debt, 50% to savings)",
            "monthly_to_debt": debt_payment_2,
            "monthly_to_savings": current_surplus - debt_payment_2,
            "months_to_debt_free": months_to_clear_2,
            "interest_cost": interest_cost_2,
            "down_payment_progress": (current_surplus - debt_payment_2) * months_to_clear_2,
        })

        # scenario 3: minimum + save for house
        debt_payment_3 = sum(
            acc.minimum_payment for acc in self.debt.accounts
        )
        months_to_clear_3 = total_debt / debt_payment_3 if debt_payment_3 > 0 else float('inf')
        interest_cost_3 = total_monthly_interest * months_to_clear_3

        scenarios.append({
            "name": "minimums only (max house savings)",
            "monthly_to_debt": debt_payment_3,
            "monthly_to_savings": current_surplus - debt_payment_3,
            "months_to_debt_free": months_to_clear_3,
            "interest_cost": interest_cost_3,
            "down_payment_progress": (current_surplus - debt_payment_3) * months_to_clear_3,
        })

        return {
            "total_debt": total_debt,
            "monthly_interest_cost": total_monthly_interest,
            "annual_interest_cost": total_monthly_interest * 12,
            "scenarios": scenarios,
            "recommendation": (
                "scenario 1 recommended: "
                "each month of delay costs ~${:.2f} in interest".format(
                    total_monthly_interest
                )
            ),
        }
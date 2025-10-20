# analyzers/debt.py
# analyze debt, find payoff strategies

from models.debt import DebtAccount
from models.transaction import Transaction

class DebtAnalyzer:
    """analyze debt accounts and create payoff plans"""

    def __init__(self, debt_accounts: list[DebtAccount]):
        self.accounts = debt_accounts
        self.accounts_by_rate = sorted(
            debt_accounts,
            key=lambda x: x.interest_rate,
            reverse=True
        )

    def total_debt(self) -> float:
        """sum of all debt balances"""
        return sum(acc.current_balance for acc in self.accounts)

    def total_monthly_interest(self) -> float:
        """how much interest you're paying monthly"""
        return sum(acc.interest_accrued_monthly() for acc in self.accounts)

    def total_annual_interest(self) -> float:
        """how much interest you'll pay in a year (rough)"""
        return self.total_monthly_interest() * 12

    def avg_interest_rate(self) -> float:
        """weighted average interest rate"""
        if self.total_debt() == 0:
            return 0
        total_interest_rate = sum(
            acc.current_balance * acc.interest_rate
            for acc in self.accounts
        )
        return total_interest_rate / self.total_debt()

    def high_utilization_accounts(self, threshold: float = 0.50) -> list:
        """find credit cards with high utilization (> 50%)"""
        high_util = []
        for acc in self.accounts:
            if acc.account_type == "credit_card" and acc.utilization > (threshold * 100):
                high_util.append({
                    "name": acc.name,
                    "balance": acc.current_balance,
                    "limit": acc.credit_limit,
                    "utilization": acc.utilization,
                    "impact": "hurts credit score",
                })
        return high_util

    def avalanche_strategy(self, monthly_payment: float) -> list[dict]:
        """
        debt avalanche: pay minimums on all, attack highest rate first.
        mathematically optimal for interest savings.
        """
        if monthly_payment <= 0:
            return []

        # sort by interest rate (highest first)
        sorted_by_rate = sorted(
            self.accounts,
            key=lambda x: x.interest_rate,
            reverse=True
        )

        strategy = []
        for i, acc in enumerate(sorted_by_rate):
            if i == 0:
                # attack the high-rate debt
                extra_payment = monthly_payment - sum(
                    a.minimum_payment for a in self.accounts
                )
                total_payment = acc.minimum_payment + extra_payment
            else:
                # just minimum
                total_payment = acc.minimum_payment

            months_to_payoff = self._months_to_payoff(
                acc.current_balance,
                total_payment,
                acc.monthly_interest_rate
            )

            strategy.append({
                "account": acc.name,
                "current_balance": acc.current_balance,
                "interest_rate": acc.interest_rate * 100,
                "monthly_payment": total_payment,
                "months_to_payoff": months_to_payoff,
                "priority": i + 1,
                "rationale": "highest interest rate first (saves most interest)",
            })

        return strategy

    def snowball_strategy(self, monthly_payment: float) -> list[dict]:
        """
        debt snowball: pay minimums on all, attack smallest balance first.
        psychologically rewarding (quick wins), but costs more in interest.
        """
        if monthly_payment <= 0:
            return []

        # sort by balance (smallest first)
        sorted_by_balance = sorted(
            self.accounts,
            key=lambda x: x.current_balance
        )

        strategy = []
        for i, acc in enumerate(sorted_by_balance):
            if i == 0:
                # attack the small debt
                extra_payment = monthly_payment - sum(
                    a.minimum_payment for a in self.accounts
                )
                total_payment = acc.minimum_payment + extra_payment
            else:
                # just minimum
                total_payment = acc.minimum_payment

            months_to_payoff = self._months_to_payoff(
                acc.current_balance,
                total_payment,
                acc.monthly_interest_rate
            )

            strategy.append({
                "account": acc.name,
                "current_balance": acc.current_balance,
                "interest_rate": acc.interest_rate * 100,
                "monthly_payment": total_payment,
                "months_to_payoff": months_to_payoff,
                "priority": i + 1,
                "rationale": "smallest balance first (psychological wins)",
            })

        return strategy

    def balance_transfer_analysis(self) -> dict:
        """
        identify candidates for 0% balance transfer offers.
        usually: pay transfer fee (1-3%), get 0% for 6-21 months.
        """
        cc_debt = [
            acc for acc in self.accounts
            if acc.account_type == "credit_card"
        ]

        if not cc_debt:
            return {"candidates": []}

        # sort by interest rate (highest first = best candidates)
        sorted_by_rate = sorted(
            cc_debt,
            key=lambda x: x.interest_rate,
            reverse=True
        )

        candidates = []
        for acc in sorted_by_rate[:3]:  # top 3
            transfer_fee_percent = 0.03  # assume 3%
            transfer_fee = acc.current_balance * transfer_fee_percent

            # how much you'd save with 0% for 12 months
            interest_if_kept = acc.current_balance * acc.interest_rate
            savings = interest_if_kept - transfer_fee

            if savings > 0:
                candidates.append({
                    "account": acc.name,
                    "current_balance": acc.current_balance,
                    "current_rate": acc.interest_rate * 100,
                    "transfer_fee": transfer_fee,
                    "annual_interest_if_kept": interest_if_kept,
                    "potential_savings": savings,
                })

        return {
            "candidates": candidates,
            "total_potential_savings": sum(
                c["potential_savings"] for c in candidates
            ),
        }

    def payoff_timeline(
        self,
        monthly_payment: float,
        strategy: str = "avalanche"
    ) -> dict:
        """
        project timeline to be debt-free using a strategy.
        strategy: "avalanche" or "snowball"
        """
        if strategy == "avalanche":
            plan = self.avalanche_strategy(monthly_payment)
        elif strategy == "snowball":
            plan = self.snowball_strategy(monthly_payment)
        else:
            return {}

        # find when last debt is paid off
        total_months = max(
            p["months_to_payoff"] for p in plan
        ) if plan else 0

        total_interest_paid = self._project_total_interest(
            plan,
            total_months
        )

        return {
            "strategy": strategy,
            "monthly_payment": monthly_payment,
            "months_to_debt_free": total_months,
            "years_to_debt_free": total_months / 12,
            "projected_total_interest": total_interest_paid,
            "payoff_plan": plan,
        }

    def utilization_impact(self) -> dict:
        """explain credit utilization impact"""
        cc_accounts = [
            acc for acc in self.accounts
            if acc.account_type == "credit_card"
        ]

        if not cc_accounts:
            return {}

        total_limit = sum(acc.credit_limit for acc in cc_accounts if acc.credit_limit)
        total_balance = sum(acc.current_balance for acc in cc_accounts)
        overall_utilization = (total_balance / total_limit * 100) if total_limit > 0 else 0

        return {
            "overall_utilization": overall_utilization,
            "accounts": [
                {
                    "name": acc.name,
                    "utilization": acc.utilization,
                    "status": "🔴 high" if acc.utilization > 50 else "🟡 moderate" if acc.utilization > 30 else "🟢 low",
                }
                for acc in cc_accounts
            ],
            "credit_score_impact": (
                "severely hurts" if overall_utilization > 70
                else "hurts" if overall_utilization > 50
                else "slightly impacts" if overall_utilization > 30
                else "minimal impact"
            ),
            "recommendation": (
                "pay down high-utilization cards ASAP" if overall_utilization > 50
                else "keep paying down, getting close to optimal"
            ),
        }

    @staticmethod
    def _months_to_payoff(
        balance: float,
        monthly_payment: float,
        monthly_rate: float
    ) -> float:
        """
        calculate months needed to pay off a debt.
        using standard loan payoff formula.
        """
        if monthly_payment <= 0:
            return float('inf')

        if monthly_rate == 0:
            return balance / monthly_payment

        # months = -log(1 - (balance * rate / payment)) / log(1 + rate)
        import math
        try:
            numerator = 1 - (balance * monthly_rate / monthly_payment)
            if numerator <= 0:
                return float('inf')
            months = -math.log(numerator) / math.log(1 + monthly_rate)
            return max(0, months)
        except:
            return float('inf')

    @staticmethod
    def _project_total_interest(plan: list[dict], months: int) -> float:
        """rough estimate of total interest paid over timeline"""
        total = 0
        for item in plan:
            # simplified: assume consistent payment
            balance = item["current_balance"]
            rate = item["interest_rate"] / 100 / 12
            payment = item["monthly_payment"]

            remaining = balance
            for _ in range(int(item["months_to_payoff"])):
                interest = remaining * rate
                total += interest
                remaining -= (payment - interest)
                if remaining <= 0:
                    break

        return total
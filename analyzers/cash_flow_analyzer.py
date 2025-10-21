# analyzers/cash_flow_analyzer.py

from analyzers.spending import SpendingAnalyzer
from analyzers.subscription_manager import SubscriptionManager
from analyzers.recurring_purchases_manager import RecurringPurchasesManager
from analyzers.debt import DebtAnalyzer
from analyzers.sinking_fund_manager import SinkingFundManager

class CashFlowAnalyzer:
    """Projects monthly cash flow and creates a strategic allocation plan."""

    def __init__(
        self,
        spending_analyzer: SpendingAnalyzer,
        subscription_manager: SubscriptionManager,
        recurring_purchases_manager: RecurringPurchasesManager,
        debt_analyzer: DebtAnalyzer,
        sinking_fund_manager: SinkingFundManager,
        monthly_income: float,
        checking_balance: float
    ):
        self.spending = spending_analyzer
        self.subs = subscription_manager
        self.purchases = recurring_purchases_manager
        self.debt = debt_analyzer
        self.sinking_funds = sinking_fund_manager
        self.monthly_income = monthly_income
        self.checking_balance = checking_balance

    def generate_allocation_plan(self) -> dict:
        """Creates a 'Pay Yourself First' allocation plan for the month."""
        # 1. Fixed & Essential Costs
        essential_costs = (
            self.subs.total_monthly_cost() +
            self.purchases.total_monthly_cost()
        )
        
        # 2. Savings Goals (from sinking funds)
        savings_goals = self.sinking_funds.get_total_monthly_contribution()

        # 3. Debt Payoff
        min_debt_payments = sum(acc.minimum_payment for acc in self.debt.accounts)
        
        # Calculate remaining income after essentials, savings, and min payments
        remaining_for_extras = self.monthly_income - essential_costs - savings_goals - min_debt_payments

        # 4. Aggressive Debt Payoff (Avalanche)
        # let's allocate 50% of the remainder to extra debt payments
        aggressive_debt_payment = remaining_for_extras * 0.5
        
        # 5. Discretionary Spending (what's truly left)
        discretionary_budget = remaining_for_extras - aggressive_debt_payment

        plan = {
            "Income": self.monthly_income,
            "1. Essential Costs (Subs & Recurring)": essential_costs,
            "2. Savings Goals (Sinking Funds)": savings_goals,
            "3. Minimum Debt Payments": min_debt_payments,
            "4. Aggressive Debt Payoff (Avalanche)": aggressive_debt_payment,
            "5. Discretionary Spending Budget": discretionary_budget,
            "Projected Monthly Surplus": discretionary_budget - self.spending.average_monthly(), # compare to historical discretionary
        }
        return plan

    def project_checking_account_balance(self) -> dict:
        """Forecasts the checking account balance to prevent overdrafts."""
        plan = self.generate_allocation_plan()
        
        # Total planned outflows for the month
        total_outflows = (
            plan["1. Essential Costs (Subs & Recurring)"] +
            plan["2. Savings Goals (Sinking Funds)"] +
            plan["3. Minimum Debt Payments"] +
            plan["4. Aggressive Debt Payoff (Avalanche)"] +
            plan["5. Discretionary Spending Budget"] # Use the budgeted amount, not historical
        )

        projected_end_balance = self.checking_balance + self.monthly_income - total_outflows

        # Check for a buffer. a good rule of thumb is to keep at least $500.
        buffer = 500
        status = "🟢 Healthy"
        if projected_end_balance < 0:
            status = "🚨 OVERDRAFT RISK"
        elif projected_end_balance < buffer:
            status = "🟡 Low Buffer"
            
        return {
            "Start of Month Balance": self.checking_balance,
            "Projected Income": self.monthly_income,
            "Projected Outflows": total_outflows,
            "Projected End of Month Balance": projected_end_balance,
            "Buffer Status": status
        }
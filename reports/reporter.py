# reports/reporter.py
# generates a comprehensive, human-readable financial report from all analyzer outputs.

from datetime import datetime
from analyzers.spending import SpendingAnalyzer
from analyzers.subscriptions import SubscriptionDetector
from analyzers.anomalies import AnomalyDetector
from analyzers.locations import LocationAnalyzer
from analyzers.debt import DebtAnalyzer
from analyzers.subscription_manager import SubscriptionManager
from analyzers.recurring_purchases_manager import RecurringPurchasesManager
from analyzers.inventory_manager import InventoryManager
from analyzers.credit_card_tracker import CreditCardTracker
from analyzers.wants_manager import WantsManager
from analyzers.sinking_fund_manager import SinkingFundManager
from analyzers.cash_flow_analyzer import CashFlowAnalyzer
from budget.budgeter import Budgeter
from budget.debt_strategy import DebtStrategy


class Reporter:
    """
    assembles data from all analyzers into a single, cohesive text report.
    """

    def __init__(
        self,
        spending: SpendingAnalyzer,
        subscriptions: SubscriptionDetector,
        budgeter: Budgeter,
        anomalies: AnomalyDetector = None,
        locations: LocationAnalyzer = None,
        debt_analyzer: DebtAnalyzer = None,
        debt_strategy: DebtStrategy = None,
    ):
        self.spending = spending
        self.subscriptions = subscriptions
        self.budgeter = budgeter
        self.anomalies = anomalies
        self.locations = locations
        self.debt_analyzer = debt_analyzer
        self.debt_strategy = debt_strategy
        # these will be attached from main.py after initialization
        self.subscription_manager = None
        self.recurring_purchases_manager = None
        self.inventory_manager = None
        self.cc_tracker = None
        self.wants_manager = None
        self.sinking_fund_manager = None
        self.cash_flow_analyzer = None

    def _render_bar(self, value, max_value, length=25):
        """helper to render a simple text-based progress bar for goals."""
        if max_value <= 0 or value < 0:
            return '─' * length
        fill_len = int(length * (value / max_value))
        return '█' * fill_len + '─' * (length - fill_len)

    def generate_financial_dashboard(self) -> str:
        """generates a visual text-based dashboard of overall financial health."""
        output = []
        output.append("=" * 70)
        output.append("FINANCIAL DASHBOARD")
        output.append("=" * 70)

        # assets section
        checking_balance = self.cash_flow_analyzer.checking_balance
        sinking_fund_total = self.sinking_fund_manager.get_total_saved()
        total_assets = checking_balance + sinking_fund_total
        output.append("\n--- ✅ ASSETS (Liquid) ---")
        output.append(f"  {'Checking Account:':<30} ${checking_balance:12,.2f}")
        output.append(f"  {'Sinking Funds Total:':<30} ${sinking_fund_total:12,.2f}")
        output.append(f"  {'TOTAL LIQUID ASSETS:':<30} ${total_assets:12,.2f}")

        # sinking funds breakdown
        for fund in self.sinking_fund_manager.funds:
            bar = self._render_bar(fund.current_balance, fund.goal_amount)
            output.append(f"    - {fund.name:<25} ${fund.current_balance:8,.2f} / ${fund.goal_amount:8,.2f} [{bar}] {fund.percentage_complete:.1f}%")

        # liabilities section
        cc_debt = sum(acc.current_balance for acc in self.debt_analyzer.accounts if acc.account_type == 'credit_card')
        other_debt = self.debt_analyzer.total_debt() - cc_debt
        total_liabilities = self.debt_analyzer.total_debt()
        output.append("\n--- 🚨 LIABILITIES ---")
        output.append(f"  {'Credit Card Debt:':<30} ${cc_debt:12,.2f}")
        output.append(f"  {'Other Loans:':<30} ${other_debt:12,.2f}")
        output.append(f"  {'TOTAL LIABILITIES:':<30} ${total_liabilities:12,.2f}")

        # net worth calculation
        net_worth = total_assets - total_liabilities
        output.append("\n--- NET WORTH (Liquid Estimate) ---")
        output.append(f"  {'Your Estimated Net Worth:':<30} ${net_worth:12,.2f}")
        
        return "\n".join(output)

    def summary_text(self) -> str:
        """generates the complete, multi-section financial report."""
        output = []

        # --- section 1: top-level dashboard & forward-looking plans ---
        if self.cash_flow_analyzer and self.sinking_fund_manager:
            output.append(self.generate_financial_dashboard())

            projection = self.cash_flow_analyzer.project_checking_account_balance()
            output.append("\n" + "=" * 70)
            output.append("CASH FLOW PROJECTION (THIS MONTH)")
            output.append("=" * 70)
            output.append(f"  {'Status:':<35} {projection['Buffer Status']}")
            output.append(f"  {'Start Balance:':<35} ${projection['Start of Month Balance']:>12,.2f}")
            output.append(f"  {'Projected Income:':<35} ${projection['Projected Income']:>12,.2f}")
            output.append(f"  {'Projected Outflows (Budgeted):':<35} ${projection['Projected Outflows']:>12,.2f}")
            output.append(f"  {'PROJECTED END BALANCE:':<35} ${projection['Projected End of Month Balance']:>12,.2f}")

            plan = self.cash_flow_analyzer.generate_allocation_plan()
            output.append("\n" + "=" * 70)
            output.append("MONTHLY ALLOCATION PLAN (Pay Yourself First)")
            output.append("=" * 70)
            for key, value in plan.items():
                output.append(f"  {key:<35} ${value:>12,.2f}")

        # --- section 2: alerts and reminders ---
        if self.cc_tracker:
            schedule = self.cc_tracker.payment_schedule()
            output.append("\n" + "=" * 70)
            output.append("ALERTS & REMINDERS")
            output.append("=" * 70)
            output.append("\n--- Credit Card Payment Schedule ---")
            output.append(f"  Total Unpaid Charges Tracked: ${schedule['grand_total']:,.2f}")
            if schedule.get('next_check_15th', {}).get('charges'):
                output.append(f"  - Due by 15th: ${schedule['next_check_15th']['total']:,.2f} ({schedule['next_check_15th']['count']} charges)")
            if schedule.get('next_check_eom', {}).get('charges'):
                output.append(f"  - Due by End of Month: ${schedule['next_check_eom']['total']:,.2f} ({schedule['next_check_eom']['count']} charges)")

        if self.recurring_purchases_manager:
            overdue = self.recurring_purchases_manager.get_overdue()
            if overdue:
                output.append(f"\n--- ⚠️ Overdue Recurring Purchases ({len(overdue)}) ---")
                for purchase in overdue[:3]:
                    output.append(f"  - {purchase.name} (${purchase.amount:,.2f}) was expected on {purchase.next_expected.date()}")

        if self.inventory_manager:
            expired = self.inventory_manager.get_expired()
            if expired:
                output.append(f"\n--- 🚨 Expired Inventory ({len(expired)}) ---")
                for item in expired[:3]:
                    output.append(f"  - {item.name} expired on {item.expiration_date.date()}")
            expiring_soon = self.inventory_manager.get_expiring_soon()
            if expiring_soon:
                output.append(f"\n--- ⏰ Inventory Expiring Soon ({len(expiring_soon)}) ---")
                for item in expiring_soon[:3]:
                    output.append(f"  - {item.name} expires in {item.days_until_expiration} days")

        # --- section 3: behavioral finance & goals ---
        if self.cc_tracker:
            health = self.cc_tracker.get_usage_health()
            output.append("\n" + "=" * 70)
            output.append("BEHAVIORAL FINANCE & GOALS")
            output.append("=" * 70)
            output.append("\n--- Credit Card Usage Health (This Month) ---")
            output.append(f"  {'Status:':<30} {health['Usage Status']}")
            output.append(f"  {'Total New Charges:':<30} {health['New Charges This Month']} charges")
            output.append(f"  {'Total Spent on Cards:':<30} ${health['Total Spent on Card This Month']:,.2f}")
            output.append(f"  {'Recommendation:':<30} {health['Recommendation']}")

            # show detailed list of new charges
            if health.get('Charges List'):
                output.append(f"\n  Recent charges this month:")
                for charge in health['Charges List']:
                    output.append(
                        f"    {charge.date.strftime('%m/%d')} | "
                        f"{charge.card_name:<20} | "
                        f"{charge.merchant:<30} | "
                        f"${charge.amount:>8,.2f}"
                    )

        if self.wants_manager:
            stats = self.wants_manager.cooling_off_stats()
            output.append("\n--- Wants 'Cooling-Off' Tracker ---")
            output.append(f"  You have saved ${stats['savings_from_cooling']:,.2f} by canceling {stats['cancellation_rate']:.0f}% of wants.")
            ready = self.wants_manager.get_ready_wants()
            if ready:
                output.append(f"  - You have {len(ready)} item(s) ready for purchase after 3 check-ins.")

        # --- section 4: debt deep dive ---
        if self.debt_analyzer:
            output.append("\n" + "=" * 70)
            output.append("DEBT ANALYSIS")
            output.append("=" * 70)
            output.append(f"  {'Total Debt:':<25} ${self.debt_analyzer.total_debt():,.2f}")
            output.append(f"  {'Avg. Interest Rate:':<25} {self.debt_analyzer.avg_interest_rate() * 100:.2f}%")
            output.append(f"  {'Est. Monthly Interest:':<25} ${self.debt_analyzer.total_monthly_interest():,.2f}")
            utilization = self.debt_analyzer.utilization_impact()
            if utilization:
                output.append(f"  {'Credit Utilization:':<25} {utilization['overall_utilization']:.1f}% ({utilization['credit_score_impact']})")

        # --- section 5: historical spending review ---
        min_date, max_date = self.spending.get_date_range()
        output.append("\n" + "=" * 70)
        output.append(f"HISTORICAL SPENDING REVIEW ({min_date.strftime('%b %Y')} - {max_date.strftime('%b %Y')})")
        output.append("=" * 70)
        output.append("\n--- Spending by Category ---")
        for cat, amount in list(self.spending.by_category().items())[:7]:
            pct = (amount / self.spending.total_spent()) * 100
            output.append(f"  {cat:.<40} ${amount:>10,.2f} ({pct:>5.1f}%)")
        
        output.append("\n--- Top Merchants ---")
        for merchant, amount in self.spending.top_merchants(5):
            output.append(f"  {merchant:.<40} ${amount:>10,.2f}")

        # --- final save ---
        output.append("\n" + "=" * 70)
        return "\n".join(output)

    def save_report(self, filepath: str):
        """saves the generated report to a text file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.summary_text())
        print(f"✅ report saved to {filepath}")
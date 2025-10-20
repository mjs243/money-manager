# reports/reporter.py
# generate readable budget reports

from analyzers.spending import SpendingAnalyzer
from analyzers.subscriptions import SubscriptionDetector
from analyzers.anomalies import AnomalyDetector
from analyzers.locations import LocationAnalyzer
from analyzers.debt import DebtAnalyzer
from budget.budgeter import Budgeter
from budget.debt_strategy import DebtStrategy
from datetime import datetime

class Reporter:
    """generate text + data reports"""

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

    def summary_text(self) -> str:
        """generate readable summary"""
        min_date, max_date = self.spending.get_date_range()
        by_cat = self.spending.by_category()
        by_month = self.spending.by_month()

        output = []
        output.append("=" * 70)
        output.append("SPENDING ANALYSIS REPORT")
        output.append("=" * 70)
        output.append(f"\nanalysis period: {min_date.date()} to {max_date.date()}")
        output.append(f"total transactions analyzed: {len(self.spending.transactions)}")

        # overview
        output.append(f"\n--- overview ---")
        output.append(f"total spent: ${self.spending.total_spent():,.2f}")
        output.append(f"avg monthly: ${self.spending.average_monthly():,.2f}")
        output.append(f"months analyzed: {len(by_month)}")

        # by category
        output.append(f"\n--- spending by category ---")
        for cat, amount in by_cat.items():
            pct = (amount / self.spending.total_spent()) * 100
            output.append(f"  {cat:.<40} ${amount:>10,.2f} ({pct:>5.1f}%)")

        # top merchants
        output.append(f"\n--- top merchants ---")
        for merchant, amount in self.spending.top_merchants(10):
            output.append(f"  {merchant:.<40} ${amount:>10,.2f}")

        # recurring purchases
        if hasattr(self, 'recurring_purchases_manager') and self.recurring_purchases_manager:
            output.append(f"\n--- recurring purchases ---")
            manager = self.recurring_purchases_manager
            output.append(f"active purchases: {len(manager.get_active_purchases())}")
            output.append(f"monthly cost: ${manager.total_monthly_cost():,.2f}")

            due_soon = manager.get_due_soon()
            overdue = manager.get_overdue()

            if overdue:
                output.append(f"\n--- ⚠️  overdue purchases ({len(overdue)}) ---")
                for purchase in overdue[:5]:
                    output.append(
                        f"  {purchase.name:.<35} "
                        f"${purchase.amount:>8,.2f} "
                        f"({purchase.frequency.value})"
                    )

            if due_soon:
                output.append(f"\n--- 📅 due soon ({len(due_soon)}) ---")
                for purchase in due_soon[:5]:
                    output.append(
                        f"  {purchase.name:.<35} "
                        f"${purchase.amount:>8,.2f} "
                        f"in {purchase.days_until_next} days"
                    )

        # subscriptions
        if self.subscriptions:
            output.append(f"\n--- recurring charges (detected by pattern) ---")

            recurring = self.subscriptions.find_recurring()

            if recurring:
                for merchant, data in list(recurring.items())[:15]:
                    output.append(
                        f"  {merchant:.<35} "
                        f"${data['amount']:>8,.2f} "
                        f"every {data['interval_days']:.0f} days "
                        f"({data['interval_type']}) "
                        f"[confidence: {data['confidence']:.0f}%]"
                    )

                # summary
                output.append(f"\n--- subscription summary ---")
                health = self.subscriptions.subscription_health_check()
                output.append(f"  active subscriptions: {health['active_subscriptions']}")
                output.append(f"  monthly total: ${health['monthly_total']:,.2f}")
                output.append(f"  annual total: ${health['annual_total']:,.2f}")

                # possibly cancelled
                gaps = self.subscriptions.analyze_gaps()
                if gaps:
                    output.append(f"\n--- ⚠️  possibly cancelled subscriptions ---")
                    output.append(f"  (no charge in {gaps[0]['days_since']} days)")
                    for gap in gaps[:5]:
                        output.append(
                            f"    {gap['merchant']:.<30} "
                            f"was ~${gap['avg_monthly_impact']:,.2f}/month"
                        )

                # potential duplicates
                dupes = self.subscriptions.potential_duplicates_in_recurring()
                if dupes:
                    output.append(f"\n--- ⚠️  potential duplicate subscriptions ---")
                    for dupe in dupes:
                        output.append(
                            f"    {dupe['merchant_1']:.<25} + "
                            f"{dupe['merchant_2']:<25}"
                        )
                        output.append(
                            f"    → monthly cost: "
                            f"${dupe['total_monthly_duplicate']:,.2f}"
                        )

            else:
                output.append("  (no recurring patterns detected)")

            monthly_recurring = self.subscriptions.estimated_monthly_recurring()
            output.append(f"\nestimated monthly recurring: ${monthly_recurring:,.2f}")

        # budget vs targets
        output.append(f"\n--- budget vs targets (monthly avg) ---")
        vs_targets = self.budgeter.vs_targets()
        for cat in sorted(vs_targets.keys()):
            data = vs_targets[cat]
            status = "✓" if data["over_under"] == "under" else "✗"
            output.append(
                f"  {status} {cat:.<35} "
                f"${data['avg_monthly']:>8,.2f} / "
                f"${data['target']:>8,.2f}"
            )

        # locations
        if self.locations:
            output.append(f"\n--- frequent locations ---")
            freq_locs = self.locations.frequent_locations(8)
            for location, count in freq_locs:
                output.append(f"  {location:.<40} x{count}")

            spending_by_loc = self.locations.spending_by_location()
            output.append(f"\n--- spending by location ---")
            for location, amount in list(spending_by_loc.items())[:8]:
                output.append(f"  {location:.<40} ${amount:>10,.2f}")

            # commute analysis
            commute = self.locations.commute_analysis()
            if commute["transactions"] > 0:
                output.append(f"\n--- commute spending ---")
                output.append(f"  total: ${commute['total']:,.2f}")
                output.append(f"  transactions: {commute['transactions']}")
                output.append(f"  monthly avg: ${commute['monthly_avg']:,.2f}")
                output.append(f"  primary vendor: {commute['top_merchant']}")

            # merchant frequency
            output.append(f"\n--- most visited merchants ---")
            freq_merchants = self.locations.merchant_frequency(10)
            for merchant, count in freq_merchants:
                output.append(f"  {merchant:.<40} x{count} visits")

        # anomalies
        if self.anomalies:
            # large purchases
            large = self.anomalies.large_purchases(percentile=90)
            if large:
                output.append(f"\n--- large purchases (top 90th percentile) ---")
                for purchase in large[:10]:
                    output.append(
                        f"  {purchase['date'].date()} | "
                        f"{purchase['merchant']:.<25} | "
                        f"${purchase['amount']:>10,.2f}"
                    )

            # statistical outliers
            outliers = self.anomalies.statistical_outliers(std_dev_threshold=2.0)
            if outliers:
                output.append(f"\n--- statistical outliers (2σ threshold) ---")
                for outlier in outliers[:8]:
                    output.append(
                        f"  {outlier['date'].date()} | "
                        f"{outlier['merchant']:.<25} | "
                        f"${outlier['amount']:>10,.2f} "
                        f"(z-score: {outlier['z_score']:.2f})"
                    )

            # unusual by category
            unusual = self.anomalies.unusual_categories()
            if unusual:
                output.append(f"\n--- unusual spending by category ---")
                for cat, txns in unusual.items():
                    output.append(f"  {cat}:")
                    for txn in txns[:3]:
                        output.append(
                            f"    {txn['date'].date()} | "
                            f"{txn['merchant']:.<20} | "
                            f"${txn['amount']:>10,.2f}"
                        )

            # duplicates
            dupes = self.anomalies.duplicate_transactions()
            if dupes:
                output.append(f"\n--- potential duplicate transactions ---")
                for pair in dupes[:5]:
                    output.append(
                        f"  {pair[0]['date'].date()} "
                        f"{pair[0]['merchant']:.<25} "
                        f"${pair[0]['amount']:>10,.2f}"
                    )
                    output.append(
                        f"  {pair[1]['date'].date()} "
                        f"{pair[1]['merchant']:.<25} "
                        f"${pair[1]['amount']:>10,.2f}"
                    )
                    output.append("")

        # inventory alerts
        if hasattr(self, 'inventory_manager') and self.inventory_manager:
            output.append(f"\n--- inventory alerts ---")
            expired = self.inventory_manager.get_expired()
            expiring_soon = self.inventory_manager.get_expiring_soon()

            if expired:
                output.append(f"⚠️  {len(expired)} expired items:")
                for item in expired[:5]:
                    output.append(f"  • {item.name} (expired)")

            if expiring_soon:
                output.append(f"⏰ {len(expiring_soon)} expiring soon:")
                for item in expiring_soon[:5]:
                    output.append(
                        f"  • {item.name} "
                        f"({item.days_until_expiration} days)"
                    )

        # credit card payment schedule
        if hasattr(self, 'cc_tracker') and self.cc_tracker:
            schedule = self.cc_tracker.payment_schedule()

            output.append(f"\n--- credit card payment schedule ---")
            output.append(f"total unpaid: ${schedule['grand_total']:,.2f}")

            charges_15th = schedule.get('next_check_15th', {})
            charges_eom = schedule.get('next_check_eom', {})

            if charges_15th.get('charges'):
                output.append(
                    f"\ndue by 15th: "
                    f"${charges_15th['total']:,.2f} ({charges_15th['count']} charges)"
                )

            if charges_eom.get('charges'):
                output.append(
                    f"due by EOM: "
                    f"${charges_eom['total']:,.2f} ({charges_eom['count']} charges)"
                )

        # debt analysis
        if self.debt_analyzer:
            output.append(f"\n--- debt summary ---")
            output.append(f"total debt: ${self.debt_analyzer.total_debt():,.2f}")
            output.append(f"monthly interest cost: ${self.debt_analyzer.total_monthly_interest():,.2f}")
            output.append(f"annual interest cost: ${self.debt_analyzer.total_annual_interest():,.2f}")
            output.append(f"avg interest rate: {self.debt_analyzer.avg_interest_rate()*100:.2f}%")

            # utilization
            utilization = self.debt_analyzer.utilization_impact()
            if utilization:
                output.append(f"\n--- credit utilization ---")
                output.append(f"overall: {utilization['overall_utilization']:.1f}%")
                for acc in utilization['accounts']:
                    output.append(
                        f"  {acc['status']} {acc['name']:.<35} "
                        f"{acc['utilization']:.1f}%"
                    )
                output.append(f"\nimpact: {utilization['credit_score_impact']}")
                output.append(f"action: {utilization['recommendation']}")

            # payoff strategy
            output.append(f"\n--- debt payoff strategy (avalanche) ---")
            avalanche = self.debt_analyzer.avalanche_strategy(monthly_payment=800)
            timeline = self.debt_analyzer.payoff_timeline(800, strategy="avalanche")

            for item in avalanche:
                output.append(
                    f"  priority {item['priority']}: {item['account']:.<25} "
                    f"${item['current_balance']:>10,.2f} @ "
                    f"{item['interest_rate']:>5.1f}%"
                )
                output.append(
                    f"    → ${item['monthly_payment']:>8,.2f}/month "
                    f"→ {item['months_to_payoff']:.0f} months"
                )

            output.append(f"\ndebt-free in: {timeline['months_to_debt_free']:.0f} months "
                         f"({timeline['years_to_debt_free']:.1f} years)")
            output.append(f"projected interest: ${timeline['projected_total_interest']:,.2f}")

            # high utilization
            high_util = self.debt_analyzer.high_utilization_accounts()
            if high_util:
                output.append(f"\n--- ⚠️  high utilization cards ---")
                for acc in high_util:
                    output.append(
                        f"  {acc['name']:.<30} "
                        f"{acc['utilization']:.1f}% full"
                    )

            # balance transfer analysis
            bt_analysis = self.debt_analyzer.balance_transfer_analysis()
            if bt_analysis['candidates']:
                output.append(f"\n--- balance transfer opportunities ---")
                output.append(f"potential savings: ${bt_analysis['total_potential_savings']:,.2f}")
                for cand in bt_analysis['candidates']:
                    output.append(
                        f"  {cand['account']:.<30} "
                        f"save ~${cand['potential_savings']:,.2f}"
                    )

        # house fund projection
        output.append(f"\n--- house down payment goal ---")
        projection = self.budgeter.house_fund_projection(500)
        output.append(f"  current savings: ${projection['current_savings']:,.2f}")
        output.append(f"  target amount: ${projection['goal_amount']:,.2f}")
        output.append(f"  gap: ${projection['gap']:,.2f}")
        output.append(
            f"  @ ${projection['monthly_contribution']:,.2f}/month: "
            f"{projection['months_to_goal']:.0f} months "
            f"({projection['years_to_goal']:.1f} years)"
        )

        output.append("\n" + "=" * 70)
        return "\n".join(output)

    def save_report(self, filepath: str):
        """save report to file"""
        with open(filepath, 'w') as f:
            f.write(self.summary_text())
        print(f"✅ report saved to {filepath}")
# main.py
# run the budget analysis pipeline

import sys
from pathlib import Path

# add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from parsers.csv_parser import CSVParser
from analyzers.spending import SpendingAnalyzer
from analyzers.subscriptions import SubscriptionDetector
from analyzers.subscription_manager import SubscriptionManager
from analyzers.anomalies import AnomalyDetector
from analyzers.locations import LocationAnalyzer
from analyzers.debt import DebtAnalyzer
from analyzers.recurring_purchases_manager import RecurringPurchasesManager
from analyzers.inventory_manager import InventoryManager
from analyzers.credit_card_tracker import CreditCardTracker
from analyzers.plaid_syncer import PlaidSyncer
from budget.budgeter import Budgeter
from budget.debt_strategy import DebtStrategy
from reports.reporter import Reporter
from models.debt import DebtAccount

def main():
    """main analysis pipeline"""
    print("\n🏠 budget analyzer\n")

    # sync from plaid (optional)
    print("🔄 checking plaid sync...")
    try:
        syncer = PlaidSyncer()
        syncer.sync_all_to_csv("data/transactions.csv", days=90)
    except Exception as e:
        print(f"⚠️  plaid sync skipped: {e}")
        print("   continuing with existing data...\n")

    # load transactions
    parser = CSVParser("data/transactions.csv")
    transactions = parser.load()

    if not transactions:
        print("❌ no transactions found. check your csv file.")
        return

    # analyze spending
    print("\n📊 analyzing spending...")
    spending_analyzer = SpendingAnalyzer(transactions)
    print(f"   total spent: ${spending_analyzer.total_spent():,.2f}")
    print(f"   avg monthly: ${spending_analyzer.average_monthly():,.2f}")

    # load subscription manager
    print("\n📋 loading subscription manager...")
    subscription_manager = SubscriptionManager("data/subscriptions.json")

    # detect subscriptions
    print("\n🔄 detecting subscriptions (pattern-based)...")
    subscription_detector = SubscriptionDetector(transactions)
    detected_recurring = subscription_detector.find_recurring()
    print(f"   found {len(detected_recurring)} detected recurring charges")

    health = subscription_detector.subscription_health_check()
    print(f"   monthly recurring: ${subscription_manager.total_monthly_cost(detected_recurring):,.2f}")

    if health['possibly_cancelled'] > 0:
        print(f"   ⚠️  {health['possibly_cancelled']} possibly cancelled")

    if health['potential_duplicates'] > 0:
        print(f"   ⚠️  {health['potential_duplicates']} potential duplicates")

    # detect anomalies
    print("\n🚨 detecting anomalies...")
    anomaly_detector = AnomalyDetector(transactions)
    large = anomaly_detector.large_purchases()
    outliers = anomaly_detector.statistical_outliers()
    dupes = anomaly_detector.duplicate_transactions()
    print(f"   found {len(large)} large purchases")
    print(f"   found {len(outliers)} statistical outliers")
    print(f"   found {len(dupes)} potential duplicates")

    # analyze locations
    print("\n📍 analyzing locations...")
    location_analyzer = LocationAnalyzer(transactions)
    freq_locs = location_analyzer.frequent_locations()
    freq_merchants = location_analyzer.merchant_frequency()
    commute = location_analyzer.commute_analysis()
    print(f"   found {len(freq_locs)} frequent locations")
    print(f"   commute spending: ${commute['monthly_avg']:,.2f}/month")

    # load recurring purchases manager
    print("\n🔄 loading recurring purchases manager...")
    recurring_purchases_manager = RecurringPurchasesManager("data/recurring_purchases.json")
    due_soon = recurring_purchases_manager.get_due_soon()
    overdue = recurring_purchases_manager.get_overdue()
    if due_soon:
        print(f"   ⏰ {len(due_soon)} purchases due soon")
    if overdue:
        print(f"   ⚠️  {len(overdue)} purchases overdue")

    # load inventory manager
    print("\n📦 loading inventory manager...")
    inventory_manager = InventoryManager("data/inventory.json")
    expired = inventory_manager.get_expired()
    expiring_soon = inventory_manager.get_expiring_soon()
    if expired:
        print(f"   ⚠️  {len(expired)} expired items")
    if expiring_soon:
        print(f"   ⏰ {len(expiring_soon)} expiring soon")

    # load credit card tracker
    print("\n💳 loading credit card tracker...")
    cc_tracker = CreditCardTracker("data/credit_card_charges.json")

    # detect credit card transactions and track them
    credit_card_txns = [
        t for t in transactions
        if t.account_type == "Credit Card"
    ]

    new_charges = 0
    for txn in credit_card_txns:
        existing = [
            c for c in cc_tracker.charges
            if (c.merchant == txn.merchant and
                c.amount == txn.amount and
                c.date.date() == txn.date.date())
        ]
        if not existing:
            cc_tracker.add_charge_from_transaction(txn, "Chase Credit Card")
            new_charges += 1

    if new_charges > 0:
        print(f"   ✅ tracked {new_charges} new charges")

    unpaid = cc_tracker.detect_unpaid_charges()
    if unpaid:
        print(f"   ⚠️  {len(unpaid)} charges need payment")

    # define debt accounts manually
    debt_accounts = [
        DebtAccount(
            name="Chase Credit Card",
            account_type="credit_card",
            current_balance=0,  # update with actual balance
            credit_limit=5000,
            interest_rate=0.21,
            minimum_payment=25,
        ),
        DebtAccount(
            name="Student Loan (Dept Education)",
            account_type="student_loan",
            current_balance=0,  # update with actual balance
            interest_rate=0.05,
            minimum_payment=50,
        ),
        DebtAccount(
            name="Toyota Auto Loan",
            account_type="auto_loan",
            current_balance=0,  # update with actual balance
            interest_rate=0.045,
            minimum_payment=483.09,
        ),
    ]

    # analyze debt
    print("\n💳 analyzing debt...")
    debt_analyzer = DebtAnalyzer(debt_accounts)
    print(f"   total debt: ${debt_analyzer.total_debt():,.2f}")
    print(f"   monthly interest: ${debt_analyzer.total_monthly_interest():,.2f}")

    # debt strategy
    print("\n📊 calculating payoff strategies...")
    debt_strategy = DebtStrategy(debt_analyzer, spending_analyzer)
    budget_rec = debt_strategy.recommended_payoff_budget()
    print(f"   available for debt: ${budget_rec['available_for_debt']:,.2f}")

    # build budget
    print("\n💰 building budget...")
    budgeter = Budgeter(spending_analyzer)
    projection = budgeter.house_fund_projection(500)
    print(f"   months to down payment: {projection['months_to_goal']:.0f}")

    # generate report
    print("\n📝 generating report...")
    reporter = Reporter(
        spending_analyzer,
        subscription_detector,
        budgeter,
        anomaly_detector,
        location_analyzer,
        debt_analyzer,
        debt_strategy,
    )
    reporter.subscription_manager = subscription_manager
    reporter.recurring_purchases_manager = recurring_purchases_manager
    reporter.inventory_manager = inventory_manager
    reporter.cc_tracker = cc_tracker

    report_text = reporter.summary_text()
    print(report_text)

    # save report
    reporter.save_report("data/output/report.txt")

    print("\n✅ analysis complete!\n")

if __name__ == "__main__":
    main()
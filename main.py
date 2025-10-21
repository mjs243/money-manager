# main.py
# the central orchestrator for the budget analysis pipeline.

import sys
import os
from pathlib import Path

# fix encoding for Windows console
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# add project root to python's path to allow for clean module imports
sys.path.insert(0, str(Path(__file__).parent))

# --- data ingestion & models ---
from analyzers.ynab_syncer import YNABSyncer
from parsers.csv_parser import CSVParser
from models.debt import DebtAccount
from models.transaction import Transaction

# --- core analyzers ---
from analyzers.spending import SpendingAnalyzer
from analyzers.subscriptions import SubscriptionDetector
from analyzers.anomalies import AnomalyDetector
from analyzers.locations import LocationAnalyzer
from analyzers.debt import DebtAnalyzer

# --- managers for manual & proactive data ---
from analyzers.subscription_manager import SubscriptionManager
from analyzers.recurring_purchases_manager import RecurringPurchasesManager
from analyzers.inventory_manager import InventoryManager
from analyzers.credit_card_tracker import CreditCardTracker
from analyzers.wants_manager import WantsManager
from analyzers.sinking_fund_manager import SinkingFundManager

# --- forward-looking & strategic modules ---
from analyzers.cash_flow_analyzer import CashFlowAnalyzer
from budget.budgeter import Budgeter
from budget.debt_strategy import DebtStrategy

# --- output ---
from reports.reporter import Reporter


def main():
    """
    runs the full financial analysis pipeline from data sync to report generation.
    """
    print("\n🏠 budget analyzer\n")

    # step 1: sync latest transactions from ynab
    print("🔄 syncing from ynab...")
    try:
        ynab_syncer = YNABSyncer()
        ynab_syncer.sync_to_csv(days=90)  # sync last 90 days of transactions
    except Exception as e:
        print(f"⚠️  ynab sync failed: {e}")
        print("   continuing with existing local data...\n")

    # step 2: load transactions from the csv file into memory
    parser = CSVParser("data/transactions.csv")
    transactions = parser.load()

    if not transactions:
        print("❌ no transactions found. check your csv file or ynab sync setup.")
        return

    # step 3: initialize all analyzers and managers
    # note: these are user-configurable values. update them to match your financial situation.
    MONTHLY_INCOME = 4600.0  # estimate your total monthly take-home pay
    CHECKING_ACCOUNT_BALANCE = 2500.0  # your current checking balance

    print("\n📊 analyzing spending...")
    spending_analyzer = SpendingAnalyzer(transactions)
    print(f"   total spent (last 90d): ${spending_analyzer.total_spent():,.2f}")
    print(f"   avg monthly: ${spending_analyzer.average_monthly():,.2f}")

    print("\n📋 loading subscription manager...")
    subscription_manager = SubscriptionManager("data/subscriptions.json")
    subscription_detector = SubscriptionDetector(transactions)
    detected_recurring = subscription_detector.find_recurring()
    print(f"   found {len(detected_recurring)} auto-detected recurring charges.")

    print("\n🚨 detecting anomalies...")
    anomaly_detector = AnomalyDetector(transactions)

    print("\n📍 analyzing locations...")
    location_analyzer = LocationAnalyzer(transactions)

    print("\n🔄 loading recurring purchases manager...")
    recurring_purchases_manager = RecurringPurchasesManager("data/recurring_purchases.json")

    print("\n📦 loading inventory manager...")
    inventory_manager = InventoryManager("data/inventory.json")

    print("\n💳 loading credit card tracker...")
    cc_tracker = CreditCardTracker("data/credit_card_charges.json")
    credit_card_txns = [t for t in transactions if t.account_type.lower() == "credit card"]
    new_charges_tracked = 0
    for txn in credit_card_txns:
        if not any(c.date == txn.date and c.merchant == txn.merchant and c.amount == txn.amount for c in cc_tracker.charges):
            cc_tracker.add_charge_from_transaction(txn, txn.account_name)
            new_charges_tracked += 1
    if new_charges_tracked > 0:
        print(f"   tracked {new_charges_tracked} new credit card charges.")

    print("\n🛍️  loading wants manager...")
    wants_manager = WantsManager("data/wants.json")
    wants_manager.perform_check_ins() # auto-perform monthly check-ins

    print("\n💰 loading sinking funds...")
    sinking_fund_manager = SinkingFundManager("data/sinking_funds.json")

    # define your debt accounts here. update balances manually or automate with plaid balance sync in future.
    debt_accounts = [
        DebtAccount(name="Chase Credit Card", account_type="credit_card", current_balance=1250.55, credit_limit=5000, interest_rate=0.21, minimum_payment=40),
        DebtAccount(name="Student Loan", account_type="student_loan", current_balance=22000.00, interest_rate=0.05, minimum_payment=250),
        DebtAccount(name="Auto Loan", account_type="auto_loan", current_balance=8500.00, interest_rate=0.045, minimum_payment=483.09),
    ]
    debt_analyzer = DebtAnalyzer(debt_accounts)
    debt_strategy = DebtStrategy(debt_analyzer, spending_analyzer)

    # step 4: initialize the forward-looking strategic analyzers
    print("\n🧠 initializing financial command center...")
    cash_flow_analyzer = CashFlowAnalyzer(spending_analyzer, subscription_manager, recurring_purchases_manager, debt_analyzer, sinking_fund_manager, monthly_income=MONTHLY_INCOME, checking_balance=CHECKING_ACCOUNT_BALANCE)
    budgeter = Budgeter(spending_analyzer)

    # step 5: generate the comprehensive report
    print("\n📝 generating report...")
    reporter = Reporter(
        spending=spending_analyzer,
        subscriptions=subscription_detector,
        budgeter=budgeter,
        anomalies=anomaly_detector,
        locations=location_analyzer,
        debt_analyzer=debt_analyzer,
        debt_strategy=debt_strategy
    )
    # attach the managers and strategic analyzers to the reporter
    reporter.subscription_manager = subscription_manager
    reporter.recurring_purchases_manager = recurring_purchases_manager
    reporter.inventory_manager = inventory_manager
    reporter.cc_tracker = cc_tracker
    reporter.wants_manager = wants_manager
    reporter.sinking_fund_manager = sinking_fund_manager
    reporter.cash_flow_analyzer = cash_flow_analyzer

    report_text = reporter.summary_text()
    print(report_text)

    # step 6: save the report to a file
    reporter.save_report("data/output/report.txt")

    print("\n✅ analysis complete!\n")

if __name__ == "__main__":
    main()
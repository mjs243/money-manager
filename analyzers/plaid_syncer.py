# analyzers/plaid_syncer.py
# sync transactions from plaid

import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

# install: pip install plaid-client

from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.configuration import Configuration
from plaid.api_client import ApiClient

class PlaidSyncer:
    """sync transactions from linked plaid accounts"""

    def __init__(self):
        self.client_id = os.getenv('PLAID_CLIENT_ID')
        self.secret = os.getenv('PLAID_SECRET')
        self.environment = os.getenv('PLAID_ENVIRONMENT', 'development')

        if not self.client_id or not self.secret:
            print("❌ missing plaid credentials in .env")
            raise ValueError("Missing PLAID_CLIENT_ID or PLAID_SECRET")

        # setup client
        config = Configuration(
            host=f"https://{self.environment}.plaid.com",
            api_key={
                'clientId': self.client_id,
                'secret': self.secret,
            }
        )
        api_client = ApiClient(config)
        self.client = plaid_api.PlaidApi(api_client)

        # get all access tokens from .env
        self.access_tokens = self._load_access_tokens()

    def _load_access_tokens(self) -> dict:
        """load all plaid access tokens from .env"""
        tokens = {}
        env_vars = os.environ

        for key, value in env_vars.items():
            if key.startswith('PLAID_ACCESS_TOKEN_'):
                account_name = key.replace('PLAID_ACCESS_TOKEN_', '').replace('_', ' ')
                tokens[account_name] = value

        if not tokens:
            print("⚠️  no plaid access tokens found in .env")
            print("   run: python scripts/plaid_setup.py")

        return tokens

    def get_accounts(self, access_token: str) -> list:
        """get all accounts for an access token"""
        try:
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)
            return response['accounts']
        except Exception as e:
            print(f"❌ error getting accounts: {e}")
            return []

    def fetch_transactions(
        self,
        access_token: str,
        days: int = 90,
        account_id: str = None
    ) -> list:
        """fetch transactions for an account"""
        try:
            start_date = (datetime.now() - timedelta(days=days)).date()
            end_date = datetime.now().date()

            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
                options={
                    "account_ids": [account_id] if account_id else None,
                }
            )

            response = self.client.transactions_get(request)
            return response['transactions']

        except Exception as e:
            print(f"❌ error fetching transactions: {e}")
            return []

    def sync_all_to_csv(
        self,
        output_path: str = "data/transactions.csv",
        days: int = 90
    ):
        """sync all linked accounts to csv"""
        print(f"\n🔄 syncing plaid transactions ({days} days)...")

        all_transactions = []

        for account_name, access_token in self.access_tokens.items():
            print(f"\n  📲 {account_name}...")

            # get accounts
            accounts = self.get_accounts(access_token)
            if not accounts:
                print(f"     no accounts found")
                continue

            # fetch transactions for each account
            for account in accounts:
                account_id = account['account_id']
                account_name_full = account['name']
                account_type = account['type']
                subtype = account.get('subtype', '')

                txns = self.fetch_transactions(
                    access_token,
                    days=days,
                    account_id=account_id
                )

                print(f"     • {account_name_full}: {len(txns)} transactions")

                for txn in txns:
                    all_transactions.append({
                        "Date": txn['date'],
                        "Original Date": txn['date'],
                        "Account Type": account_type,
                        "Account Name": account_name_full,
                        "Account Number": account_id[-4:],  # last 4 digits
                        "Institution Name": account_name,
                        "Name": txn.get('merchant_name', txn['name']),
                        "Custom Name": "",
                        "Amount": abs(txn.get('amount', 0)),
                        "Description": txn['name'],
                        "Category": self._map_plaid_category(txn),
                        "Note": "",
                        "Ignored From": "",
                        "Tax Deductible": "",
                    })

        if not all_transactions:
            print("❌ no transactions found")
            return

        # create dataframe
        df = pd.DataFrame(all_transactions)

        # sort by date
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date', ascending=False)

        # merge with existing
        try:
            existing_df = pd.read_csv(output_path)
            existing_df['Date'] = pd.to_datetime(existing_df['Date'])

            # combine and deduplicate
            combined = pd.concat([df, existing_df], ignore_index=True)
            combined = combined.drop_duplicates(
                subset=['Date', 'Name', 'Amount'],
                keep='first'
            )
            combined = combined.sort_values('Date', ascending=False)

        except FileNotFoundError:
            combined = df

        # save
        combined.to_csv(output_path, index=False)
        print(f"\n✅ synced {len(df)} new transactions")
        print(f"   total in file: {len(combined)}")
        print(f"   saved to: {output_path}")

    @staticmethod
    def _map_plaid_category(transaction: dict) -> str:
        """map plaid categories to our categories"""
        plaid_category = transaction.get('personal_finance_category', {})
        primary = plaid_category.get('primary', 'Uncategorized')

        # mapping
        category_map = {
            'TRANSPORTATION': 'Auto & Transport',
            'TRAVEL': 'Auto & Transport',
            'FOOD_AND_DRINK': 'Dining & Drinks',
            'FOOD_AND_DRINK_GROCERIES': 'Groceries',
            'FOOD_AND_DRINK_RESTAURANTS': 'Dining & Drinks',
            'SHOPPING': 'Shopping',
            'SHOPPING_ELECTRONICS': 'Software & Tech',
            'UTILITIES': 'Bills & Utilities',
            'MEDICAL': 'Shopping',
            'ENTERTAINMENT': 'Entertainment & Rec.',
            'FINANCIAL': 'Fees',
            'PERSONAL': 'Shopping',
        }

        return category_map.get(primary, primary)

    def get_balance_summary(self) -> dict:
        """get summary of all account balances"""
        summary = {}

        for account_name, access_token in self.access_tokens.items():
            accounts = self.get_accounts(access_token)

            for account in accounts:
                summary[account['name']] = {
                    "type": account['type'],
                    "balance": account['balances']['current'],
                    "available": account['balances'].get('available', 0),
                    "institution": account_name,
                }

        return summary

    def balance_report(self) -> str:
        """generate balance summary report"""
        summary = self.get_balance_summary()

        output = []
        output.append("=" * 70)
        output.append("ACCOUNT BALANCES (FROM PLAID)")
        output.append("=" * 70)

        total_checking = 0
        total_savings = 0
        total_credit = 0

        for account_name, data in summary.items():
            account_type = data['type']
            balance = data['balance']
            institution = data['institution']

            output.append(f"\n{institution}")
            output.append(f"  {account_name:.<40} ${balance:>10,.2f}")

            if account_type == 'depository':
                total_checking += balance
            elif account_type == 'savings':
                total_savings += balance
            elif account_type == 'credit':
                total_credit += balance

        output.append(f"\n--- totals ---")
        output.append(f"checking/depository: ${total_checking:,.2f}")
        output.append(f"savings: ${total_savings:,.2f}")
        output.append(f"credit card debt: ${total_credit:,.2f}")
        output.append(f"net worth: ${total_checking + total_savings - total_credit:,.2f}")

        output.append("\n" + "=" * 70)
        return "\n".join(output)
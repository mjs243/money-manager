# analyzers/ynab_syncer.py
# syncs all transactions from a specified ynab budget.

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

class YNABSyncer:
    """fetches and syncs transactions from the ynab api."""

    def __init__(self):
        """initializes the syncer by loading credentials from the environment."""
        load_dotenv(dotenv_path='config/.env')
        self.api_token = os.getenv('YNAB_API_TOKEN')
        self.budget_id = os.getenv('YNAB_BUDGET_ID')

        if not self.api_token or not self.budget_id:
            raise ValueError("ynab_api_token and ynab_budget_id must be set in config/.env")

        self.base_url = "https://api.youneedabudget.com/v1"
        self.headers = {'authorization': f'bearer {self.api_token}'}

    def fetch_transactions(self, days: int = 90) -> list:
        """
        fetches transactions from the last n days from the specified ynab budget.
        """
        # ynab needs the date in iso format (e.g., '2025-10-20')
        since_date = (datetime.now() - timedelta(days=days)).strftime('%y-%m-%d')
        url = f"{self.base_url}/budgets/{self.budget_id}/transactions"
        params = {'since_date': since_date}

        print(f"-> fetching ynab transactions since {since_date}...")

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status() # will raise an error for 4xx/5xx responses
            return response.json().get('data', {}).get('transactions', [])
        except requests.exceptions.RequestException as e:
            print(f"❌ error fetching from ynab api: {e}")
            return []

    def sync_to_csv(self, output_path: str = "data/transactions.csv", days: int = 90):
        """
        fetches ynab transactions and merges them into the local csv,
        ensuring no duplicates are created.
        """
        transactions = self.fetch_transactions(days=days)

        if not transactions:
            print("-> no new transactions found from ynab.")
            return

        print(f"-> received {len(transactions)} transactions from ynab.")
        
        # transform the ynab data into our application's format
        transformed_rows = []
        for txn in transactions:
            # ynab amounts are in "milliunits". divide by 1000 to get the dollar amount.
            # we only care about outflows, which are negative in ynab.
            if txn['amount'] >= 0:
                continue # skip inflows/income for this simple sync

            transformed_rows.append({
                'date': txn['date'],
                'original date': txn['date'],
                'account type': 'Cash' if txn['account_name'] != 'Chase Credit Card' else 'Credit Card', # simple logic
                'account name': txn.get('account_name', 'Unknown'),
                'account number': txn.get('account_id', '')[-4:],
                'institution name': 'YNAB', # source is ynab
                'name': txn.get('payee_name', 'Unknown Payee'),
                'custom name': '',
                'amount': abs(txn['amount'] / 1000.0), # convert from milliunits and make positive
                'description': txn.get('memo', ''),
                'category': txn.get('category_name', 'Uncategorized'),
                'note': '',
                'ignored from': '',
                'tax deductible': '',
                'source': 'ynab',  # mark as YNAB source
            })

        if not transformed_rows:
            print("-> no new spending transactions to sync.")
            return

        new_df = pd.DataFrame(transformed_rows)

        # merge with existing csv, handling duplicates
        try:
            existing_df = pd.read_csv(output_path)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            
            # ensure date column is consistent for sorting and duplicate checking
            combined_df['Date'] = pd.to_datetime(combined_df['Date']).dt.strftime('%y-%m-%d')
            
            # drop duplicates based on key fields
            combined_df.drop_duplicates(
                subset=['Date', 'Name', 'Amount', 'Description'],
                keep='first',
                inplace=True
            )
            combined_df.sort_values(by='Date', ascending=False, inplace=True)

        except FileNotFoundError:
            # if the file doesn't exist, the new data is our only data
            print("-> transactions.csv not found. creating a new one.")
            combined_df = new_df

        combined_df.to_csv(output_path, index=False)
        print(f"✅ successfully synced and saved {len(new_df)} new transactions to '{output_path}'.")
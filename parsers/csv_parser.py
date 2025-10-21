import pandas as pd
from datetime import datetime
from models.transaction import Transaction
import config

class CSVParser:
    """parse bank/credit card csv exports"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.df = None
        self.transactions = []

    def load(self) -> list[Transaction]:
        """load and parse csv file"""
        print(f"📂 loading {self.filepath}...")

        # read csv
        self.df = pd.read_csv(self.filepath)

        # normalize column names (handle variations)
        self.df.columns = [col.strip().lower() for col in self.df.columns]

        print(f"   found {len(self.df)} raw records")

        # parse each row
        for _, row in self.df.iterrows():
            txn = self._parse_row(row)
            if txn:
                self.transactions.append(txn)

        print(f"   parsed {len(self.transactions)} valid transactions")
        return self.transactions

    def _parse_row(self, row) -> Transaction | None:
        """convert csv row to transaction object"""
        try:
            # extract fields (handle column name variations)
            date_str = row.get('date') or row.get('original date')
            amount = float(row.get('amount', 0))
            merchant = row.get('name', '')
            category = row.get('category', 'Uncategorized')
            description = row.get('description', '')
            account_type = row.get('account type', '')
            account_name = row.get('account name', '')
            institution = row.get('institution name', '')
            source = row.get('source', 'csv')  # default to 'csv' if not specified

            # skip if amount is 0
            if amount == 0:
                return None

            # skip excluded categories
            if category in config.exclude_categories:
                return None

            # skip paypal transfers (internal movement)
            if any(kw in description.upper() for kw in config.paypal_keywords):
                return None

            # parse date - try multiple formats
            date = None
            for fmt in ['%Y-%m-%d', '%d-%m-%y', '%m/%d/%Y', '%Y/%m/%d']:
                try:
                    date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue

            if not date:
                return None

            return Transaction(
                date=date,
                account_type=account_type,
                account_name=account_name,
                institution=institution,
                merchant=merchant,
                amount=amount,
                description=description,
                category=category,
                source=source,
            )

        except Exception as e:
            # silently skip malformed rows (uncomment below for debugging)
            # print(f"Error parsing row: {e}")
            return None
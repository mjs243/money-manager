import pandas as pd
from datetime import datetime
from models.transaction import Transaction
import config

class csvParser:
    """parse transaction csv exports"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.df = None
        self.transactions = []
        
    def load(self) -> list[Transaction]:
        """load and parse csv file"""
        print(f"📂 loading {self.filepath}...")
        
        # read csv
        self.df = pd.read_csv(self.filepath)
        
        # normalize column names
        self.df.columns = [col.strip().lower() for col in self.df.columns]
        
        print(f"   found {len(self.df)} raw records")
        
        for _, row in self.df.iterrows():
            txn = self._parse_row(row)
            if txn:
                self.transactions.append(txn)
                
        print(f"   parsed {len(self.transactions)} valid transactions")
        return self.transactions
    
    def _parse_row(self, row) -> Transaction | None:
        """parse csv row to transaction object"""
        try:
            # extract fields
            date_str = row.get()
            
# scripts/sync_plaid.py
# manually sync plaid data

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzers.plaid_syncer import PlaidSyncer

def main():
    print("\n🔄 plaid sync\n")

    try:
        syncer = PlaidSyncer()

        # sync
        syncer.sync_all_to_csv(days=90)

        # show balances
        print(syncer.balance_report())

    except Exception as e:
        print(f"❌ error: {e}")

if __name__ == "__main__":
    main()
# scripts/initialize_data_files.py
# this utility script creates and populates all necessary .json data files
# with sample data. it's useful for a fresh start or if your local
# data files were deleted or corrupted.

import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# define the path to the data directory relative to the script location
DATA_DIR = Path(__file__).parent.parent / "data"

def create_json_file(file_path: Path, data: list, overwrite: bool = False):
    """
    creates a json file from a list of dictionaries.
    will not overwrite an existing file unless the --overwrite flag is used.
    """
    if file_path.exists() and not overwrite:
        print(f"-> skipping '{file_path.name}', file already exists.")
        return

    try:
        # ensure the data directory exists
        DATA_DIR.mkdir(exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        status = "overwritten" if overwrite and file_path.exists() else "created"
        print(f"✅ successfully {status} '{file_path.name}'")
    except Exception as e:
        print(f"❌ failed to create '{file_path.name}': {e}")


def generate_sinking_funds_data():
    """generates sample data for sinking funds."""
    return [
        {
            "name": "🏡 House Down Payment",
            "goal_amount": 60000.0,
            "current_balance": 27000.0,
            "monthly_contribution": 500.0,
            "target_date": None,
            "created_date": (datetime.now() - timedelta(days=365)).isoformat()
        },
        {
            "name": "🚗 Car Repair Fund",
            "goal_amount": 2000.0,
            "current_balance": 850.0,
            "monthly_contribution": 100.0,
            "target_date": None,
            "created_date": (datetime.now() - timedelta(days=180)).isoformat()
        },
        {
            "name": "🌴 Vacation Fund",
            "goal_amount": 3000.0,
            "current_balance": 400.0,
            "monthly_contribution": 150.0,
            "target_date": None,
            "created_date": (datetime.now() - timedelta(days=90)).isoformat()
        }
    ]

def generate_subscriptions_data():
    """generates sample data for manually tracked subscriptions."""
    return [
        {
            "name": "Netflix Premium",
            "merchant": "Netflix, Inc.",
            "amount": 22.99,
            "category": "Entertainment & Rec.",
            "interval_days": 30,
            "start_date": (datetime.now() - timedelta(days=700)).isoformat(),
            "end_date": None,
            "notes": "Main streaming service.",
            "is_active": True
        },
        {
            "name": "Proton VPN",
            "merchant": "Paypal *proton",
            "amount": 59.88,
            "category": "Software & Tech",
            "interval_days": 365,
            "start_date": (datetime.now() - timedelta(days=400)).isoformat(),
            "end_date": None,
            "notes": "Annual privacy subscription.",
            "is_active": True
        },
        {
            "name": "Old Gym Membership",
            "merchant": "Planet Fitness",
            "amount": 10.00,
            "category": "Health & Fitness",
            "interval_days": 30,
            "start_date": (datetime.now() - timedelta(days=800)).isoformat(),
            "end_date": (datetime.now() - timedelta(days=100)).isoformat(),
            "notes": "Cancelled this a few months ago.",
            "is_active": False
        }
    ]

def generate_recurring_purchases_data():
    """generates sample data for recurring physical goods."""
    return [
        {
            "name": "Dog Food Delivery",
            "merchant": "Chewy.com",
            "amount": 75.50,
            "category": "Shopping",
            "frequency": "monthly",
            "interval_days": 30,
            "last_purchase": (datetime.now() - timedelta(days=15)).isoformat(),
            "next_expected": (datetime.now() + timedelta(days=15)).isoformat(),
            "notes": "Large bag of kibble.",
            "is_active": True,
            "purchase_history": [(datetime.now() - timedelta(days=15)).isoformat()]
        },
        {
            "name": "Furnace Air Filters",
            "merchant": "Amazon Subscribe & Save",
            "amount": 25.00,
            "category": "Shopping",
            "frequency": "quarterly",
            "interval_days": 90,
            "last_purchase": (datetime.now() - timedelta(days=80)).isoformat(),
            "next_expected": (datetime.now() + timedelta(days=10)).isoformat(),
            "notes": "Remember to change these on time.",
            "is_active": True,
            "purchase_history": [(datetime.now() - timedelta(days=80)).isoformat()]
        }
    ]

def generate_wants_data():
    """generates sample data demonstrating the wants cooling-off period."""
    return [
        {
            "name": "New Mechanical Keyboard",
            "price": 250.0,
            "category": "Electronics",
            "reason": "For better typing experience at home office.",
            "created": (datetime.now() - timedelta(days=40)).isoformat(),
            "status": "pending",
            "check_in_dates": [(datetime.now() - timedelta(days=10)).isoformat()],
            "purchased_date": None,
            "notes": "Currently has 1/3 check-ins."
        },
        {
            "name": "Fancy Standing Desk",
            "price": 800.0,
            "category": "Furniture",
            "reason": "Thought it would help with back pain.",
            "created": (datetime.now() - timedelta(days=70)).isoformat(),
            "status": "cancelled",
            "check_in_dates": [(datetime.now() - timedelta(days=40)).isoformat(), (datetime.now() - timedelta(days=10)).isoformat()],
            "purchased_date": None,
            "notes": "Decided it was too expensive after the second check-in."
        }
    ]

def generate_inventory_data():
    """generates sample data for inventory with expiration dates."""
    return [
        {
            "name": "Emergency Water Bottle Case",
            "category": "Emergency",
            "purchase_date": (datetime.now() - timedelta(days=300)).isoformat(),
            "expiration_date": (datetime.now() + timedelta(days=400)).isoformat(),
            "quantity": 1,
            "unit": "case",
            "location": "Basement Shelf",
            "status": "active",
            "notes": "Good for another year."
        },
        {
            "name": "First Aid Kit Supplies",
            "category": "Emergency",
            "purchase_date": (datetime.now() - timedelta(days=1000)).isoformat(),
            "expiration_date": (datetime.now() - timedelta(days=10)).isoformat(),
            "quantity": 1,
            "unit": "kit",
            "location": "Car Trunk",
            "status": "active",
            "notes": "This has expired and needs to be replaced!"
        }
    ]

def generate_credit_card_charges_data():
    """generates sample data for the credit card tracker."""
    return [
        {
            "date": (datetime.now() - timedelta(days=20)).isoformat(),
            "merchant": "Some Online Store",
            "amount": 112.50,
            "category": "Shopping",
            "card_name": "Chase Credit Card",
            "status": "pending",
            "payment_date": None,
            "notes": "This will be on the end-of-month payment plan."
        },
        {
            "date": (datetime.now() - timedelta(days=5)).isoformat(),
            "merchant": "Local Restaurant",
            "amount": 88.20,
            "category": "Dining & Drinks",
            "card_name": "Chase Credit Card",
            "status": "detected",
            "payment_date": None,
            "notes": "This will be on the next 15th payment plan."
        }
    ]

def main(overwrite: bool):
    """main function to generate all data files."""
    print("--- initializing data files ---")
    
    # define all the files and their data-generating functions
    files_to_create = {
        "sinking_funds.json": generate_sinking_funds_data,
        "subscriptions.json": generate_subscriptions_data,
        "recurring_purchases.json": generate_recurring_purchases_data,
        "wants.json": generate_wants_data,
        "inventory.json": generate_inventory_data,
        "credit_card_charges.json": generate_credit_card_charges_data,
    }
    
    for filename, generator_func in files_to_create.items():
        file_path = DATA_DIR / filename
        data = generator_func()
        create_json_file(file_path, data, overwrite)
        
    print("\n✅ data initialization complete.")
    print("you can now run `python main.py` without errors.")
    if not overwrite:
        print("use the --overwrite flag to replace existing files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create and populate sample JSON data files for the Budget Analyzer."
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="If set, this will overwrite existing data files with the sample data."
    )
    args = parser.parse_args()

    main(overwrite=args.overwrite)
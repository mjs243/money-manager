# config.py
# central config for budget analyzer

# categories to exclude from spending analysis
# (these are accounting movements, not actual spending)
exclude_categories = [
    "Internal Transfers",
    "Credit Card Payment",
    "Savings Transfer",
    "Investment",
    "Loan Payment",
    "Income",
]

# paypal movements to ignore
paypal_keywords = [
    "PAYPAL INSTANT TRANSFER",
    "PAYPAL *",
    "APPLE CASH SENT",
]

# budget targets (monthly)
budget_targets = {
    "Dining & Drinks": 200,
    "Groceries": 300,
    "Auto & Transport": 200,
    "Entertainment & Rec.": 100,
    "Shopping": 150,
    "Software & Tech": 100,
    "Bills & Utilities": 250,
}

# savings goals
savings_goals = {
    "down_payment": {
        "target": 50000,
        "current": 27000,
        "monthly_contribution": 500,
    },
    "emergency_fund": {
        "target": 10000,
        "current": 0,
        "monthly_contribution": 200,
    },
}

# house down payment estimate
house_down_payment = {
    "target_price": 300000,
    "down_payment_percent": 0.20,
    "target_amount": 60000,
    "current_savings": 27000,
    "gap": 33000,
}
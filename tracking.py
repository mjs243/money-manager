#!/usr/bin/env python3
"""
Debt Tracker v1.0 - Run after each paycheck
"""
import datetime

# USER CONFIG
INCOME_PER_PAYCHECK = 3293.93
SAVINGS_TARGET = 1500
DEBT_TARGET = 2500

def main():
    today = datetime.date.today()
    
    # Calculate monthly allocations
    needs = INCOME_PER_PAYCHECK * 0.47
    savings = SAVINGS_TARGET / 2
    wants = INCOME_PER_PAYCHECK - needs - savings
    
    print(f"\n=== PAYCHECK ALLOCATION ({today.strftime('%Y-%m-%d')} ===")
    print(f"Debt Attack: ${needs:.2f}")
    print(f"Savings Seed: ${savings:.2f}")
    print(f"Life Money: ${wants:.2f}")
    print("-"*40)
    print("ACTION: Transfer immediately to buckets!")

if __name__ == "__main__":
    main()
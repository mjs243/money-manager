# scripts/find_ynab_budget_id.py
# a simple helper script to find your ynab budget id.

import os
import requests
from dotenv import load_dotenv

# load api token from your .env file
load_dotenv(dotenv_path='config/.env')
YNAB_API_TOKEN = os.getenv('YNAB_API_TOKEN')

def find_budgets():
    """Fetches and lists all budgets associated with your ynab account."""
    if not YNAB_API_TOKEN:
        print("❌ error: ynab_api_token not found in config/.env")
        print("   please add your token and try again.")
        return

    headers = {'authorization': f'bearer {YNAB_API_TOKEN}'}
    url = 'https://api.youneedabudget.com/v1/budgets'

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # raises an http error for bad responses
        data = response.json().get('data', {}).get('budgets', [])

        if not data:
            print("no budgets found for this api token.")
            return

        print("\nfound your ynab budgets:")
        print("="*50)
        for budget in data:
            print(f"  budget name: {budget['name']}")
            print(f"  budget id:   {budget['id']}")
            print(f"  currency:    {budget['currency_format']['iso_code']}")
            print("-"*50)

        print("\ncopy the 'budget id' for your main budget and add it to your")
        print("config/.env file as 'ynab_budget_id'.")

    except requests.exceptions.RequestException as e:
        print(f"❌ an error occurred: {e}")
        if '401' in str(e):
            print("   (hint: a 401 error usually means your api token is incorrect.)")

if __name__ == "__main__":
    find_budgets()
import json
from datetime import datetime
from typing import List, Dict
from src.config import ACCOUNTS_TXT, ACCOUNTS_JSON

class AccountManager:
    @staticmethod
    def save_accounts(accounts: List[Dict[str, str]]):
        """Save accounts to both text and JSON files"""
        AccountManager._save_to_txt(accounts)
        AccountManager._save_to_json(accounts)
        AccountManager._print_accounts(accounts)

    @staticmethod
    def _save_to_txt(accounts: List[Dict[str, str]]):
        with open(ACCOUNTS_TXT, "a") as f:
            for account in accounts:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"Email: {account['email']}, Password: {account['password']}, (Created at {timestamp})\n")

    @staticmethod
    def _save_to_json(accounts: List[Dict[str, str]]):
        with open(ACCOUNTS_JSON, "w") as json_file:
            json.dump(accounts, json_file, indent=4)

    @staticmethod
    def _print_accounts(accounts: List[Dict[str, str]]):
        print("\nAll accounts have been created. Here are the accounts' details:\n")
        for account in accounts:
            print(f"Email: {account['email']}, Password: {account['password']}")
        print("\nThey have been saved to the accounts files txt and json.\nHave fun using ExitLag!")

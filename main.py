import asyncio
import warnings
from tqdm import TqdmExperimentalWarning
from tqdm.rich import tqdm
from DrissionPage import ChromiumPage, ChromiumOptions
from lib.bypass import CloudflareBypasser
from lib.lib import Main
from src.email_handler import EmailHandler
from src.account_creator import AccountCreator
from src.password_generator import PasswordGenerator
from src.account_manager import AccountManager
from src.config import MAX_ACCOUNTS, DEFAULT_ACCOUNTS, EXITLAG_REGISTER_URL

warnings.filterwarnings("ignore", category=TqdmExperimentalWarning)

async def get_execution_count() -> int:
    while True:
        execution_count = input(f"\nHow many accounts do you want to create?\nIf nothing is entered, the script will stick to the default value ({DEFAULT_ACCOUNTS})\nAmount: ")
        if execution_count == "":
            return DEFAULT_ACCOUNTS
        try:
            count = int(execution_count)
            if count > MAX_ACCOUNTS:
                print(f"Maximum allowed accounts is {MAX_ACCOUNTS}. Setting count to {MAX_ACCOUNTS}.")
                return MAX_ACCOUNTS
            return count
        except ValueError:
            print("Invalid number given. Please enter a valid number.")

async def main():
    main_library = Main()
    port = ChromiumOptions().auto_port()
    
    browsers = {"chrome": True}
    
    await main_library.getSettingsAndBlockIP()
    if browsers.get("chrome") is None:
        print("\nChrome is required for this tool. Please install it via:\nhttps://google.com/chrome")
        return

    execution_count = await get_execution_count()
    accounts = []
    bar = tqdm(total=execution_count, desc="Account Creation Progress")

    for i in range(execution_count):
        page = ChromiumPage(port)
        
        # Initialize handlers
        email_handler = EmailHandler(page)
        account_creator = AccountCreator()
        password_generator = PasswordGenerator()

        # Get email
        email = await email_handler.get_email(bar, i, execution_count)
        if not email:
            print("Failed to generate email. Exiting...")
            continue

        bar.set_description(f"Generate account process completed [{i + 1}/{execution_count}]")
        bar.n += 0.1
        bar.refresh()

        # Setup new tab and bypass Cloudflare
        tab = page.new_tab(EXITLAG_REGISTER_URL)
        CloudflareBypasser(tab).bypass()
        bar.set_description(f"Bypassed Cloudflare captcha protection [{i + 1}/{execution_count}]")
        bar.n += 0.1
        bar.refresh()
        print()

        # Generate password and create account
        password = password_generator.generate()
        if await account_creator.create_account(page, tab, email, password, bar):
            if await email_handler.verify_email(page, tab, email, bar):
                accounts.append({"email": email, "password": password})
                bar.set_description(f"All process completed [{i + 1}/{execution_count}]")
                bar.n += 1
                bar.refresh()
                print()
            else:
                print("Failed to verify email. Skipping and continuing...\n")
                bar.n += 0.1
                bar.refresh()
        else:
            print("Failed to create account. Exiting...")
            bar.n += 0.1
            bar.refresh()

        page.quit()

    bar.close()
    AccountManager.save_accounts(accounts)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"An error occurred: {e}")

import asyncio
import re
import json
import browsers
import warnings
import string
import secrets
import random
from tqdm import TqdmExperimentalWarning
from tqdm.rich import tqdm
from DrissionPage import ChromiumPage, ChromiumOptions
from lib.bypass import CloudflareBypasser
from lib.lib import Main
from datetime import datetime
from faker import Faker

warnings.filterwarnings("ignore", category=TqdmExperimentalWarning)
fake = Faker()

async def get_email(page: ChromiumPage) -> str:
    """Get a new email address from mails.org"""
    page.listen.start("https://mails.org", method="POST")
    page.get("https://mails.org")
    for _ in range(10):
        result = page.listen.wait()
        if result.url == "https://mails.org/api/email/generate":
            return result.response.body["message"]
    return None


async def create_account(page: ChromiumPage, tab, email: str, password: str, bar: tqdm) -> bool:
    """Create a new account on exitlag.com"""
    try:
        first_name = fake.first_name()
        last_name = fake.last_name()        
        password = generate_password(12)

        tab.ele(".rc-anchor-logo-img rc-anchor-logo-img-large", timeout=10)
        tab.ele("#inputFirstName").input(first_name)
        tab.ele("#inputLastName").input(last_name)
        tab.ele("#inputEmail").input(email)
        tab.ele("#inputNewPassword2").input(password)
        tab.ele("#inputNewPassword1").input(password)
        await asyncio.sleep(1)
        page.listen.start("https://mails.org", method="POST")
        await asyncio.sleep(1)
        tab.ele(".custom-checkbox--input checkbox").click()
        bar.set_description("Signup process completed")
        bar.update(30)
        # reCAPTCHA button element
        recaptcha_button = tab.ele(".btn btn-primary btn-block  btn-recaptcha btn-recaptcha-invisible")
        # Attempt to remove the disabled attribute until it's not disabled anymore
        max_attempts = 10  # Set a maximum number of attempts to avoid infinite loops
        attempts = 0

        while attempts < max_attempts:
            # Check if the recaptcha_button have disabled attr
            if recaptcha_button.attr("disabled") is not None:
                tab.run_js("arguments[0].removeAttribute('disabled')", recaptcha_button)
                await asyncio.sleep(0.5)
                attempts += 1
            else:
                recaptcha_button.click()
                # Wait for the URL to change after clicking
                if tab.wait.url_change("https://www.exitlag.com/clientarea.php", timeout=60):
                    return True
                else:
                    # If the URL did not change, it might mean the button was disabled again
                    recaptcha_button = tab.ele(".btn btn-primary btn-block  btn-recaptcha btn-recaptcha-invisible")  # Re-fetch the button
                    attempts = 0
        # Final check to see if the button is still disabled
        if recaptcha_button.attr("disabled") is not None:
            print("Error: reCAPTCHA button is still disabled after multiple attempts.")
            return False
    except Exception as e:
        print(f"Error creating account: {e}")
    return False


async def verify_email(page: ChromiumPage, tab, email: str, bar: tqdm) -> bool:
    """Verify the email address"""
    try:
        link = None
        for _ in range(10):
            result = page.listen.wait()
            content = result.response.body["emails"]
            if not content:
                continue
            for emailId, y in content.items():
                if y["subject"] == "[ExitLag] Please confirm your e-mail address":
                    links = re.findall(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", y["body"])
                    for link in links:
                        if link.startswith("https://www.exitlag.com/user/verify"):
                            link = re.sub(r"</?[^>]+>", "", link)
                            break
            if link:
                break
        if link:
            bar.set_description("Visiting verify email link")
            bar.update(20)
            tab.get(link)
            await asyncio.sleep(5)
            bar.set_description("Clearing cache and data")
            bar.update(9)
            tab.set.cookies.clear()
            tab.clear_cache()
            page.set.cookies.clear()
            page.clear_cache()
            page.quit()
            return True
    except Exception as e:
        print(f"Error verifying email: {e}")
    return False


def generate_password(length=12):
    """Generate a strong password with uppercase, lowercase, digits, and special characters."""
    if length < 8:
        raise ValueError("Password length should be at least 8 characters.")
    
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_characters = string.punctuation
    
    password = [
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(digits),
        random.choice(special_characters)
    ]
    
    all_characters = lowercase + uppercase + digits + special_characters
    password += random.choices(all_characters, k=length - len(password))
    
    random.shuffle(password)
  
    return ''.join(password)
    
async def clear_cache_and_cookies(tab):
    """Clear session storage, cookies, and cache for the given tab."""
    tab.clear_cache(cookies=True)
    print("Cleared session storage, cache, and cookies.")

async def main():
    main_library = Main()
    port = ChromiumOptions().auto_port()

    await main_library.getSettingsAndBlockIP()

    print("\nEnsuring Chrome availability...")

    if browsers.get("chrome") is None:
        print("\nChrome is required for this tool. Please install it via:\nhttps://google.com/chrome")
    else:
        password_length = 10

        accounts = []
        json_accounts = []

        while True:
            execution_count = input("\nHow many accounts do you want to create?\nIf nothing is entered, the script will stick to the default value (1)\nAmount: ")
            if execution_count == "":
                execution_count = 1
                break
            else:
                try:
                    execution_count = int(execution_count)
                    break
                except ValueError:
                    print("Invalid number given. Please enter a valid number.")

        bar = tqdm(total=execution_count)

        for i in range(execution_count):
            # Create a new session of DrissionPage for each account
            page = ChromiumPage(port)
            email = await get_email(page)
            if not email:
                print("Failed to generate email. Exiting...")
                continue
            bar.set_description(f"Generate account process completed [{i + 1}/{execution_count}]")
            bar.update(0.1)
            tab = page.new_tab("https://www.exitlag.com/register")
            CloudflareBypasser(tab).bypass()
            bar.set_description(f"Bypassed Cloudflare captcha protection [{i + 1}/{execution_count}]")
            bar.update(0.1)
            print()

            password = generate_password(password_length)

            if await create_account(page, tab, email, password, bar):
                if await verify_email(page, tab, email, bar):
                    accounts.append({"email": email, "password": password})
                    json_accounts.append({"email": email, "password": password})
                    bar.set_description(f"All process completed [{i + 1}/{execution_count}]")
                    bar.update(0.8)
                    print()
                else:
                    print("Failed to verify email. Skipping and continuing...\n")
            else:
                print("Failed to create account. Exiting...")

            page.quit()

        bar.close()

        with open("accounts.txt", "a") as f:
            for account in accounts:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"Email: {account['email']}, Password: {account['password']}, (Created at {timestamp})\n")

        with open("accounts.json", "w") as json_file:
            json.dump(json_accounts, json_file, indent=4)
        
        print("\nAll accounts have been created. Here are the accounts' details:\n")
        for account in accounts:
            print(f"Email: {account['email']}, Password: {account['password']}")
        print("\nThey have been saved to the accounts files txt and json.\nHave fun using ExitLag!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"An error occurred: {e}")

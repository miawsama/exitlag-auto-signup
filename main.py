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

async def get_email(page: ChromiumPage, bar: tqdm, iteration: int, total: int) -> str:
    """Get a new email address from mails.org"""
    page.listen.start("https://mails.org", method="POST")
    page.get("https://mails.org")
    for _ in range(10):
        result = page.listen.wait()
        if result.url == "https://mails.org/api/email/generate":
            bar.set_description(f"Generate Email Completed [{iteration + 1}/{total}]")
            bar.update(0.1)
            return result.response.body["message"]
    return None

async def create_account(page: ChromiumPage, tab, email: str, password: str, bar: tqdm) -> bool:
    """Create a new account on exitlag.com"""
    try:
        first_name = fake.first_name()
        last_name = fake.last_name()
        
        tab.ele(".rc-anchor-logo-img rc-anchor-logo-img-large", timeout=10)
        tab.ele("#inputFirstName").input(first_name)
        tab.ele("#inputLastName").input(last_name)
        tab.ele("#inputEmail").input(email)
        tab.ele("#inputNewPassword1").input(password)
        tab.ele("#inputNewPassword2").input(password)
        await asyncio.sleep(1)
        
        page.listen.start("https://mails.org", method="POST")
        tab.ele(".custom-checkbox--input checkbox").click()
        bar.set_description("Signup process completed")
        bar.n += 0.1
        bar.refresh()
        
        recaptcha_button = tab.ele(".btn btn-primary btn-block  btn-recaptcha btn-recaptcha-invisible")
        max_attempts = 10
        attempts = 0
        while attempts < max_attempts:
            if recaptcha_button.attr("disabled") is not None:
                tab.run_js("arguments[0].removeAttribute('disabled')", recaptcha_button)
                await asyncio.sleep(0.5)
                attempts += 1
            else:
                recaptcha_button.click()
                await asyncio.sleep(2)

                error_element = tab.ele(".alert alert-danger error-payment", timeout=5)
                if error_element:
                    print("Error: Payment error message appeared. Re-entering the last generated password.")
                    tab.ele("#inputNewPassword1").input(password)
                    tab.ele("#inputNewPassword2").input(password)
                    recaptcha_button.click()
                    await asyncio.sleep(2)
                    error_element = tab.ele(".alert alert-danger error-payment", timeout=5)
                    if error_element:
                        print("Error: Payment error message still appears. Account creation failed.")
                        return False

                if tab.wait.url_change("https://www.exitlag.com/clientarea.php", timeout=60):
                    bar.set_description("Account created successfully")
                    bar.n += 0.9
                    bar.refresh()
                    return True
                else:
                    recaptcha_button = tab.ele(".btn btn-primary btn-block  btn-recaptcha btn-recaptcha-invisible")
                    attempts = 0

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
            bar.n += 0.1
            bar.refresh()
            tab.get(link)
            await asyncio.sleep(5)
            bar.set_description("Clearing cache and data")
            bar.n += 0.1
            bar.refresh()
            tab.set.cookies.clear()
            tab.clear_cache()
            page.set.cookies.clear()
            page.clear_cache()
            page.quit()
            bar.set_description("Email verified successfully")
            bar.n += 0.8
            bar.refresh()
            return True
    except Exception as e:
        print(f"Error verifying email: { e}")
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

async def main():
    main_library = Main()
    port = ChromiumOptions().auto_port()
    await main_library.getSettingsAndBlockIP()
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

        bar = tqdm(total=execution_count, desc="Account Creation Progress")

        for i in range(execution_count):
            page = ChromiumPage(port)
            email = await get_email(page, bar, i, execution_count)
            if not email:
                print("Failed to generate email. Exiting...")
                continue
            bar.set_description(f"Generate account process completed [{i + 1}/{execution_count}]")
            bar.n += 0.1
            bar.refresh()
            tab = page.new_tab("https://www.exitlag.com/register")
            CloudflareBypasser(tab).bypass()
            bar.set_description(f"Bypassed Cloudflare captcha protection [{i + 1}/{execution_count}]")
            bar.n += 0.1
            bar.refresh()
            print()

            password = generate_password(password_length)

            if await create_account(page, tab, email, password, bar):
                if await verify_email(page, tab, email, bar):
                    accounts.append({"email": email, "password": password})
                    json_accounts.append({"email": email, "password": password})
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

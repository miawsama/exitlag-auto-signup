import asyncio
import re
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

characters = 'abcdefghijklmnopqrstuvwxyz'
uppercase_characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
symbols = '!@#$%^&*()_+-=[]{}|;:,.<>?'
digits = '0123456789'
password_length = 10

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
        # Generate Fake Name
        first_name = fake.first_name()
        last_name = fake.last_name()
        
        tab.ele(".rc-anchor-logo-img rc-anchor-logo-img-large", timeout=10)
        tab.ele("#inputFirstName").input(first_name)
        tab.ele("#inputLastName").input(last_name)
        tab.ele("#inputEmail").input(email)
        tab.actions.click("#inputNewPassword1").input(password)
        tab.actions.click("#inputNewPassword2").input(password)
        await asyncio.sleep(1)
        
        page.listen.start("https://mails.org", method="POST")
        tab.ele(".custom-checkbox--input checkbox").click()
        bar.set_description("Signup process completed")
        bar.update(30)  
        tab.ele(".btn btn-primary btn-block  btn-recaptcha btn-recaptcha-invisible").click()
        
        if tab.wait.url_change("https://www.exitlag.com/clientarea.php", timeout=60):
            return True
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
    

async def main():
    main_library = Main()
    port = ChromiumOptions().auto_port()

    await main_library.getSettingsAndBlockIP()

    print("\nEnsuring Chrome availability...")

    if browsers.get("chrome") is None:
        print("\nChrome is required for this tool. Please install it via:\nhttps://google.com/chrome")
    else:
        password_length = 8
        characters = string.ascii_uppercase + string.ascii_lowercase + string.digits + string.punctuation
        symbols = random.sample(string.punctuation, 2)

        accounts = []

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

        bar = tqdm(total=execution_count * 100)

        for i in range(execution_count):
            page = ChromiumPage(port)
            email = await get_email(page)
            if not email:
                print("Failed to generate email. Exiting...")
                continue
            bar.set_description(f"Generate account process completed [{i + 1}/{execution_count}]")
            bar.update(15)
            tab = page.new_tab("https://www.exitlag.com/register")
            CloudflareBypasser(tab).bypass()
            bar.set_description(f"Bypassed Cloudflare captcha protection [{i + 1}/{execution_count}]")
            bar.update(5)
            print()

            # Define the number of each character type
            num_lowercase = 2
            num_uppercase = 2
            num_digits = 2
            num_symbols = password_length - (num_lowercase + num_uppercase + num_digits)

            # Generate the required characters
            lowercase_letters = ''.join(secrets.choice(characters) for _ in range(num_lowercase))
            uppercase_letters = ''.join(secrets.choice(uppercase_characters) for _ in range(num_uppercase))
            digits = ''.join(secrets.choice(digits) for _ in range(num_digits))
            symbols = ''.join(secrets.choice(symbols) for _ in range(num_symbols))

            # Combine all parts
            password = lowercase_letters + uppercase_letters + digits + symbols

            # Shuffle the final password
            password_list = list(password)
            random.shuffle(password_list)
            password = ''.join(password_list)

            # Ensure the password length is correct
            assert len(password) == password_length, "Password length mismatch!"

            # Ensure that the password contains at least one lowercase character
            if not any(c.islower() for c in password):
                password += secrets.choice(characters)  # Add a lowercase character if it's not present

            if await create_account(page, tab, email, password, bar):
                if await verify_email(page, tab, email, bar):
                    accounts.append({"email": email, "password": password})
                    bar.set_description(f"All process completed [{i + 1}/{execution_count}]")
                    bar.update(80)
                    print()
                else:
                    print("Failed to verify email. Skipping and continuing...\n")
            else:
                print("Failed to create account. Exiting...")

        bar.close()

        with open("accounts.txt", "a") as f:
            for account in accounts:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"Email: {account['email']}, Password: {account['password']}, (Created at {timestamp})\n")
        print("\nAll accounts have been created. Here are the accounts' details:\n")
        for account in accounts:
            print(f"Email: {account['email']}, Password: {account['password']}")
        print("\nThey have been saved to the file accounts.txt.\nHave fun using ExitLag!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"An error occurred: {e}")

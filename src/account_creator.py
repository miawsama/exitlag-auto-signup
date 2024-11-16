import asyncio
from typing import Dict, Optional
from DrissionPage import ChromiumPage
from tqdm import tqdm
from faker import Faker
from src.config import SELECTORS, EXITLAG_CLIENT_AREA

class AccountCreator:
    def __init__(self):
        self.fake = Faker()

    async def create_account(self, page: ChromiumPage, tab, email: str, password: str, bar: tqdm) -> bool:
        """Create a new account on exitlag.com"""
        try:
            self._fill_registration_form(tab, email, password)
            return await self._submit_form(tab, page, bar)
        except Exception as e:
            print(f"Error creating account: {e}")
            return False

    def _fill_registration_form(self, tab, email: str, password: str):
        first_name = self.fake.first_name()
        last_name = self.fake.last_name()
        
        tab.ele(SELECTORS['first_name']).input(first_name)
        tab.ele(SELECTORS['last_name']).input(last_name)
        tab.ele(SELECTORS['email']).input(email)
        tab.ele(SELECTORS['password1']).input(password)
        tab.ele(SELECTORS['password2']).input(password)

    async def _submit_form(self, tab, page: ChromiumPage, bar: tqdm) -> bool:
        await asyncio.sleep(1)
        page.listen.start("https://mails.org", method="POST")
        tab.ele(SELECTORS['checkbox']).click()
        
        bar.set_description("Signup process completed")
        bar.n += 0.1
        bar.refresh()

        return await self._handle_recaptcha(tab, bar)

    async def _handle_recaptcha(self, tab, bar: tqdm, max_attempts: int = 10) -> bool:
        recaptcha_button = tab.ele(SELECTORS['recaptcha_btn'])
        attempts = 0

        while attempts < max_attempts:
            if await self._try_recaptcha_click(tab, recaptcha_button):
                if await self._verify_registration_success(tab, bar):
                    return True
            attempts += 1

        print("Error: reCAPTCHA button is still disabled after multiple attempts.")
        return False

    async def _try_recaptcha_click(self, tab, recaptcha_button) -> bool:
        if recaptcha_button.attr("disabled") is not None:
            tab.run_js("arguments[0].removeAttribute('disabled')", recaptcha_button)
            await asyncio.sleep(0.5)
            return False
        
        recaptcha_button.click()
        await asyncio.sleep(2)
        return True

    async def _verify_registration_success(self, tab, bar: tqdm) -> bool:
        if tab.wait.url_change(EXITLAG_CLIENT_AREA, timeout=60):
            bar.set_description("Account created successfully")
            bar.n += 0.9
            bar.refresh()
            return True
        return False

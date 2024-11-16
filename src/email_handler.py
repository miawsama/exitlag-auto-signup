import asyncio
import re
from typing import Optional
from DrissionPage import ChromiumPage
from tqdm import tqdm

class EmailHandler:
    def __init__(self, page: ChromiumPage):
        self.page = page

    async def get_email(self, bar: tqdm, iteration: int, total: int) -> Optional[str]:
        """Get a new email address from mails.org"""
        self.page.listen.start("https://mails.org", method="POST")
        self.page.get("https://mails.org")
        
        for _ in range(10):
            result = self.page.listen.wait()
            if result.url == "https://mails.org/api/email/generate":
                bar.set_description(f"Generate Email Completed [{iteration + 1}/{total}]")
                bar.update(0.1)
                return result.response.body["message"]
        return None

    async def verify_email(self, page: ChromiumPage, tab, email: str, bar: tqdm) -> bool:
        """Verify the email address"""
        try:
            link = await self._find_verification_link(page)
            if link:
                return await self._process_verification(tab, link, bar, page)
        except Exception as e:
            print(f"Error verifying email: {e}")
        return False

    async def _find_verification_link(self, page) -> Optional[str]:
        """Find the verification link in the email content"""
        for _ in range(10):
            result = page.listen.wait()
            content = result.response.body["emails"]
            if not content:
                continue
            
            link = self._extract_link_from_content(content)
            if link:
                return link
        return None

    def _extract_link_from_content(self, content: dict) -> Optional[str]:
        """Extract verification link from email content"""
        for _, email_data in content.items():
            if email_data["subject"] == "[ExitLag] Please confirm your e-mail address":
                links = re.findall(
                    r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                    email_data["body"]
                )
                for link in links:
                    if link.startswith("https://www.exitlag.com/user/verify"):
                        return re.sub(r"</?[^>]+>", "", link)
        return None

    async def _process_verification(self, tab, link: str, bar: tqdm, page: ChromiumPage) -> bool:
        """Process the verification link"""
        bar.set_description("Visiting verify email link")
        bar.n += 0.1
        bar.refresh()
        
        tab.get(link)
        await asyncio.sleep(5)
        
        bar.set_description("Clearing cache and data")
        bar.n += 0.1
        bar.refresh()
        
        self._clear_browser_data(tab, page)
        
        bar.set_description("Email verified successfully")
        bar.n += 0.8
        bar.refresh()
        return True

    def _clear_browser_data(self, tab, page):
        """Clear browser cache and cookies"""
        tab.set.cookies.clear()
        tab.clear_cache()
        page.set.cookies.clear()
        page.clear_cache()
        page.quit()

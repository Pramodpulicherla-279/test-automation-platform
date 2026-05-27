import json
import allure
from pathlib import Path


class LoginPage:
    def __init__(self, page):
        self.page     = page
        self.locators = self._load_locators()

    def _load_locators(self):
        path = Path(__file__).parents[1] / "locators" / "login.json"
        with open(path) as f:
            return json.load(f)

    def navigate(self, url: str):
        with allure.step(f"Navigate to {url}"):
            self.page.goto(url)

    def fill_email(self, username: str):
        with allure.step(f"Fill email → {username}"):
            self.page.wait_for_selector(self.locators["email_input"], state="visible")
            self.page.fill(self.locators["email_input"], username)

    def fill_password(self, password: str):
        with allure.step("Fill password"):
            self.page.wait_for_selector(self.locators["password_input"], state="visible")
            self.page.fill(self.locators["password_input"], password)

    def click_login_button(self):
        with allure.step("Click login button and wait for navigation"):
            self.page.wait_for_selector(self.locators["login_button"], state="visible")
            with self.page.expect_navigation(timeout=15_000):
                self.page.click(self.locators["login_button"])
            self.page.wait_for_url("**/home-4", timeout=15_000)

    def get_dashboard_text(self) -> str:
        with allure.step("Verify dashboard loaded"):
            selector = self.locators["dashboard_text"]
            self.page.wait_for_url("**/home-4", timeout=15_000)
            for attempt in range(3):
                try:
                    element = self.page.locator(selector)
                    element.wait_for(state="visible", timeout=5_000)
                    text = element.inner_text()
                    allure.attach(text, name="dashboard_text",
                                  attachment_type=allure.attachment_type.TEXT)
                    return text
                except Exception as e:
                    print(f"[RETRY] Attempt {attempt+1}: {e}", flush=True)
                    self.page.wait_for_timeout(2_000)
            screenshot = self.page.screenshot()
            allure.attach(screenshot, name="dashboard_not_found",
                          attachment_type=allure.attachment_type.PNG)
            raise Exception("Dashboard element not found after 3 retries")

    def login(self, username: str, password: str):
        with allure.step(f"Login as {username}"):
            self.fill_email(username)
            self.fill_password(password)
            self.click_login_button()
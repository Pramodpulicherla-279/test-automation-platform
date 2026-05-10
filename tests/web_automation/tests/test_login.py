import pytest
import allure


@allure.feature("Login")
class TestLogin:

    @allure.story("TC_L001 – Successful login")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_login_valid_credentials(self, shared_page, login_page, test_data):
        creds = test_data["login"]

        with allure.step("Open application URL"):
            login_page.navigate(test_data["base_url"])

        with allure.step("Perform login"):
            login_page.login(creds["username"], creds["password"])

        with allure.step("Assert URL contains /home-4"):
            shared_page.wait_for_url("**/home-4", timeout=15_000)
            assert "home-4" in shared_page.url, \
                f"Expected /home-4 in URL, got: {shared_page.url}"

    @allure.story("TC_L002 – Dashboard text visible after login")
    @allure.severity(allure.severity_level.NORMAL)
    def test_dashboard_text_visible(self, shared_page, login_page, test_data):
        expected = test_data["login"]["expected_dashboard_text"]

        with allure.step("Verify dashboard element text"):
            actual = login_page.get_dashboard_text()

        with allure.step(f"Assert dashboard text equals '{expected}'"):
            assert actual == expected, \
                f"Expected: '{expected}', Got: '{actual}'"
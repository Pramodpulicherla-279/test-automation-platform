import pytest
import allure

from tests.web_automation.conftest import onboarding_page




@allure.feature("UserOnboarding")
class TestUserOnboarding:

    @allure.story("TC_001 – Add User")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc_001(self, user_onboarding_page, test_data):
        data = test_data["user_onboarding"]
        user_onboarding_page.open_hamburger_menu()
        user_onboarding_page.click_organization()
        user_onboarding_page.click_users()
        user_onboarding_page.click_add()
        user_onboarding_page.click_add_single_user()
        user_onboarding_page.fill_user_name(data["user_name"])
        user_onboarding_page._fill_number_input()
        user_onboarding_page.click_business_unit_field()
        user_onboarding_page.click_business_unit_option()
        user_onboarding_page.click_user_role_field()
        user_onboarding_page.click_user_role_option()
        user_onboarding_page.click_save()

    @allure.story("TC_002 – Add User → Add Administrator")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc_002(self, user_onboarding_page, test_data):
        data = test_data["user_onboarding"]
        user_onboarding_page._flow_add_User(data["User_name"], data["field_agent"])
        user_onboarding_page.click_save_farm()
        user_onboarding_page._flow_add_crop()
        user_onboarding_page.click_cancel_boundary_btn()
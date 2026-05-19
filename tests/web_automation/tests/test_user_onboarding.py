from cv2 import data
import pytest
import allure



@allure.feature("UserOnboarding")
class TestUserOnboarding:

    @allure.story("TC_001 - Add Users")
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
        user_onboarding_page.click_user_role_option("Field Agent")
        user_onboarding_page.click_save()

    @allure.story("TC_002 - Add Users → Add Manager ")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc_002(self, user_onboarding_page, test_data):
       data = test_data["tc_002"]
       user_onboarding_page.click_add()
       user_onboarding_page.click_add_single_user()
       user_onboarding_page.fill_user_name(data["user_name"])
       user_onboarding_page._fill_number_input()
       user_onboarding_page.click_business_unit_field()
       user_onboarding_page.click_business_unit_option()
       user_onboarding_page.click_user_role_field()
       user_onboarding_page.click_user_role_option("Manager")
       user_onboarding_page.click_save()

    @allure.story("TC_003 - Add Users → Add Supervisor ")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc_003(self, user_onboarding_page, test_data):
       data = test_data["tc_003"]
       user_onboarding_page.click_add()
       user_onboarding_page.click_add_single_user()
       user_onboarding_page.fill_user_name(data["user_name"])
       user_onboarding_page._fill_number_input()
       user_onboarding_page.click_business_unit_field()
       user_onboarding_page.click_business_unit_option()
       user_onboarding_page.click_user_role_field()
       user_onboarding_page.click_user_role_option("Supervisor")
       user_onboarding_page.click_save()

    
   
    # @allure.story("TC_007 - Add BU")
    # @allure.severity(allure.severity_level.CRITICAL)
    # def test_tc_007(self, user_onboarding_page, test_data):
    #    data = test_data["business_unit"]
    #    user_onboarding_page.click_organization()
    #    user_onboarding_page.click_Business_units()
    #    user_onboarding_page.click_three_dot_devqa()    # hover on ...
    #    user_onboarding_page.click_add_from_devqa()  
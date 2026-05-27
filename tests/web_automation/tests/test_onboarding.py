import pytest
import allure


@allure.feature("Onboarding")
class TestOnboarding:

    @allure.story("TC_001 – Add Farmer → Add Farm")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc_001(self, onboarding_page, test_data):
        data = test_data["onboarding"]
        onboarding_page.open_hamburger_menu()
        onboarding_page.click_current_season()
        onboarding_page._flow_add_farmer(data["farmer_name"], data["field_agent"])
        onboarding_page.click_save_farm()
        onboarding_page.click_skip_crop()
        onboarding_page.click_cancel_boundary_btn()

    @allure.story("TC_002 – Add Farmer → Add Farm → Add Crop")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc_002(self, onboarding_page, test_data):
        data = test_data["onboarding"]
        onboarding_page._flow_add_farmer(data["farmer_name"], data["field_agent"])
        onboarding_page.click_save_farm()
        onboarding_page._flow_add_crop()
        onboarding_page.click_cancel_boundary_btn()

    @allure.story("TC_003 – Farmer List → Farmer Farms → Add Farm")
    @allure.severity(allure.severity_level.NORMAL)
    def test_tc_003(self, onboarding_page, test_data):
        onboarding_page._flow_navigate_farmer_farms()
        onboarding_page.click_add_farm_btn()
        onboarding_page.click_save_farm()
        onboarding_page.click_skip_crop()
        onboarding_page.click_cancel_boundary_btn()

    @allure.story("TC_004 – Farmer Farms → Add Farm → Add Crop")
    @allure.severity(allure.severity_level.NORMAL)
    def test_tc_004(self, onboarding_page, test_data):
        with allure.step("Navigate to Farmer Farms"):
            onboarding_page._flow_navigate_farmer_farms()
        with allure.step("Click Add Farm"):
            onboarding_page.click_add_farm_btn()
        with allure.step("Save Farm"):
            onboarding_page.click_save_farm()
        with allure.step("Add Crop"):
            onboarding_page._flow_add_crop()
        with allure.step("Cancel Boundary"):
            onboarding_page.click_cancel_boundary_btn()

    @allure.story("TC_005 – Add Farm → Add Crop → Add Boundary")
    @allure.severity(allure.severity_level.NORMAL)
    def test_tc_005(self, shared_page, onboarding_page, test_data):
        with allure.step("Wait for page stability"):
            shared_page.wait_for_timeout(6_000)
        with allure.step("Navigate to Farmer Farms"):
            onboarding_page._flow_navigate_farmer_farms()
        with allure.step("Click Add Farm"):
            onboarding_page.click_add_farm_btn()
        with allure.step("Save Farm"):
            onboarding_page.click_save_farm()
        with allure.step("Add Crop"):
            onboarding_page._flow_add_crop()
        with allure.step("Draw Boundary"):
            onboarding_page._flow_add_boundary()

    @allure.story("TC_006 – Add Farm → Skip Crop → Add Boundary")
    @allure.severity(allure.severity_level.NORMAL)
    def test_tc_006(self, onboarding_page, test_data):
        with allure.step("Navigate to Farmer Farms"):
            onboarding_page._flow_navigate_farmer_farms()
        with allure.step("Click Add Farm"):
            onboarding_page.click_add_farm_btn()
        with allure.step("Save Farm"):
            onboarding_page.click_save_farm()
        with allure.step("Skip Crop"):
            onboarding_page.click_skip_crop()
        with allure.step("Draw Boundary"):
            onboarding_page._flow_add_boundary()

    @allure.story("TC_007 – Pending Farms → Add Crop → Add Boundary")
    @allure.severity(allure.severity_level.NORMAL)
    def test_tc_007(self, onboarding_page, test_data):
        with allure.step("Navigate to Pending Farms menu"):
            onboarding_page._flow_pending_farms_to_menu()
        with allure.step("Click Add Crop"):
            onboarding_page.click_add_crop_btn_pending_farms()
        with allure.step("Add Crop"):
            onboarding_page._flow_add_crop()
        with allure.step("Draw Boundary"):
            onboarding_page._flow_add_boundary()

    @allure.story("TC_008 – Pending Farms → Add Boundary")
    @allure.severity(allure.severity_level.NORMAL)
    def test_tc_008(self, shared_page, onboarding_page, test_data):
        with allure.step("Wait for page stability"):
            shared_page.wait_for_timeout(6000)
        with allure.step("Navigate to Pending Farms menu"):
            onboarding_page._flow_pending_farms_to_menu()
        with allure.step("Click Add Boundary"):
            onboarding_page.click_add_boundary_btn_pending_farms()
        with allure.step("Draw Boundary"):
            onboarding_page._flow_add_boundary()

    @allure.story("TC_009 – Add Single Farmer")
    @allure.severity(allure.severity_level.NORMAL)
    def test_tc_009(self, onboarding_page, test_data):
        data = test_data["onboarding"]
        with allure.step("Add Farmer"):
            onboarding_page._flow_add_farmer(data["farmer_name"], data["field_agent"])

    @allure.story("TC_010 – Farmer Farms → Add Farm → Add Crop")
    @allure.severity(allure.severity_level.NORMAL)
    def test_tc_010(self, onboarding_page, test_data):
        with allure.step("Navigate to Farmer Farms"):
            onboarding_page._flow_navigate_farmer_farms()
        with allure.step("Click Add Farm"):
            onboarding_page.click_add_farm_btn()
        with allure.step("Save Farm"):
            onboarding_page.click_save_farm()
        with allure.step("Add Crop"):
            onboarding_page._flow_add_crop()
        with allure.step("Cancel Boundary"):
            onboarding_page.click_cancel_boundary_btn()
import pytest
import allure
import time

@allure.feature("Field Updates")
class TestFieldUpdate:

    @allure.story("TC_001 – Add Field Update without media files")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc_001(self, field_update_page, test_data):
        data = test_data["field_update"]
        # field_update_page.open_hamburger_menu()
        field_update_page.click_current_season()
        field_update_page._flow_navigate_farmer_farms()
        field_update_page.click_three_dots()
        field_update_page.click_overview_option()
        field_update_page.click_field_updates_tab()
        field_update_page.click_add_field_update_btn()
        field_update_page.click_date_input()
        field_update_page.click_date_option()
        field_update_page.fill_notes_input(data["notes"])
        field_update_page.click_save_updates()
        field_update_page.verify_farmer_details_text()
        field_update_page.click_three_dots()
        field_update_page.click_overview_option()
        field_update_page.click_field_updates_tab()
        field_update_page.click_cross_icon()

    # @allure.story("TC_002 – Add Field Update with media files (image, video, audio)")
    # @allure.severity(allure.severity_level.CRITICAL)
    # def test_tc_002(self, field_update_page, test_data):
    #     data = test_data["field_update"]
    #     field_update_page.click_three_dots()
    #     field_update_page.click_overview_option()
    #     field_update_page.click_field_updates_tab()
    #     field_update_page.click_add_field_update_btn()
    #     field_update_page.click_date_input()
    #     field_update_page.click_date_option()
    #     field_update_page.fill_notes_input(data["notes"])
    #     field_update_page.upload_files(["tests/web_automation/test_data/image.jpg", "tests/web_automation/test_data/video.mp4", "tests/web_automation/test_data/audio.mp3"])
    #     field_update_page.click_save_updates()
    #     field_update_page.verify_farmer_details_text()
    #     field_update_page.click_three_dots()
    #     field_update_page.click_overview_option()
    #     field_update_page.click_field_updates_tab()
    #     field_update_page.click_cross_icon()


    @allure.story("TC_003 – Add Field Update with media files (image)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc_003(self, field_update_page, test_data):
        data = test_data["field_update"]
        field_update_page.click_three_dots()
        field_update_page.click_overview_option()
        field_update_page.click_field_updates_tab()
        field_update_page.click_add_field_update_btn()
        field_update_page.click_date_input()
        field_update_page.click_date_option()
        field_update_page.fill_notes_input(data["notes"])
        field_update_page.upload_files(["tests/web_automation/test_data/image.jpg"])
        field_update_page.click_save_updates()
        field_update_page.verify_farmer_details_text()
        field_update_page.click_three_dots()
        field_update_page.click_overview_option()
        field_update_page.click_field_updates_tab()
        field_update_page.click_cross_icon()


    @allure.story("TC_004 – Add Field Update with media files (video)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc_004(self, field_update_page, test_data):
        data = test_data["field_update"]
        field_update_page.click_three_dots()
        field_update_page.click_overview_option()
        field_update_page.click_field_updates_tab()
        field_update_page.click_add_field_update_btn()
        field_update_page.click_date_input()
        field_update_page.click_date_option()
        field_update_page.fill_notes_input(data["notes"])
        field_update_page.upload_files(["tests/web_automation/test_data/video.mp4"])
        field_update_page.click_save_updates()
        field_update_page.verify_farmer_details_text()
        field_update_page.click_three_dots()
        field_update_page.click_overview_option()
        field_update_page.click_field_updates_tab()
        field_update_page.click_cross_icon()

    @allure.story("TC_005 – Add Field Update with media files (audio)")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_tc_005(self, field_update_page, test_data):
        data = test_data["field_update"]
        field_update_page.click_three_dots()
        field_update_page.click_overview_option()
        field_update_page.click_field_updates_tab()
        field_update_page.click_add_field_update_btn()
        field_update_page.click_date_input()
        field_update_page.click_date_option()
        field_update_page.fill_notes_input(data["notes"])
        field_update_page.upload_files(["tests/web_automation/test_data/audio.mp3"])
        field_update_page.click_save_updates()
        field_update_page.verify_farmer_details_text()
        field_update_page.click_three_dots()
        field_update_page.click_overview_option()
        field_update_page.click_field_updates_tab()
        field_update_page.click_cross_icon()


import allure
import pytest


@allure.feature("Crop Health")
class TestCropHealth:
    @allure.story("TC_001 – Validate Crop Health Data")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_validate_crop_health_screen(self, crop_health_page, test_data):
        data = test_data["crop_health"]["data_1"]
        crop_health_page.navigate_to_crop_health_screen()
        crop_health_page.wait_for_crop_health_page_load()
        actual_data = crop_health_page.get_crop_health_data()

        failures = []
        with allure.step("Validate Crop Health Data"):
            for key, expected_value in data.items():
                actual_value = actual_data.get(key)

                print(
                    f"\nValidating => {key}"
                    f"\nExpected => {expected_value}"
                    f"\nActual => {actual_value}",
                    flush=True,
                )

                if actual_value != expected_value:
                    error_message = (
                        f"\nMismatch found in '{key}'"
                        f"\nExpected: {expected_value}"
                        f"\nActual: {actual_value}"
                    )
                    allure.attach(error_message, name=f"Mismatch for {key}", attachment_type=allure.attachment_type.TEXT)
                    failures.append(error_message)

        if failures:
            raise AssertionError("\n" + "\n".join(failures))

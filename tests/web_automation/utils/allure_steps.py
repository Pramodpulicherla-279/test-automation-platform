"""
utils/allure_steps.py
=====================
Helpers that bridge the existing tracker.step() style
in page objects to Allure's step/attachment system.
"""

import allure
import functools
from typing import Callable


def allure_step(step_title: str):
    """
    Decorator — wraps any async page-object method in an Allure step.

    Usage:
        @allure_step("Click login button")
        async def click_login(self): ...
    """
    def decorator(fn: Callable):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            with allure.step(step_title):
                return await fn(*args, **kwargs)
        return wrapper
    return decorator


async def attach_screenshot(page, name: str = "screenshot"):
    """Attach a Playwright screenshot to the current Allure step."""
    screenshot = await page.screenshot()
    allure.attach(
        screenshot,
        name=name,
        attachment_type=allure.attachment_type.PNG,
    )


def attach_json(data: dict, name: str = "data"):
    """Attach a JSON blob to the current Allure report."""
    import json
    allure.attach(
        json.dumps(data, indent=2),
        name=name,
        attachment_type=allure.attachment_type.JSON,
    )

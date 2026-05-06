async def execute_actions(page, actions):
    for action in actions:
        if action["type"] == "fill":
            await page.fill(action["selector"], action["value"])
        elif action["type"] == "click":
            await page.click(action["selector"])
        elif action["type"] == "wait":
            await page.wait_for_selector(action["selector"])
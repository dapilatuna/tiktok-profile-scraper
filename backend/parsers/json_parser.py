
import json

from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError
)


def read_embedded_json(page, timeout=15000):

    script_locator = page.locator(
        "script#__UNIVERSAL_DATA_FOR_REHYDRATION__"
    )

    try:
        script_locator.wait_for(
            state="attached",
            timeout=timeout
        )

        script_content = script_locator.text_content(
            timeout=10000
        )

        if script_content:
            return json.loads(script_content)

    except PlaywrightTimeoutError:
        print("Embedded JSON did not appear in time.")

    return {}

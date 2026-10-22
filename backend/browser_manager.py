
from contextlib import contextmanager

from playwright.sync_api import sync_playwright


@contextmanager
def browser_session():

    with sync_playwright() as playwright:

        browser = playwright.chromium.launch(
            channel="chrome",
            headless=False
        )

        try:
            page = browser.new_page()
            yield page

        finally:
            browser.close()


import json

from contextlib import contextmanager

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError
)

# ==========================================
# 1. EXTRACT PROFILE INFORMATION
# ==========================================

@contextmanager
def extract_profile(username: str):
    """
    Extract public TikTok profile information
    using Playwright with Google Chrome.
    """

    profile_url = f"https://www.tiktok.com/@{username}"

    profile_detail = None

    # ======================================
    # 1.1 OPEN PROFILE WITH PLAYWRIGHT
    # ======================================

    print("Opening profile with Google Chrome...")

    with sync_playwright() as playwright:

        browser = playwright.chromium.launch(
            channel="chrome",
            headless=False
        )

        try:
            page = browser.new_page()

            response = page.goto(
                profile_url,
                wait_until="domcontentloaded",
                timeout=30000
            )

            if response is None:
                raise ValueError(
                    "Chrome no devolvió una respuesta."
                )

            print("HTTP status:", response.status)

            if response.status in (403, 429):
                raise ValueError(
                    "TikTok restringió el acceso al perfil."
                )

            if response.status >= 400:
                raise ValueError(
                    f"Error HTTP: {response.status}"
                )

            # ======================================
            # 1.2 EXTRACT EMBEDDED JSON
            # ======================================

            print("Waiting for profile JSON...")

            script_locator = page.locator(
                "script#__UNIVERSAL_DATA_FOR_REHYDRATION__"
            )

            try:
                script_locator.wait_for(
                    state="attached",
                    timeout=15000
                )

                script_content = script_locator.text_content(
                    timeout=10000
                )

                if script_content:
                    data = json.loads(script_content)

                    default_scope = data.get(
                        "__DEFAULT_SCOPE__", {}
                    )

                    profile_detail = default_scope.get(
                        "webapp.user-detail"
                    )

            except PlaywrightTimeoutError:
                print(
                    "Profile JSON did not appear in time."
                )
        # ==========================================
        # 2. VALIDATE EXTRACTED DATA
        # ==========================================

            if not isinstance(profile_detail, dict):
                raise ValueError(
                    "No se encontraron los datos del perfil."
                )

            status_code = profile_detail.get("statusCode")

            if status_code is not None and status_code != 0:
                raise ValueError(
                    "TikTok no devolvió un perfil disponible."
                )

            user_info = profile_detail.get("userInfo") or {}

            user = user_info.get("user") or {}
            stats = user_info.get("stats") or {}

            if not user.get("uniqueId"):
                raise ValueError(
                    "No se pudo identificar el usuario."
                )

            # ==========================================
            # 3. STRUCTURE PROFILE DATA
            # ==========================================

            profile = {
                "username": user.get("uniqueId"),
                "name": user.get("nickname"),
                "biography": user.get("signature"),
                "followers": stats.get("followerCount"),
                "following": stats.get("followingCount"),
                "likes": stats.get("heartCount"),
                "video_count": stats.get("videoCount"),
                "verified": user.get("verified"),
                "private": user.get("privateAccount"),
                "profile_url": profile_url
            }
            yield page, profile

        finally:
             browser.close()


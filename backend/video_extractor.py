import re
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)


# ==========================================
# 1. BROWSER SESSION CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

BROWSER_DATA_DIR = (
        BASE_DIR / "data" / "chrome_session"
)

VIDEO_CARD_SELECTOR = (
    '[data-e2e="user-post-item-list"] '
    '[data-e2e="user-post-item"]'
)


# ==========================================
# 2. VALIDATE VIDEO URLS
# ==========================================

def canonical_video_url(
        url: str,
        username: str
) -> str | None:

    parsed_url = urlparse(url)

    if parsed_url.netloc not in (
            "www.tiktok.com",
            "tiktok.com"
    ):
        return None

    match = re.fullmatch(
        r"/@([^/]+)/video/(\d+)",
        parsed_url.path.rstrip("/")
    )

    if match is None:
        return None

    video_username, video_id = match.groups()

    if video_username.lower() != username.lower():
        return None

    return (
        f"https://www.tiktok.com/"
        f"@{video_username}/video/{video_id}"
    )


# ==========================================
# 3. CONVERT VIEWS DISPLAYED IN HTML
# ==========================================

def parse_view_count(
        display: str
) -> int | None:

    value = display.strip().upper().replace(" ", "")

    match = re.fullmatch(
        r"([\d.,]+)([KMB]?)",
        value
    )

    if match is None:
        return None

    number_text, suffix = match.groups()

    if suffix:
        number_text = number_text.replace(",", ".")
    else:
        number_text = number_text.replace(",", "")

    try:
        number = float(number_text)
    except ValueError:
        return None

    multiplier = {
        "": 1,
        "K": 1_000,
        "M": 1_000_000,
        "B": 1_000_000_000
    }[suffix]

    return round(number * multiplier)


# ==========================================
# 4. DISCOVER VIDEOS FROM THE DOM
# ==========================================

def discover_videos(
        page,
        username: str,
        max_candidates: int = 24,
        max_scrolls: int = 5
) -> tuple[list, list]:

    profile_url = f"https://www.tiktok.com/@{username}"

    found_videos = {}
    errors = []

    print("Opening profile...")

    response = page.goto(
        profile_url,
        wait_until="domcontentloaded",
        timeout=30000
    )

    if response is None:
        raise ValueError(
            "Chrome no devolvió el documento del perfil."
        )

    if response.status in (403, 429):
        raise ValueError(
            "TikTok restringió el acceso al perfil."
        )

    if response.status >= 400:
        raise ValueError(
            f"Error HTTP: {response.status}"
        )

    # --------------------------------------
    # 4.1 READ VIDEO CARDS FROM HTML
    # --------------------------------------

    for attempt in range(max_scrolls + 1):

        page.wait_for_timeout(1500)

        captcha = page.get_by_text(
            "Drag the slider to fit the puzzle",
            exact=False
        )

        if captcha.count() > 0:

            try:
                captcha.wait_for(
                    state="hidden",
                    timeout=120000
                )

            except PlaywrightTimeoutError:
                errors.append(
                    "No se completó la verificación de seguridad."
                )
                break

        cards = page.locator(
            VIDEO_CARD_SELECTOR
        )

        # ----------------------------------
        # 4.2 PROCESS EACH VIDEO CARD
        # ----------------------------------

        for index in range(cards.count()):

            card = cards.nth(index)

            anchor = card.locator(
                'a[href*="/video/"]'
            ).first

            if anchor.count() == 0:
                continue

            raw_url = anchor.get_attribute("href")

            if not raw_url:
                continue

            video_url = canonical_video_url(
                raw_url,
                username
            )

            if video_url is None:
                continue

            video_id = video_url.rsplit("/", 1)[-1]

            if video_id in found_videos:
                continue

            # ------------------------------
            # 4.3 EXTRACT VIDEO VIEWS
            # ------------------------------

            views_element = card.locator(
                '[data-e2e="video-views"]'
            )

            views_display = (
                views_element.first.inner_text().strip()
                if views_element.count()
                else None
            )

            # ------------------------------
            # 4.4 IDENTIFY PINNED VIDEOS
            # ------------------------------

            badge = card.locator(
                '[data-e2e="video-card-badge"]'
            )

            badge_text = (
                badge.first.inner_text().strip().casefold()
                if badge.count()
                else ""
            )

            is_pinned = (
                    "anclado" in badge_text
                    or "pinned" in badge_text
            )

            # ------------------------------
            # 4.5 STRUCTURE VIDEO DATA
            # ------------------------------

            found_videos[video_id] = {
                "id": video_id,
                "video_id": video_id,
                "url": video_url,
                "username": username,
                "description": "",
                "create_time": 0,
                "views": (
                    parse_view_count(views_display)
                    if views_display
                    else None
                ),
                "views_display": views_display,
                "likes": None,
                "comment_count": None,
                "comments_count": None,
                "shares": None,
                "save_count": None,
                "saves": None,
                "duration": None,
                "music_title": None,
                "music_author": None,
                "hashtags": [],
                "pinned": is_pinned,
                "comments": [],
                "comments_extracted": 0
            }

        print(
            "Videos discovered from DOM:",
            len(found_videos)
        )

        if len(found_videos) >= max_candidates:
            break

        # ----------------------------------
        # 4.6 SCROLL TO LOAD MORE VIDEOS
        # ----------------------------------

        if attempt < max_scrolls:
            page.mouse.wheel(0, 1200)

    if not found_videos and not errors:
        errors.append(
            "No se encontraron publicaciones en el DOM."
        )

    return (
        list(found_videos.values())[:max_candidates],
        errors
    )


# ==========================================
# 5. OPEN A VIDEO CARD
# ==========================================

def open_video_card(
        page,
        video_url: str
) -> bool:

    card = page.locator(
        VIDEO_CARD_SELECTOR
    ).filter(
        has=page.locator(
            f'a[href="{video_url}"]'
        )
    ).first

    if card.count() == 0:
        return False

    card.scroll_into_view_if_needed()

    card.click(timeout=10000)

    return True


# ==========================================
# 6. EXTRACT VIDEOS
# ==========================================

def extract_videos(
        username: str,
        limit: int = 10
) -> dict:

    BROWSER_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with sync_playwright() as playwright:

        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_DATA_DIR),
            channel="chrome",
            headless=False
        )

        try:

            page = (
                context.pages[0]
                if context.pages
                else context.new_page()
            )

            # ----------------------------------
            # 6.1 DISCOVER VIDEO CARDS
            # ----------------------------------

            candidates, errors = discover_videos(
                page,
                username
            )

            # ----------------------------------
            # 6.2 SELECT DISCOVERED VIDEOS
            # ----------------------------------

            selected_videos = candidates[:limit]

            # Video details and comments will be
            # extracted from the DOM after inspecting
            # the HTML of an opened video.

            final_videos = selected_videos

            print(
                "Videos extracted from DOM:",
                len(final_videos)
            )

            return {
                "videos": final_videos,
                "urls_discovered": len(candidates),
                "videos_parsed": len(candidates),
                "errors": errors
            }

        finally:
            context.close()
import re
from urllib.parse import urlparse

from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
)
from backend.video_content_extractor import (
    enrich_videos_with_comments
)


# ==========================================
# 1. VIDEO CARD SELECTOR
# ==========================================

VIDEO_CARD_SELECTOR = (
    '[data-e2e="user-post-item-list"] '
    '[data-e2e="user-post-item"]'
)
# ==========================================
# 2. VALIDATE VIDEO URLS
# ==========================================

def canonical_video_url(
        url: str,
        username: str) -> str | None:

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
        normal_limit: int = 10,
        max_scrolls: int = 5
) -> tuple[list, list]:

    profile_url = f"https://www.tiktok.com/@{username}"

    found_videos = {}
    errors = []
    normal_count = 0

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


            # Count only non-pinned videos.
            if not is_pinned:
                normal_count += 1

            # Stop after finding ten normal videos.
            if normal_count >= normal_limit:
                break

        print(
            "Videos discovered from DOM:",
            len(found_videos),
            "| Pinned:",
            sum(
                video["pinned"]
                for video in found_videos.values()
            ),
            "| Normal:",
            normal_count
        )

        # Stop scrolling when the limit is reached.
        if normal_count >= normal_limit:
            break

        # Scroll only if more normal videos are needed.
        if attempt < max_scrolls:
            page.mouse.wheel(0, 1200)

    if not found_videos and not errors:
        errors.append(
            "No se encontraron publicaciones en el DOM."
        )

    return (
        list(found_videos.values()),
        errors
    )




# ==========================================
# 6. EXTRACT VIDEOS
# ==========================================
def extract_videos(
        page,
        username: str,
        limit: int = 10
) -> dict:

    # Discover pinned videos and ten normal videos.
    candidates, errors = discover_videos(
        page,
        username,
        normal_limit=limit
    )

    # Extract data during one visit per candidate.
    enriched = enrich_videos_with_comments(
        page,
        candidates,
        dates_only=False
    )

    # Normal videos are already in profile order.
    normal_videos = [
        video for video in enriched
        if not video["pinned"]
    ][:limit]

    pinned_videos = [
        video for video in enriched
        if video["pinned"]
    ]

    def publication_time(video):
        return video.get("publication_sort_time")

    # Check whether all normal dates were recovered.
    verified_normals = all(
        publication_time(video) is not None
        for video in normal_videos
    )

    if verified_normals and normal_videos:

        # Include pinned videos only when their dates
        # can actually be compared.
        eligible = normal_videos + [
            video for video in pinned_videos
            if publication_time(video) is not None
        ]

        selected = sorted(
            eligible,
            key=lambda video: publication_time(video),
            reverse=True
        )[:limit]

    else:

        # Do not introduce old or undated pinned videos.
        selected = normal_videos[:limit]

        errors.append(
            "No se recuperaron todas las fechas. "
            "Se conservó el orden de los videos normales."
        )

    print("FINAL SELECTED VIDEOS:")

    for index, video in enumerate(selected, start=1):
        print(
            index,
            video["id"],
            video.get("publication_date_label"),
            "PINNED:",
            video["pinned"]
        )

    return {
        "videos": selected,
        "urls_discovered": len(candidates),
        "videos_parsed": len(enriched),
        "errors": errors
    }
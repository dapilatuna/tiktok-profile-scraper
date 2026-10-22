
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError
)

from backend.parsers.html_parser import canonical_video_url
from backend.parsers.metric_parser import parse_view_count


VIDEO_CARD_SELECTOR = (
    '[data-e2e="user-post-item-list"] '
    '[data-e2e="user-post-item"]'
)


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

    print("Reading videos from the open profile...")

    if page.is_closed():
        raise ValueError(
            "La pestaña del perfil está cerrada."
        )

    if page.url.rstrip("/") != profile_url.rstrip("/"):
        raise ValueError(
            "La página abierta no corresponde al perfil solicitado."
        )

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

            views_element = card.locator(
                '[data-e2e="video-views"]'
            )

            views_display = (
                views_element.first.inner_text().strip()
                if views_element.count()
                else None
            )

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

            if not is_pinned:
                normal_count += 1

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

        if normal_count >= normal_limit:
            break

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

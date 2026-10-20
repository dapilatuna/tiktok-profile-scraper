
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from backend.video_content_extractor import (
    extract_video_content,
    enrich_videos_with_comments
)


# ==========================================
# 1. BROWSER SESSION CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

BROWSER_DATA_DIR = (
        BASE_DIR / "data" / "chrome_session"
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
# 3. STRUCTURE VIDEO INFORMATION
# ==========================================

def normalize_video(
        item: dict,
        username: str
) -> dict | None:

    video_id = str(item.get("id") or "")

    author = item.get("author") or {}
    video_username = author.get("uniqueId") or ""

    if not video_id.isdigit():
        return None

    if video_username.lower() != username.lower():
        return None

    stats = item.get("stats") or {}
    video_info = item.get("video") or {}
    music = item.get("music") or {}

    hashtags = [
        challenge.get("title")
        for challenge in (item.get("challenges") or [])
        if isinstance(challenge, dict)
           and challenge.get("title")
    ]

    return {
        "id": video_id,
        "video_id": video_id,
        "url": (
            f"https://www.tiktok.com/"
            f"@{video_username}/video/{video_id}"
        ),
        "username": video_username,
        "description": item.get("desc") or "",
        "create_time": int(item.get("createTime") or 0),
        "views": stats.get("playCount"),
        "likes": stats.get("diggCount"),
        "comment_count": stats.get("commentCount"),
        "comments_count": stats.get("commentCount"),
        "shares": stats.get("shareCount"),
        "save_count": stats.get("collectCount"),
        "saves": stats.get("collectCount"),
        "duration": video_info.get("duration"),
        "music_title": music.get("title"),
        "music_author": music.get("authorName"),
        "hashtags": hashtags,
        "pinned": bool(item.get("isPinnedItem", False)),
        "comments": [],
        "comments_extracted": 0
    }


# ==========================================
# 4. IDENTIFY VIDEO LIST REQUESTS
# ==========================================

def is_video_list_request(url: str) -> bool:

    parsed_url = urlparse(url)

    return (
            parsed_url.netloc in (
        "www.tiktok.com",
        "tiktok.com"
    )
            and parsed_url.path.rstrip("/")
            == "/api/post/item_list"
    )


# ==========================================
# 5. DISCOVER VIDEOS
# ==========================================

def discover_videos(
        page,
        username: str,
        max_candidates: int = 24,
        max_scrolls: int = 5
) -> tuple[list, list]:

    profile_url = f"https://www.tiktok.com/@{username}"

    completed_requests = []
    found_videos = {}
    errors = []

    # --------------------------------------
    # 5.1 OBSERVE COMPLETED NETWORK REQUESTS
    # --------------------------------------

    def observe_finished(request):

        if is_video_list_request(request.url):
            completed_requests.append(request)

            print("Video list request completed.")

    page.on("requestfinished", observe_finished)

    try:

        # --------------------------------------
        # 5.2 OPEN PROFILE
        # --------------------------------------

        print("Opening profile...")

        response = page.goto(
            profile_url,
            wait_until="domcontentloaded",
            timeout=30000
        )

        if response is None:
            raise ValueError(
                "No se recibió el documento del perfil."
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
        # 5.3 READ NETWORK AND DOM DATA
        # --------------------------------------


        for attempt in range(max_scrolls + 1):

            page.wait_for_timeout(2000)

            # Check whether TikTok requests
            # a human security verification.
            captcha_visible = page.get_by_text(
                "Drag the slider to fit the puzzle",
                exact=False
            ).count() > 0

            if captcha_visible:

                print(
                    "CAPTCHA detected. "
                    "Waiting up to 120 seconds "
                    "for manual verification..."
                )

                try:
                    page.get_by_text(
                        "Drag the slider to fit the puzzle",
                        exact=False
                    ).wait_for(
                        state="hidden",
                        timeout=120000
                    )

                    print(
                        "CAPTCHA is no longer visible. "
                        "Continuing video extraction..."
                    )

                    page.wait_for_timeout(3000)

                except PlaywrightTimeoutError:
                    errors.append(
                        "La verificación de seguridad "
                        "no terminó dentro de los "
                        "120 segundos."
                    )

                    print("CAPTCHA verification timed out.")
                    break

            # Process completed video list requests.
            while completed_requests:

                request = completed_requests.pop(0)

                try:
                    video_response = request.response()

                    if video_response is None:
                        continue

                    if video_response.status in (403, 429):
                        errors.append(
                            "TikTok restringió la solicitud "
                            "de publicaciones."
                        )
                        continue

                    if video_response.status != 200:
                        continue

                    response_body = video_response.body()

                    if not response_body:
                        print("Video response is empty.")
                        continue

                    response_data = json.loads(
                        response_body
                    )

                    if not isinstance(response_data, dict):
                        continue

                    item_list = response_data.get(
                        "itemList"
                    ) or []

                    print(
                        "Videos in JSON:",
                        len(item_list)
                    )

                    for item in item_list:

                        if not isinstance(item, dict):
                            continue

                        video = normalize_video(
                            item,
                            username
                        )

                        if video is not None:
                            found_videos[video["id"]] = video

                except (ValueError, TypeError) as error:
                    print(
                        "Invalid video JSON:",
                        error
                    )

                except Exception as error:
                    print(
                        "Could not read video response:",
                        error
                    )

            # Also discover video links from HTML.
            links = page.locator(
                'a[href*="/video/"]'
            ).evaluate_all(
                "elements => elements.map(element => element.href)"
            )

            for link in links:

                video_url = canonical_video_url(
                    link,
                    username
                )

                if video_url is None:
                    continue

                video_id = video_url.rsplit("/", 1)[-1]

                if video_id not in found_videos:
                    found_videos[video_id] = {
                        "id": video_id,
                        "video_id": video_id,
                        "url": video_url,
                        "username": username,
                        "description": "",
                        "create_time": 0,
                        "views": None,
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
                        "pinned": False,
                        "comments": [],
                        "comments_extracted": 0
                    }

            print(
                "Videos discovered:",
                len(found_videos)
            )

            if len(found_videos) >= max_candidates:
                break

            if attempt < max_scrolls:
                page.mouse.wheel(0, 1200)

        videos = sorted(
            found_videos.values(),
            key=lambda video: video["create_time"],
            reverse=True
        )

        if not videos and not errors:
            errors.append(
                "No se recuperaron publicaciones "
                "del perfil."
            )

        return videos[:max_candidates], errors

    finally:
        page.remove_listener(
            "requestfinished",
            observe_finished
        )


# ==========================================
# 6. EXTRACT MOST RECENT VIDEOS
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

        # Persistent context automatically saves
        # cookies and browser session data.
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_DATA_DIR),
            channel="chrome",
            headless=False
        )

        try:

            # Reuse an existing page if available.
            page = (
                context.pages[0]
                if context.pages
                else context.new_page()
            )

            # --------------------------------------
            # 6.1 DISCOVER VIDEOS
            # --------------------------------------

            candidates, errors = discover_videos(
                page,
                username
            )

            # Read missing dates from individual
            # video pages when necessary.
            for video in candidates:

                if video["create_time"] != 0:
                    continue

                try:
                    details = extract_video_content(
                        page,
                        video["url"],
                        include_comments=False
                    )

                    if isinstance(details, dict):
                        for key, value in details.items():
                            if value is not None:
                                video[key] = value

                except Exception as error:
                    errors.append(
                        f"{video['url']}: {error}"
                    )

            # --------------------------------------
            # 6.2 SELECT RECENT VIDEOS
            # --------------------------------------

            candidates.sort(
                key=lambda video: int(
                    video.get("create_time") or 0
                ),
                reverse=True
            )

            selected_videos = candidates[:limit]


            # --------------------------------------
            # 6.3 USE DATA FROM THE VIDEO LIST
            # --------------------------------------

            # The video list response already contains
            # publication dates and engagement statistics.
            # Avoid opening each video unnecessarily.

            final_videos = enrich_videos_with_comments(
                page,
                selected_videos
            )

            print(
                "Videos extracted successfully:",
                len(final_videos)
            )



            return {
                "videos": final_videos,
                "urls_discovered": len(candidates),
                "videos_parsed": len(candidates),
                "errors": errors
            }

        finally:
            # Session data remains on disk.
            context.close()

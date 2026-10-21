import json
import re
import unicodedata
from datetime import datetime, timezone, timedelta

from playwright.sync_api import (
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
)


# ==========================================
# 1. SHARED HELPERS
# ==========================================

def to_utc_date(timestamp):
    if timestamp is None:
        return None

    try:
        return datetime.fromtimestamp(
            int(timestamp),
            tz=timezone.utc
        ).isoformat()

    except (TypeError, ValueError, OverflowError, OSError):
        return None

# ==========================================
# 2. READ VIDEO PUBLICATION DATE FROM DOM
# ==========================================

def extract_publication_date(page):

    date_element = page.locator(
        '[data-e2e="browser-nickname"]'
    ).first

    try:
        date_element.wait_for(
            state="visible",
            timeout=5000
        )

        visible_text = date_element.inner_text(
            timeout=3000
        )

    except PlaywrightError:
        return None, None

    if "·" not in visible_text:
        return None, None

    date_label = (
        visible_text.rsplit("·", 1)[-1]
        .replace("\xa0", " ")
        .strip()
    )

    normalized = unicodedata.normalize(
        "NFKD",
        date_label.casefold()
    ).encode("ascii", "ignore").decode("ascii")

    normalized = " ".join(normalized.split())
    now = datetime.now(timezone.utc)

    match = re.fullmatch(
        r"(?:hace\s+)?(\d+|un|una)\s+"
        r"(min(?:uto)?s?|h(?:ora)?s?|"
        r"d(?:ia)?s?|sem(?:ana)?s?|"
        r"mes(?:es)?|a(?:no)?s?)",
        normalized
    )

    if match:
        amount_text, unit = match.groups()
        amount = (
            1 if amount_text in ("un", "una")
            else int(amount_text)
        )

        if unit.startswith("min"):
            delta = timedelta(minutes=amount)
        elif unit.startswith("h"):
            delta = timedelta(hours=amount)
        elif unit.startswith("d"):
            delta = timedelta(days=amount)
        elif unit.startswith("sem"):
            delta = timedelta(weeks=amount)
        elif unit.startswith("mes"):
            delta = timedelta(days=30 * amount)
        else:
            delta = timedelta(days=365 * amount)

        return date_label, (
                now - delta
        ).timestamp()

    if normalized == "ayer":
        return date_label, (
                now - timedelta(days=1)
        ).timestamp()

    try:
        if re.fullmatch(
                r"\d{4}-\d{1,2}-\d{1,2}",
                normalized
        ):
            date = datetime.strptime(
                normalized,
                "%Y-%m-%d"
            ).replace(tzinfo=timezone.utc)

        elif re.fullmatch(
                r"\d{1,2}-\d{1,2}",
                normalized
        ):
            month, day = map(
                int,
                normalized.split("-")
            )

            date = datetime(
                now.year,
                month,
                day,
                tzinfo=timezone.utc
            )

            if date > now + timedelta(days=1):
                date = date.replace(
                    year=now.year - 1
                )

        else:
            return date_label, None

        return date_label, date.timestamp()

    except ValueError:
        return date_label, None

# ==========================================
# 3. OPEN COMMENTS PANEL
# ==========================================

def open_comments_if_needed(page):

    if page.locator(
            '[data-e2e="comment-level-1"]'
    ).count() > 0:
        return True

    selectors = (
        '[data-e2e="browse-comment-icon"]',
        '[data-e2e="comment-icon"]',
        '[data-e2e="comment-count"]',
    )

    for selector in selectors:

        try:
            button = page.locator(selector).first

            if button.count() and button.is_visible():
                button.click(timeout=2000)
                return True

        except PlaywrightError:
            pass

    return False


# ==========================================
# 4. SCROLL COMMENTS
# ==========================================

def scroll_comments(page):
    # Scroll where the visible comments appear.
    comments = page.locator(
        '[data-e2e="comment-level-1"], '
        '[data-e2e="comment-level-2"]'
    )

    if comments.count():
        try:
            last_comment = comments.last

            last_comment.scroll_into_view_if_needed(
                timeout=3000
            )

            last_comment.hover(timeout=3000)

            page.mouse.wheel(0, 1000)

            return True

        except PlaywrightError:
            pass

    panel = page.locator(
        '[data-e2e="search-comment-container"]'
    ).first

    if panel.count():
        try:
            panel.hover(timeout=2000)
            page.mouse.wheel(0, 1000)
            return True

        except PlaywrightError:
            pass

    return False


def expand_visible_replies(page, max_clicks=3):
    # Expand visible reply groups.
    pattern = re.compile(
        r"(?:ver|mostrar|cargar|view|show|load)"
        r".{0,35}(?:respuestas?|replies|reply)",
        re.IGNORECASE
    )

    controls = page.get_by_text(pattern)
    clicked = 0

    for index in range(
            min(controls.count(), max_clicks)
    ):
        try:
            control = controls.nth(index)

            if control.is_visible():
                control.click(timeout=1500)
                clicked += 1

        except PlaywrightError:
            continue

    return clicked
# ==========================================
# 5. COLLECT COMMENTS FROM DOM
# ==========================================
def collect_comments(
        page,
        video_id,
        max_scrolls=50,
        expected_count=None
):
    """Collect comments and replies loaded in the DOM."""

    collected = {}
    previous_count = 0
    stagnant_rounds = 0

    open_comments_if_needed(page)
    page.wait_for_timeout(1000)

    for attempt in range(max_scrolls + 1):

        expanded = expand_visible_replies(page)

        if expanded:
            page.wait_for_timeout(500)

        texts = page.locator(
            '[data-e2e="comment-level-1"], '
            '[data-e2e="comment-level-2"]'
        )

        for index in range(texts.count()):

            text_node = texts.nth(index)

            try:
                content = text_node.inner_text(
                    timeout=1500
                ).strip()

                if not content:
                    continue

                container = text_node.locator(
                    'xpath=ancestor::div'
                    '[@data-comment-ui-enabled="true"][1]'
                )

                if not container.count():
                    continue

                level = (
                    "2"
                    if text_node.get_attribute("data-e2e")
                       == "comment-level-2"
                    else "1"
                )

                author = container.locator(
                    f'a:has([data-e2e="comment-username-{level}"])'
                ).first

                if not author.count():
                    author = container.locator(
                        'a[href*="/@"]'
                    ).last

                author_url = (
                    author.get_attribute("href")
                    if author.count()
                    else None
                )

                username = (
                    author_url.split("/@", 1)[1]
                    .split("/")[0]
                    .split("?")[0]
                    if author_url and "/@" in author_url
                    else None
                )

                author_name = (
                    author.inner_text(
                        timeout=1500
                    ).strip()
                    if author.count()
                    else None
                )

                date_node = container.locator(
                    f'[data-e2e="comment-time-{level}"]'
                ).first

                label = (
                    date_node.inner_text().strip()
                    if date_node.count()
                    else None
                )

                like_node = container.locator(
                    '[data-e2e="comment-like-count"]'
                ).first

                like_count = (
                    parse_metric(like_node.inner_text())
                    if like_node.count()
                    else None
                )

                comment_id = container.get_attribute("id")

                key = comment_id or (
                    username,
                    content,
                    label
                )

                if key in collected:
                    continue

                collected[key] = {
                    "id": comment_id,
                    "video_id": str(video_id),
                    "parent_comment_id": None,
                    "username": username,
                    "author_name": author_name,
                    "text": content,
                    "created_at_utc": None,
                    "published_label": label,
                    "like_count": like_count,
                    "reply_count": None
                }

            except PlaywrightError:
                continue

        current_count = len(collected)

        if (
                expected_count is not None
                and current_count >= expected_count
        ):
            break

        if (
                current_count == previous_count
                and expanded == 0
        ):
            stagnant_rounds += 1
        else:
            stagnant_rounds = 0

        previous_count = current_count

        if stagnant_rounds >= 5:
            break

        if attempt < max_scrolls:

            if not scroll_comments(page):
                break

            page.wait_for_timeout(900)

    print(
        "Comments recovered:",
        len(collected),
        "/",
        expected_count
    )

    return {
        "comments": list(collected.values()),
        "comments_extracted": len(collected),
        "more_comments_indicated": (
                expected_count is not None
                and len(collected) < expected_count
        )
    }

# ==========================================
# 6. EXTRACT VIDEO DATA FROM HTML
# ==========================================

def parse_metric(text):

    if text is None:
        return None

    value = str(text).strip().upper().replace(" ", "")

    match = re.fullmatch(
        r"([\d.,]+)([KMB]?)",
        value
    )

    if not match:
        return None

    number, suffix = match.groups()

    if suffix:
        number = number.replace(",", ".")
    else:
        number = number.replace(",", "")

    try:
        return round(
            float(number) * {
                "": 1,
                "K": 1000,
                "M": 1000000,
                "B": 1000000000
            }[suffix]
        )

    except ValueError:
        return None


def extract_video_metadata(page, video_id):
    """Read the video's HTML and embedded page data."""

    def visible_text(selector):

        element = page.locator(selector).first

        if element.count() == 0:
            return None

        try:
            return element.inner_text(
                timeout=2000
            ).strip()

        except PlaywrightError:
            return None

    metadata = {}

    # Read data embedded in the HTML document.
    script = page.locator(
        'script#__UNIVERSAL_DATA_FOR_REHYDRATION__'
    ).first

    if script.count():

        try:
            html_data = json.loads(
                script.text_content(timeout=3000) or "{}"
            )

            scope = html_data.get(
                "__DEFAULT_SCOPE__", {}
            )

            detail = scope.get(
                "webapp.video-detail"
            ) or {}

            item = (
                    (detail.get("itemInfo") or {})
                    .get("itemStruct") or {}
            )

            # Never accept another video's data.
            if str(item.get("id")) != str(video_id):

                item = next(
                    (
                        entry
                        for entry in scope.get(
                        "webapp.updated-items", []
                    )
                        if str(entry.get("id"))
                           == str(video_id)
                    ),
                    {}
                )

            if item:

                stats = item.get("stats") or {}
                music = item.get("music") or {}
                movie = item.get("video") or {}

                hashtags = [
                    entry.get("title")
                    for entry in item.get("challenges", [])
                    if entry.get("title")
                ]

                timestamp = item.get("createTime")

                duration = parse_metric(
                    movie.get("duration")
                )

                metadata = {
                    "create_time": (
                        int(timestamp)
                        if timestamp
                        else 0
                    ),
                    "description": (
                            item.get("desc") or ""
                    ),
                    "views": parse_metric(
                        stats.get("playCount")
                    ),
                    "likes": parse_metric(
                        stats.get("diggCount")
                    ),
                    "comment_count": parse_metric(
                        stats.get("commentCount")
                    ),
                    "shares": parse_metric(
                        stats.get("shareCount")
                    ),
                    "save_count": parse_metric(
                        stats.get("collectCount")
                    ),
                    "duration": (
                        duration
                        if duration and duration > 0
                        else None
                    ),
                    "music_title": music.get("title"),
                    "music_author": music.get("authorName"),
                    "hashtags": hashtags
                }

        except (ValueError, TypeError, PlaywrightError):
            pass

    # Read visible elements when embedded data is missing.
    # Read visible metrics when embedded data is missing.
    fallbacks = {
        "likes": '[data-e2e="browse-like-count"]',
        "comment_count": '[data-e2e="browse-comment-count"]',
        "save_count": '[data-e2e="browse-favorite-count"]',
    }

    for field, selector in fallbacks.items():
        if metadata.get(field) is None:
            value = parse_metric(visible_text(selector))
            if value is not None:
                metadata[field] = value

    # Match the video ID before reading its share counter.
    if metadata.get("shares") is None:
        article = page.locator(
            'article[data-e2e="recommend-list-item-container"]'
            f':has([id$="-{video_id}"])'
        )

        if article.count() == 1:
            counter = article.locator(
                '[data-e2e="share-count"]'
            ).first

            if counter.count():
                try:
                    metadata["shares"] = parse_metric(
                        counter.inner_text(timeout=2000)
                    )
                except PlaywrightError:
                    pass

    if not metadata.get("description"):
        description = visible_text(
            '[data-e2e="browse-video-desc"]'
        )
        if description:
            metadata["description"] = description

    if not metadata.get("hashtags"):
        tags = page.locator(
            '[data-e2e="browse-video-desc"] a[href^="/tag/"]'
        ).all_text_contents()

        metadata["hashtags"] = [
            tag.strip().lstrip("#")
            for tag in tags
            if tag.strip()
        ]

    if not metadata.get("music_title"):
        metadata["music_title"] = visible_text(
            '[data-e2e="browse-music"]'
        )

    if not metadata.get("duration"):
        player = page.locator("video").first

        if player.count():
            try:
                value = player.evaluate(
                    "(node) => Number.isFinite(node.duration) "
                    "? Math.round(node.duration) : null"
                )

                if value and value > 0:
                    metadata["duration"] = value

            except PlaywrightError:
                pass

    return metadata

    return metadata


# ==========================================
# 7. INTEGRATED COMMENT EXTRACTION
# ==========================================


def enrich_videos_with_comments(
        page,
        videos,
        dates_only=False
):
    """Extract video data using the existing Chrome session."""

    profile_url = page.url

    for index, video in enumerate(videos, start=1):

        video_id = str(video.get("id") or "")

        if not video_id:
            continue

        extra_pages = []
        previous_pages = set(page.context.pages)
        stop_processing = False

        try:
            print(
                f"Reading video {index}/{len(videos)}: "
                f"{video_id}"
            )

            # Find the corresponding video card.
            card = page.locator(
                f'a[href*="/video/{video_id}"]'
            ).first

            for attempt in range(8):

                if card.count() > 0:
                    break

                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(700)

            if card.count() == 0:
                raise ValueError(
                    "No se encontró la tarjeta del video."
                )

            # Open by clicking, not by direct URL navigation.
            card.scroll_into_view_if_needed(
                timeout=10000
            )

            print("BEFORE VIDEO CLICK:", video_id, flush=True)

            card.click(timeout=12000)

            print("AFTER VIDEO CLICK:", video_id, flush=True)

            page.wait_for_timeout(1500)
            # Reuse this browser, including any tab opened by the click.
            extra_pages = [
                tab for tab in page.context.pages
                if tab not in previous_pages
            ]

            active_page = (
                extra_pages[-1]
                if extra_pages
                else page
            )

            try:
                active_page.locator(
                    '[data-e2e="browser-nickname"], '
                    '[data-e2e="browse-like-count"], '
                    '[data-e2e="like-count"], '
                    '[data-e2e="comment-count"], '
                    '[data-e2e="video-desc"]'
                ).first.wait_for(
                    state="visible",
                    timeout=30000
                )

            except PlaywrightTimeoutError:
                print(
                "Video content did not load within 30 seconds:",
                video_id
            )

            if (
                    "/video/" in active_page.url
                    and f"/video/{video_id}" not in active_page.url
            ):
                raise ValueError(
                    "Se abrió una publicación diferente."
                )

            # Extract all available video metadata.
            metadata = extract_video_metadata(
                active_page,
                video_id
            )

            for key, value in metadata.items():
                if value is not None:
                    video[key] = value

            # Determine publication date.
            timestamp = video.get("create_time")

            if timestamp:

                video["publication_sort_time"] = float(
                    timestamp
                )

                video["created_at_utc"] = to_utc_date(
                    timestamp
                )

                video["publication_date_label"] = (
                    video["created_at_utc"]
                )

            else:

                label, approximate_time = (
                    extract_publication_date(active_page)
                )

                if approximate_time is not None:
                    video["publication_sort_time"] = (
                        approximate_time
                    )

                if label:
                    video["publication_date_label"] = label
                    video["created_at_utc"] = label

            # Read comments during the same video visit.
            if not dates_only:

                if video.get("comment_count") == 0:
                    video["comments"] = []
                    video["comments_extracted"] = 0

                else:
                    comments_data = collect_comments(
                        active_page,
                        video_id,
                        max_scrolls=50,
                        expected_count=video.get("comment_count")
                    )

                    video.update(comments_data)

                    if (
                            video["comments_extracted"] == 0
                            and video.get("comment_count")
                    ):
                        video["comments_error"] = (
                            "TikTok no mostró los textos "
                            "de comentarios en el DOM."
                        )

                        # Read shares in the full video view, using the same page.
            if video.get("shares") is None and f"/video/{video_id}" in active_page.url:
                try:
                    active_page.reload(
                        wait_until="domcontentloaded",
                        timeout=20000
                    )

                    counter = active_page.locator(
                        'article[data-e2e="recommend-list-item-container"]'
                        f':has([id$="-{video_id}"]) [data-e2e="share-count"]'
                    ).first

                    counter.wait_for(state="attached", timeout=12000)

                    video["shares"] = parse_metric(
                        counter.inner_text(timeout=3000)
                    )

                    print("Shares extracted:", video_id, video["shares"])

                except PlaywrightError:
                    print("Shares unavailable:", video_id)

            print(
                "Video:",
                video_id,
                "| Date:",
                video.get("publication_date_label"),
                "| Likes:",
                video.get("likes"),
                "| Comments:",
                video.get("comments_extracted")
            )

        except (PlaywrightError, ValueError, TypeError) as error:

            video["comments_error"] = (
                str(error).split("\n", 1)[0]
            )

            print(
                "Video extraction error:",
                video_id,
                video["comments_error"]
            )

        finally:

            # Close only tabs opened by the video click.
            for tab in extra_pages:
                try:
                    if not tab.is_closed():
                        tab.close()
                except PlaywrightError:
                    pass

            # Restore the original profile page.
            try:
                if not page.is_closed():

                    if page.url != profile_url:

                        try:
                            page.go_back(
                                wait_until="domcontentloaded",
                                timeout=15000
                            )
                        except PlaywrightError:
                            pass

                        if page.url != profile_url:
                            page.goto(
                                profile_url,
                                wait_until="domcontentloaded",
                                timeout=30000
                            )

                    else:
                        page.keyboard.press("Escape")

                    page.wait_for_timeout(700)

            except PlaywrightError as error:
                print(
                    "Could not restore profile:",
                    str(error).split("\n", 1)[0]
                )
                stop_processing = True

        if stop_processing:
            break

    return videos

import json
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

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


def normalize_comment(
        comment,
        video_id,
        results,
        parent_id=None
):
    comment_id = str(comment.get("cid") or "")

    if not comment_id or comment_id in results:
        return

    author = comment.get("user") or {}
    reply_id = str(comment.get("reply_id") or "0")

    results[comment_id] = {
        "id": comment_id,
        "video_id": str(video_id),
        "parent_comment_id": parent_id or (
            reply_id if reply_id != "0" else None
        ),
        "username": author.get("unique_id"),
        "author_name": author.get("nickname"),
        "text": comment.get("text"),
        "created_at_utc": to_utc_date(
            comment.get("create_time")
        ),
        "like_count": comment.get("digg_count"),
        "reply_count": comment.get(
            "reply_comment_total", 0
        ),
        "language": comment.get("comment_language"),
        "pinned": comment.get("author_pin"),
        "liked_by_video_author": comment.get(
            "is_author_digged"
        ),
        "content_type": comment.get("content_type"),
        "has_images": bool(comment.get("image_list")),
        "has_sticker": bool(
            comment.get("cmt_sticker_struct")
        ),
    }

    # Include replies returned with the comment.
    for reply in comment.get("reply_comment") or []:

        if isinstance(reply, dict):
            normalize_comment(
                reply,
                video_id,
                results,
                comment_id
            )


# ==========================================
# 2. IDENTIFY COMMENT RESPONSES
# ==========================================

def is_comment_response(response, video_id):

    parsed = urlparse(response.url)

    if parsed.netloc not in (
            "tiktok.com",
            "www.tiktok.com"
    ):
        return False

    if parsed.path.rstrip("/") != "/api/comment/list":
        return False

    parameters = parse_qs(parsed.query)

    return str(video_id) in parameters.get(
        "aweme_id", []
    )


# ==========================================
# 3. OPEN COMMENTS PANEL
# ==========================================

def open_comments_if_needed(page):

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

    page.evaluate(
        """() => {
            const selectors = [
                '[data-e2e="comment-list"]',
                '[class*="CommentList"]',
                '[class*="CommentContainer"]'
            ];

            for (const selector of selectors) {
                for (
                    const node of document.querySelectorAll(selector)
                ) {
                    let element = node;

                    while (element) {
                        const style = getComputedStyle(element);

                        const hasContent =
                            element.scrollHeight >
                            element.clientHeight + 30;

                        const isScrollable =
                            /auto|scroll/.test(style.overflowY);

                        if (hasContent && isScrollable) {
                            element.scrollTop += Math.max(
                                400,
                                element.clientHeight * 0.9
                            );
                            return;
                        }

                        element = element.parentElement;
                    }
                }
            }

            window.scrollBy(0, 700);
        }"""
    )


# ==========================================
# 5. COLLECT OBSERVED COMMENTS
# ==========================================

def collect_comments(
        page,
        video_id,
        captured_responses,
        max_scrolls=6
):

    comments_by_id = {}

    processed = 0
    response_pages = 0
    response_errors = 0
    total = None
    has_more = None

    page.wait_for_timeout(1200)

    if not captured_responses:
        open_comments_if_needed(page)

    # --------------------------------------
    # READ RECEIVED COMMENT RESPONSES
    # --------------------------------------

    def process_responses():

        nonlocal processed
        nonlocal response_pages
        nonlocal response_errors
        nonlocal total
        nonlocal has_more

        while processed < len(captured_responses):

            response = captured_responses[processed]
            processed += 1

            try:
                if response.status != 200:
                    response_errors += 1
                    continue

                response.finished()
                payload = response.json()

            except (ValueError, PlaywrightError):
                response_errors += 1
                continue

            if not isinstance(payload, dict):
                continue

            if payload.get("status_code", 0) != 0:
                response_errors += 1
                continue

            response_pages += 1

            has_more = payload.get("has_more")
            total = payload.get("total", total)

            for comment in payload.get("comments") or []:

                if isinstance(comment, dict):
                    normalize_comment(
                        comment,
                        video_id,
                        comments_by_id
                    )

    # --------------------------------------
    # READ MORE COMMENTS WHEN AVAILABLE
    # --------------------------------------

    quiet_rounds = 0

    for _ in range(max_scrolls):

        page.wait_for_timeout(1000)

        previous = (
            len(comments_by_id),
            response_pages
        )

        process_responses()

        if has_more in (0, False):
            break

        current = (
            len(comments_by_id),
            response_pages
        )

        if current == previous:
            quiet_rounds += 1
        else:
            quiet_rounds = 0

        if quiet_rounds >= 3:
            break

        try:
            scroll_comments(page)

        except PlaywrightError:
            break

    page.wait_for_timeout(400)
    process_responses()

    return {
        "comments": list(comments_by_id.values()),
        "comments_extracted": len(comments_by_id),
        "comment_response_pages": response_pages,
        "comment_total_from_response": total,
        "more_comments_indicated": (
            bool(has_more)
            if has_more is not None
            else None
        ),
        "comment_response_errors": response_errors,
    }


# ==========================================
# 6. EXISTING VIDEO DETAIL EXTRACTION
# ==========================================

def extract_video_content(
        page,
        video_url,
        include_comments=False
):
    """
    Preserve compatibility with the existing
    video extractor.
    """

    video_id = urlparse(
        video_url
    ).path.rstrip("/").split("/")[-1]

    captured_responses = []

    def observe_response(response):

        if is_comment_response(response, video_id):
            captured_responses.append(response)

    if include_comments:
        page.on("response", observe_response)

    try:

        response = page.goto(
            video_url,
            wait_until="domcontentloaded",
            timeout=30000
        )

        if response is None or response.status >= 400:
            raise ValueError(
                "No se pudo abrir el video."
            )

        script = page.locator(
            "script#__UNIVERSAL_DATA_FOR_REHYDRATION__"
        )

        script.wait_for(
            state="attached",
            timeout=15000
        )

        payload = json.loads(
            script.text_content(timeout=10000) or "{}"
        )

        scope = payload.get("__DEFAULT_SCOPE__") or {}

        detail = scope.get("webapp.video-detail") or {}

        item = (
                (detail.get("itemInfo") or {})
                .get("itemStruct") or {}
        )

        if not item:
            raise ValueError(
                "No se encontró información del video."
            )

        stats = item.get("stats") or {}
        video = item.get("video") or {}
        music = item.get("music") or {}
        author = item.get("author") or {}

        result = {
            "id": str(item.get("id") or video_id),
            "url": video_url,
            "description": item.get("desc"),
            "created_at_utc": to_utc_date(
                item.get("createTime")
            ),
            "create_time": item.get("createTime"),

            "author": {
                "username": author.get("uniqueId"),
                "name": author.get("nickname"),
                "verified": author.get("verified"),
            },

            "view_count": stats.get("playCount"),
            "like_count": stats.get("diggCount"),
            "comment_count": stats.get("commentCount"),
            "share_count": stats.get("shareCount"),
            "save_count": stats.get("collectCount"),

            "stats": stats,
            "stats_v2": item.get("statsV2") or {},

            "hashtags": [
                tag.get("title")
                for tag in item.get("challenges") or []
                if isinstance(tag, dict)
                           and tag.get("title")
            ],

            "mentions": [
                entry.get("userUniqueId")
                for entry in item.get("textExtra") or []
                if isinstance(entry, dict)
                             and entry.get("userUniqueId")
            ],

            "music": {
                "id": music.get("id"),
                "title": music.get("title"),
                "author": music.get("authorName"),
                "original": music.get("original"),
            },

            "video": {
                "duration_seconds": video.get("duration"),
                "width": video.get("width"),
                "height": video.get("height"),
                "ratio": video.get("ratio"),
                "format": video.get("format"),
                "cover": video.get("cover"),
            },

            "region": item.get("region"),
            "is_ad": item.get("isAd"),
            "is_pinned": item.get("isPinnedItem"),
            "text_extra": item.get("textExtra"),
            "challenges": item.get("challenges"),
        }

        if include_comments:

            comment_data = collect_comments(
                page,
                video_id,
                captured_responses
            )

            result.update(comment_data)

        return result

    finally:

        if include_comments:
            page.remove_listener(
                "response",
                observe_response
            )


# ==========================================
# 7. INTEGRATED COMMENT EXTRACTION
# ==========================================

def enrich_videos_with_comments(page, videos):
    """
    Collect comments using the browser session
    that already discovered the profile videos.
    """

    context = page.context
    profile_url = page.url

    for index, video in enumerate(videos, start=1):

        video_id = str(video.get("id") or "")

        # Skip videos without comments.
        if not video_id or video.get("comment_count") == 0:
            continue

        captured_responses = []

        existing_pages = set(context.pages)
        extra_pages = []
        navigation_failed = False

        # ----------------------------------
        # OBSERVE COMMENT RESPONSES
        # ----------------------------------

        def observe_response(response):

            if is_comment_response(response, video_id):
                captured_responses.append(response)

        context.on("response", observe_response)

        try:

            print(
                f"Collecting comments "
                f"{index}/{len(videos)}: {video_id}"
            )

            # Find the video card on the profile.
            card = page.locator(
                f'a[href*="/video/{video_id}"]'
            ).first

            # Some cards appear after scrolling.
            for _ in range(6):

                if card.count():
                    break

                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(650)

            if not card.count():

                video["comments_error"] = (
                    "No se encontró la tarjeta "
                    "de este video en el perfil."
                )

                continue

            # ----------------------------------
            # OPEN VIDEO FROM EXISTING PROFILE
            # ----------------------------------

            card.scroll_into_view_if_needed(
                timeout=10000
            )

            card.click(timeout=12000)

            page.wait_for_timeout(1800)

            # TikTok may open a new tab or
            # display the video in the same page.
            extra_pages = [
                tab for tab in context.pages
                if tab not in existing_pages
            ]

            active_page = (
                extra_pages[-1]
                if extra_pages
                else page
            )

            # ----------------------------------
            # CHECK SECURITY VERIFICATION
            # ----------------------------------

            challenge = active_page.get_by_text(
                "Drag the slider to fit the puzzle",
                exact=False
            )

            if challenge.count():

                video["comments_error"] = (
                    "TikTok solicitó una "
                    "verificación de seguridad."
                )

                navigation_failed = True

            else:

                # ----------------------------------
                # COLLECT COMMENTS AND REPLIES
                # ----------------------------------

                comments_data = collect_comments(
                    active_page,
                    video_id,
                    captured_responses,
                    max_scrolls=6
                )

                video.update(comments_data)

                if (
                        comments_data["comment_response_pages"]
                        == 0
                ):

                    video["comments_error"] = (
                        "No se recibió una respuesta "
                        "de comentarios para este video."
                    )

                print(
                    "Comments extracted:",
                    video["comments_extracted"]
                )

        except (PlaywrightError, ValueError) as error:

            video["comments_error"] = (
                str(error).split("\n", 1)[0]
            )

            print(
                "Comment extraction error:",
                video["comments_error"]
            )

        finally:

            # Stop observing this video's responses.
            context.remove_listener(
                "response",
                observe_response
            )

            # Close only additional tabs.
            for tab in extra_pages:

                try:
                    if not tab.is_closed():
                        tab.close()

                except PlaywrightError:
                    pass

            # ----------------------------------
            # RETURN TO THE PROFILE
            # ----------------------------------

            try:

                if (
                        not page.is_closed()
                        and page.url != profile_url
                ):

                    page.go_back(
                        wait_until="domcontentloaded",
                        timeout=15000
                    )

                    page.wait_for_timeout(800)

                    if page.url != profile_url:
                        navigation_failed = True

                elif not page.is_closed():

                    page.keyboard.press("Escape")

            except PlaywrightError:
                navigation_failed = True

        # Do not continue navigating if
        # the profile could not be restored.
        if navigation_failed:

            remaining_videos = videos[index:]

            for remaining_video in remaining_videos:

                remaining_video["comments_error"] = (
                    "No se consultaron comentarios "
                    "debido a una restricción anterior."
                )

            break

    return videos

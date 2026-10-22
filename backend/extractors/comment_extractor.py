
import re

from playwright.sync_api import (
    Error as PlaywrightError
)

from backend.parsers.metric_parser import parse_metric


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


def scroll_comments(page):

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


def collect_comments(
        page,
        video_id,
        max_scrolls=50,
        expected_count=None
):

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


                container = text_node.locator("xpath=..")

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

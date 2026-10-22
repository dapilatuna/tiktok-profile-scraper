
import re
import unicodedata

from datetime import datetime, timezone, timedelta

from playwright.sync_api import (
    Error as PlaywrightError
)

from backend.parsers.json_parser import read_embedded_json
from backend.parsers.metric_parser import parse_metric


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


def extract_video_metadata(page, video_id):

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

    script = page.locator(
        'script#__UNIVERSAL_DATA_FOR_REHYDRATION__'
    ).first

    if script.count():

        try:
            html_data = read_embedded_json(
                page,
                timeout=3000
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

            print(
                "VIDEO JSON:",
                video_id,
                "| found:", bool(item),
                "| shares:",
                (item.get("stats") or {}).get("shareCount")
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


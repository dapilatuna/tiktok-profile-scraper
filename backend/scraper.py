
from playwright.sync_api import (
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError
)

from backend.extractors.video_extractor import discover_videos
from backend.extractors.metadata_extractor import (
    extract_video_metadata,
    extract_publication_date,
    to_utc_date
)
from backend.extractors.comment_extractor import collect_comments
from backend.parsers.json_parser import read_embedded_json
from backend.parsers.metric_parser import parse_metric

def enrich_videos_with_comments(
        page,
        videos,
        dates_only=False
):

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

            card.scroll_into_view_if_needed(
                timeout=10000
            )

            print(
                "BEFORE VIDEO CLICK:",
                video_id,
                flush=True
            )

            card.click(timeout=12000)

            print(
                "AFTER VIDEO CLICK:",
                video_id,
                flush=True
            )

            page.wait_for_timeout(15000)

            extra_pages = [
                tab for tab in page.context.pages
                if tab not in previous_pages
            ]

            active_page = (
                extra_pages[-1]
                if extra_pages
                else page
            )
            print("VIDEO URL:", active_page.url, flush=True)

            html = active_page.content()

            print(
                "VIDEO HTML CHECK:",
                "| video_id:", video_id,
                "| shareCount:", '"shareCount"' in html,
                "| updated-items:", '"webapp.updated-items"' in html,
                "| HTML length:", len(html),
                flush=True
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


            metadata = extract_video_metadata(
                    active_page,
                    video_id
                )

            for key, value in metadata.items():
                if value is not None:
                    video[key] = value

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

            for tab in extra_pages:
                try:
                    if not tab.is_closed():
                        tab.close()
                except PlaywrightError:
                    pass

            try:
                if page.is_closed():
                    raise PlaywrightError(
                        "La pestaña principal se cerró."
                    )

                if page.url.rstrip("/") != profile_url.rstrip("/"):
                    page.go_back(
                        wait_until="domcontentloaded",
                        timeout=15000
                    )


                if page.url.rstrip("/") != profile_url.rstrip("/"):
                    print(
                        "Profile view could not be restored "
                        "without another navigation."
                    )
                    stop_processing = True

                else:
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


def extract_videos(
        page,
        username: str,
        limit: int = 10
) -> dict:

    candidates, errors = discover_videos(
        page,
        username,
        normal_limit=limit
    )


    enriched = enrich_videos_with_comments(
        page,
        candidates,
        dates_only=False
    )

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

    verified_normals = all(
        publication_time(video) is not None
        for video in normal_videos
    )

    if verified_normals and normal_videos:

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

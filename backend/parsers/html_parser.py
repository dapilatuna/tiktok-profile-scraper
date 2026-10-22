
import re
from urllib.parse import urlparse


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

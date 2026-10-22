
from datetime import datetime, timezone

import streamlit as st

from backend.validator import validate_username
from backend.extractors.profile_extractor import extract_profile
from backend.scraper import extract_videos

def run_extraction(username):

    valid_username = validate_username(
        username
    )

    with extract_profile(valid_username) as (page, profile):

        try:
            with st.spinner(
                    "Extrayendo videos y comentarios..."
            ):

                video_report = extract_videos(
                    page,
                    valid_username,
                    limit=10
                )

        except Exception as error:
            video_report = {
                "videos": [],
                "urls_discovered": 0,
                "videos_parsed": 0,
                "errors": [str(error)]
            }

    extraction_result = {
        "extracted_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "profile": profile,
        "video_report": video_report,
        "videos": video_report.get(
            "videos",
            []
        )
    }

    return extraction_result

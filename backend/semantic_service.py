
import math
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


def prepare_semantic_data(data):
    if not isinstance(data, dict):
        raise ValueError("El JSON debe contener un objeto.")

    profile = data.get("profile") or {}
    username = str(
        profile.get("username") or ""
    ).strip()

    videos = data.get("videos") or (
            data.get("video_report") or {}
    ).get("videos") or []

    if not isinstance(videos, list):
        raise ValueError(
            "El JSON no contiene una lista válida de videos."
        )

    records = []
    seen = set()

    for index, video in enumerate(videos):
        if not isinstance(video, dict):
            continue

        video_id = str(
            video.get("video_id")
            or video.get("id")
            or index
        )

        if video_id in seen:
            continue

        seen.add(video_id)

        description = str(
            video.get("description") or ""
        ).strip()

        hashtags = []

        for tag in video.get("hashtags") or []:
            if isinstance(tag, str):
                hashtags.append(tag.strip())

            elif isinstance(tag, dict):
                value = (
                        tag.get("name")
                        or tag.get("title")
                        or ""
                )
                if value:
                    hashtags.append(str(value))

        # Only use the author's own replies.
        author_replies = []

        for comment in video.get("comments") or []:
            if not isinstance(comment, dict):
                continue

            comment_username = str(
                comment.get("username") or ""
            ).strip()

            if (
                    username
                    and comment_username.lstrip("@").casefold()
                    == username.lstrip("@").casefold()
            ):
                text = str(
                    comment.get("text") or ""
                ).strip()

                if text:
                    author_replies.append(text[:300])

        text_parts = []

        if description:
            text_parts.append(description[:600])

        if hashtags:
            text_parts.append(
                "Hashtags: " + " ".join(hashtags[:15])
            )

        if author_replies:
            text_parts.append(
                "Respuestas del autor: "
                + " | ".join(author_replies[:10])
            )

        text = "\n".join(text_parts).strip()

        if not text:
            continue

        records.append({
            "video_id": video_id,
            "label": f"Video {index + 1}",
            "text": text[:2500],
            "url": video.get("url") or "",
            "views": video.get("views"),
            "likes": video.get("likes"),
        })

    return {
        "username": username,
        "videos_found": len(videos),
        "videos_with_text": len(records),
        "records": records[:30],
    }


def cosine_similarity(vector_a, vector_b):
    if len(vector_a) != len(vector_b):
        raise ValueError(
            "Los vectores tienen dimensiones diferentes."
        )

    dot_product = sum(
        a * b
        for a, b in zip(vector_a, vector_b)
    )

    norm_a = math.sqrt(
        sum(value * value for value in vector_a)
    )

    norm_b = math.sqrt(
        sum(value * value for value in vector_b)
    )

    if norm_a == 0 or norm_b == 0:
        return 0.0

    similarity = dot_product / (norm_a * norm_b)

    return max(-1.0, min(1.0, similarity))


def analyze_semantic_similarity(data):
    prepared = prepare_semantic_data(data)
    records = prepared["records"]

    if len(records) < 2:
        raise ValueError(
            "Se necesitan al menos dos videos "
            "con contenido textual."
        )

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "No se encontró GEMINI_API_KEY en .env."
        )

    client = genai.Client(api_key=api_key)

    texts = [
        record["text"]
        for record in records
    ]

    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts,
        config=types.EmbedContentConfig(
            task_type="SEMANTIC_SIMILARITY",
            output_dimensionality=768,
        ),
    )

    if not response.embeddings:
        raise ValueError(
            "Gemini no devolvió embeddings."
        )

    vectors = [
        embedding.values
        for embedding in response.embeddings
    ]

    if len(vectors) != len(records):
        raise ValueError(
            "La cantidad de embeddings no coincide "
            "con los videos enviados."
        )

    if any(not vector for vector in vectors):
        raise ValueError(
            "Gemini devolvió un vector vacío."
        )

    pairs = []

    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            similarity = cosine_similarity(
                vectors[i],
                vectors[j],
            )

            pairs.append({
                "video_a": records[i]["label"],
                "video_b": records[j]["label"],
                "video_a_id": records[i]["video_id"],
                "video_b_id": records[j]["video_id"],
                "similarity": round(
                    similarity * 100, 2
                ),
                "text_a": records[i]["text"],
                "text_b": records[j]["text"],
            })

    pairs.sort(
        key=lambda pair: pair["similarity"],
        reverse=True,
    )

    return {
        "username": prepared["username"],
        "videos_found": prepared["videos_found"],
        "videos_analyzed": len(records),
        "embedding_dimensions": len(vectors[0]),
        "model": "gemini-embedding-001",
        "pairs": pairs,
    }

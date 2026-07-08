"""General helper functions for cleaning and serializing data."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable


def ensure_directory(path: Path) -> None:
    """Create a directory if it does not exist yet."""

    path.mkdir(parents=True, exist_ok=True)


def clean_text(value: object) -> str:
    """Normalize whitespace while preserving the original capitalization."""

    if value is None:
        return ""
    return " ".join(str(value).split()).strip()


def normalize_label(value: object) -> str:
    """Normalize labels used for tags, genres, developers and publishers."""

    cleaned = clean_text(value)
    return cleaned.lower()


def normalize_list(values: Iterable[object] | None) -> list[str]:
    """Clean, normalize and de-duplicate a list of string-like values."""

    if not values:
        return []

    normalized: list[str] = []
    seen: set[str] = set()

    for item in values:
        label = normalize_label(item)
        if not label or label in seen:
            continue
        seen.add(label)
        normalized.append(label)

    return normalized


def list_to_pipe(values: Iterable[str] | None) -> str:
    """Serialize a list as a pipe-separated string."""

    if not values:
        return ""
    return " | ".join(value for value in values if value)


def pipe_to_list(value: object) -> list[str]:
    """Deserialize a pipe-separated string into a list."""

    text = clean_text(value)
    if not text:
        return []
    parts = [clean_text(part) for part in text.split("|")]
    return [part for part in parts if part]


def json_default(value: object) -> str:
    """Fallback serializer used for JSON exports."""

    if isinstance(value, Path):
        return str(value)
    return str(value)


def safe_json_dump(data: object) -> str:
    """Serialize data to JSON using the project defaults."""

    return json.dumps(data, ensure_ascii=False, indent=2, default=json_default)


def build_store_url(appid: int, language: str) -> str:
    """Build a Steam store page URL for a given appid."""

    return f"https://store.steampowered.com/app/{appid}/?l={language}"


def extract_tags_from_html(html: str) -> list[str]:
    """Extract popular tags from a Steam store page HTML snippet."""

    matches = re.findall(r'class="app_tag[^\"]*"[^>]*>([^<]+)</a>', html, flags=re.IGNORECASE)
    cleaned = [normalize_label(match) for match in matches]
    return normalize_list(cleaned)

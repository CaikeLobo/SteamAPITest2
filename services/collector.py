"""Collection workflow that fetches Steam data and stores it in SQLite."""

from __future__ import annotations

import logging
from typing import Any

from models.game import GameRecord
from services.database import SteamDatabase
from services.steam_api import SteamAPI
from utils.helpers import clean_text, normalize_list


class SteamCollector:
    """Coordinates the Steam API client and the persistence layer."""

    def __init__(self, api: SteamAPI, database: SteamDatabase) -> None:
        self.api = api
        self.database = database
        self.logger = logging.getLogger(self.__class__.__name__)

    def collect(self, limit: int = 100) -> int:
        """Collect the ranked games, enrich them and store the results."""

        self.database.initialize()
        ranked_games = self.api.get_most_played_games(limit=limit)
        stored_count = 0

        for ranked_game in ranked_games:
            appid = ranked_game["appid"]
            try:
                details = self.api.get_app_details(appid)
                tags = self.api.get_tags(appid)
                record = self._build_record(ranked_game, details, tags)
                self.database.upsert_game(record)
                stored_count += 1
            except Exception as exc:  # noqa: BLE001
                self.logger.exception("Failed to process appid %s: %s", appid, exc)

        return stored_count

    def _build_record(
        self,
        ranked_game: dict[str, Any],
        details: dict[str, Any],
        tags: list[str],
    ) -> GameRecord:
        nome = clean_text(ranked_game.get("nome")) or clean_text(details.get("name"))
        jogadores = int(ranked_game.get("jogadores", 0))

        developer = self._extract_first(details, "developers", "desenvolvedor")
        publisher = self._extract_first(details, "publishers", "publicadora")
        release_date = self._extract_release_date(details)
        genres = self._extract_names(details.get("genres"), "description")

        if not developer:
            self.logger.warning("Missing developer for appid %s", ranked_game.get("appid"))
        if not publisher:
            self.logger.warning("Missing publisher for appid %s", ranked_game.get("appid"))
        if not release_date:
            self.logger.warning("Missing release date for appid %s", ranked_game.get("appid"))
        if not genres:
            self.logger.warning("Missing genres for appid %s", ranked_game.get("appid"))

        return GameRecord(
            appid=int(ranked_game.get("appid", 0)),
            nome=nome,
            jogadores=jogadores,
            desenvolvedor=developer,
            publicadora=publisher,
            data_lancamento=release_date,
            generos=genres,
            tags=normalize_list(tags),
        )

    @staticmethod
    def _extract_first(details: dict[str, Any], key: str, fallback_key: str) -> str:
        values = details.get(key)
        if isinstance(values, list) and values:
            return clean_text(values[0])
        fallback = details.get(fallback_key, "")
        return clean_text(fallback)

    @staticmethod
    def _extract_release_date(details: dict[str, Any]) -> str:
        release_date = details.get("release_date", {})
        if isinstance(release_date, dict):
            return clean_text(release_date.get("date", ""))
        return clean_text(release_date)

    @staticmethod
    def _extract_names(values: Any, key: str) -> list[str]:
        if not isinstance(values, list):
            return []
        return normalize_list(item.get(key) for item in values if isinstance(item, dict))

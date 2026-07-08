"""Steam HTTP client used to collect games and metadata."""

from __future__ import annotations

import logging
from typing import Any

import requests

from utils.config import REQUEST_TIMEOUT, STEAM_COUNTRY, STEAM_LANGUAGE
from utils.helpers import build_store_url, extract_tags_from_html


class SteamAPIError(RuntimeError):
    """Raised when a Steam endpoint cannot be read successfully."""


class SteamAPI:
    """Client for the public Steam endpoints used by the project."""

    def __init__(self, timeout: float = REQUEST_TIMEOUT) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0 Safari/537.36"
                )
            }
        )

    def get_most_played_games(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return the most played Steam games with current player counts."""

        url = "https://api.steampowered.com/ISteamChartsService/GetGamesByConcurrentPlayers/v1/"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()

        candidates = payload.get("response", {}).get("ranks") or payload.get("ranks") or payload.get("results")
        if not candidates:
            raise SteamAPIError("Steam charts response did not contain ranked games.")

        games: list[dict[str, Any]] = []
        for item in candidates[:limit]:
            appid = self._safe_int(item.get("appid") or item.get("appid", 0))
            jogadores = self._extract_player_count(item)
            nome = item.get("name") or item.get("appid_name") or item.get("title") or ""
            if not appid:
                self.logger.warning("Skipping malformed ranked entry: %s", item)
                continue
            games.append({"appid": appid, "nome": nome, "jogadores": jogadores})

        return games

    def get_app_details(self, appid: int) -> dict[str, Any]:
        """Fetch developer, publisher, release date and genres for one app."""

        url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l={STEAM_LANGUAGE}&cc={STEAM_COUNTRY}"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        app_payload = payload.get(str(appid), {})
        if not app_payload.get("success"):
            raise SteamAPIError(f"Steam appdetails request failed for appid {appid}.")
        return app_payload.get("data", {})

    def get_current_players(self, appid: int) -> int:
        """Fetch the number of current players for one app."""

        url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid}"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        return self._safe_int(payload.get("response", {}).get("player_count", 0))

    def get_tags(self, appid: int) -> list[str]:
        """Fetch the popular user tags from a Steam store page."""

        url = build_store_url(appid, STEAM_LANGUAGE)
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        tags = extract_tags_from_html(response.text)
        if not tags:
            self.logger.warning("No tags found for appid %s", appid)
        return tags

    @staticmethod
    def _safe_int(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _extract_player_count(item: dict[str, Any]) -> int:
        for key in ("concurrent_in_game", "current_players", "players", "player_count"):
            if key in item:
                try:
                    return int(item[key])
                except (TypeError, ValueError):
                    return 0
        return 0

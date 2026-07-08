"""Entry point for the Steam Top 100 Tags Analyzer."""

from __future__ import annotations

import logging

from services.analyzer import SteamAnalyzer
from services.collector import SteamCollector
from services.database import SteamDatabase
from services.steam_api import SteamAPI
from utils.config import DATABASE_PATH, LOG_DIR, OUTPUT_DIR, TOP_LIMIT
from utils.helpers import ensure_directory


def configure_logging() -> None:
    """Configure console and file logging."""

    ensure_directory(LOG_DIR)
    log_file = LOG_DIR / "app.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def print_summary(stats: dict[str, object], collected_count: int) -> None:
    """Print a concise execution summary to the terminal."""

    top_tags = stats["top_tags"]
    top_genres = stats["top_genres"]
    most_played = stats["most_played_games"]

    print("\nResumo da coleta e analise")
    print(f"Jogos armazenados: {collected_count}")
    print(f"Media de tags por jogo: {stats['average_tags_per_game']}")
    print(f"Jogos sem tags: {stats['games_without_tags']}")

    print("\nTop 5 tags:")
    print(top_tags.head(5).to_string(index=False))

    print("\nTop 5 generos:")
    print(top_genres.head(5).to_string(index=False))

    print("\nJogos com mais jogadores simultaneos:")
    print(most_played.to_string(index=False))


def main() -> None:
    """Run the full pipeline: collect, store, analyze and export."""

    configure_logging()
    ensure_directory(DATABASE_PATH.parent)
    ensure_directory(OUTPUT_DIR)

    logger = logging.getLogger("main")
    logger.info("Starting Steam Top 100 Tags Analyzer")

    database = SteamDatabase(DATABASE_PATH)
    api = SteamAPI()
    collector = SteamCollector(api, database)
    analyzer = SteamAnalyzer(database)

    collected_count = collector.collect(limit=TOP_LIMIT)
    stats = analyzer.run()
    print_summary(stats, collected_count)

    logger.info("Analysis finished successfully")


if __name__ == "__main__":
    main()

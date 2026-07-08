"""SQLite persistence layer for collected Steam games."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pandas as pd

from models.game import GameRecord
from utils.helpers import list_to_pipe


class SteamDatabase:
    """Encapsulates SQLite operations for the project."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """Open a SQLite connection with row factory support."""

        connection = sqlite3.connect(self.database_path)
        try:
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        """Create the SQLite table if it does not exist yet."""

        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    appid INTEGER NOT NULL UNIQUE,
                    nome TEXT NOT NULL,
                    jogadores INTEGER NOT NULL DEFAULT 0,
                    desenvolvedor TEXT NOT NULL DEFAULT '',
                    publicadora TEXT NOT NULL DEFAULT '',
                    data_lancamento TEXT NOT NULL DEFAULT '',
                    generos TEXT NOT NULL DEFAULT '',
                    tags TEXT NOT NULL DEFAULT ''
                )
                """
            )
            connection.commit()

    def upsert_game(self, game: GameRecord) -> None:
        """Insert or update one game by appid."""

        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO games (
                    appid, nome, jogadores, desenvolvedor, publicadora,
                    data_lancamento, generos, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(appid) DO UPDATE SET
                    nome = excluded.nome,
                    jogadores = excluded.jogadores,
                    desenvolvedor = excluded.desenvolvedor,
                    publicadora = excluded.publicadora,
                    data_lancamento = excluded.data_lancamento,
                    generos = excluded.generos,
                    tags = excluded.tags
                """,
                (
                    game.appid,
                    game.nome,
                    game.jogadores,
                    game.desenvolvedor,
                    game.publicadora,
                    game.data_lancamento,
                    list_to_pipe(game.generos),
                    list_to_pipe(game.tags),
                ),
            )
            connection.commit()

    def fetch_games(self) -> pd.DataFrame:
        """Load all stored games into a Pandas DataFrame."""

        with self.connect() as connection:
            frame = pd.read_sql_query("SELECT * FROM games ORDER BY jogadores DESC", connection)
        return frame

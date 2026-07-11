"""Analysis routines for the collected Steam dataset."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from services.database import SteamDatabase
from utils.config import OUTPUT_DIR, TOP_LIMIT
from utils.helpers import clean_text, ensure_directory, pipe_to_list, safe_json_dump


class SteamAnalyzer:
    """Loads the stored data, computes statistics and exports outputs."""

    def __init__(self, database: SteamDatabase, output_dir: Path = OUTPUT_DIR) -> None:
        self.database = database
        self.output_dir = output_dir

    def run(self) -> dict[str, Any]:
        """Execute the full analysis pipeline."""

        ensure_directory(self.output_dir)
        frame = self.database.fetch_games()
        if frame.empty:
            raise RuntimeError("No data available in the SQLite database.")

        cleaned = self._clean_frame(frame)
        stats = self._build_statistics(cleaned)
        self._export_games_list(frame)
        self._export_tags(stats["top_tags"])
        self._plot_top_tags(stats["top_tags"])
        return stats

    def _clean_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Prepare the data for analysis."""

        cleaned = frame.copy()
        for column in cleaned.columns:
            if cleaned[column].dtype == object:
                cleaned[column] = cleaned[column].fillna("").map(clean_text)

        cleaned = cleaned.dropna(subset=["appid", "nome"])
        cleaned = cleaned[cleaned["nome"].astype(str).str.strip() != ""]
        cleaned["tags_list"] = cleaned["tags"].map(pipe_to_list)
        cleaned["generos_list"] = cleaned["generos"].map(pipe_to_list)
        return cleaned

    def _build_statistics(self, frame: pd.DataFrame) -> dict[str, Any]:
        """Compute all requested statistics from the cleaned dataset."""

        tag_series = frame["tags_list"].explode().dropna()
        tag_series = tag_series[tag_series.astype(str).str.strip() != ""]
        genre_series = frame["generos_list"].explode().dropna()
        genre_series = genre_series[genre_series.astype(str).str.strip() != ""]

        top_tags = tag_series.value_counts().head(20).reset_index()
        top_tags.columns = ["tag", "frequencia"]

        top_genres = genre_series.value_counts().head(10).reset_index()
        top_genres.columns = ["genero", "frequencia"]

        tag_counts_per_game = frame["tags_list"].map(len)
        top_developers = self._count_non_empty(frame, "desenvolvedor", "developer")
        top_publishers = self._count_non_empty(frame, "publicadora", "publisher")

        stats = {
            "top_tags": top_tags,
            "top_genres": top_genres,
            "average_tags_per_game": round(float(tag_counts_per_game.mean()), 2),
            "games_by_developer": top_developers,
            "games_by_publisher": top_publishers,
            "games_without_tags": int((tag_counts_per_game == 0).sum()),
            "most_played_games": frame.sort_values("jogadores", ascending=False)
            .loc[:, ["appid", "nome", "jogadores"]]
            .head(10)
            .reset_index(drop=True),
        }

        return stats

    def _count_non_empty(self, frame: pd.DataFrame, column: str, label: str) -> pd.DataFrame:
        """Count non-empty values for the requested column."""

        subset = frame[[column]].copy()
        subset[column] = subset[column].map(clean_text)
        subset = subset[subset[column] != ""]
        counts = subset[column].value_counts().reset_index()
        counts.columns = [label, "quantidade"]
        return counts

    def _export_tags(self, top_tags: pd.DataFrame) -> None:
        """Write the top tags summary as CSV and JSON files."""

        csv_path = self.output_dir / "tags.csv"
        json_path = self.output_dir / "tags.json"

        top_tags.to_csv(csv_path, index=False)
        json_path.write_text(safe_json_dump(top_tags.to_dict(orient="records")), encoding="utf-8")

    def _export_games_list(self, frame: pd.DataFrame) -> None:
        """Write a text file with the top collected games."""

        txt_path = self.output_dir / "games.txt"
        top_games = frame.sort_values("jogadores", ascending=False).head(TOP_LIMIT)

        lines = [
            f"{index + 1}. {row.nome} (appid: {int(row.appid)}) - {int(row.jogadores)} jogadores"
            for index, row in top_games.reset_index(drop=True).iterrows()
        ]
        txt_path.write_text("\n".join(lines), encoding="utf-8")

    def _plot_top_tags(self, top_tags: pd.DataFrame) -> None:
        """Generate a horizontal bar chart for the top 20 tags."""

        if top_tags.empty:
            return

        plot_path = self.output_dir / "tags.png"
        plot_frame = top_tags.sort_values("frequencia", ascending=True)

        plt.figure(figsize=(12, 10))
        plt.barh(plot_frame["tag"], plot_frame["frequencia"], color="#1b2838")
        plt.title("Top 20 Tags Mais Frequentes")
        plt.xlabel("Frequência")
        plt.ylabel("Tag")
        plt.tight_layout()
        plt.savefig(plot_path, dpi=160)
        plt.close()

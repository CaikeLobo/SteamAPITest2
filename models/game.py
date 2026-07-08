"""Dataclasses used by the Steam Top 100 Tags Analyzer."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class GameRecord:
    """Represents one Steam game collected for analysis."""

    appid: int
    nome: str
    jogadores: int
    desenvolvedor: str = ""
    publicadora: str = ""
    data_lancamento: str = ""
    generos: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

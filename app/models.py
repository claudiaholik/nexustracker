"""Modelos de dominio del visor.

Son la versión "limpia" de lo que devuelve la API de Carde.io: solo los
campos que el visor necesita, con nombres claros. Igual que en Kaori,
el resto de la app trabaja con estos modelos y no con el JSON crudo.
"""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Player:
    nick: str               # El nick del jugador. NUNCA mostramos el nombre real.
    wins: int = 0
    losses: int = 0
    draws: int = 0
    points: int = 0

    @property
    def record(self) -> str:
        """Récord en formato V-D-E, por ejemplo '2-1-0'."""
        return f"{self.wins}-{self.losses}-{self.draws}"


@dataclass
class Match:
    table: int | None
    player_a: Player
    player_b: Player | None     # None cuando es un bye (jugador sin rival)
    status: str                 # "IN_PROGRESS", "COMPLETE"...
    winner_nick: str | None = None
    is_draw: bool = False
    score: str | None = None    # "2-1", solo si la partida ha terminado

    @property
    def is_bye(self) -> bool:
        return self.player_b is None

    @property
    def is_finished(self) -> bool:
        return self.status == "COMPLETE"

    def involves(self, text: str) -> bool:
        """True si alguno de los dos nicks contiene `text` (sin mayúsculas)."""
        text = text.casefold().strip()
        nicks = [self.player_a.nick] + ([self.player_b.nick] if self.player_b else [])
        return any(text in nick.casefold() for nick in nicks)


@dataclass
class Round:
    id: int
    number: int
    status: str             # "IN_PROGRESS", "COMPLETE"...
    pairings_ready: bool    # True si Carde.io ya ha generado los emparejamientos


@dataclass
class Event:
    id: int
    name: str
    store: str
    start: datetime
    lifecycle: str                          # "EVENT_FINISHED", etc.
    rounds: list[Round] = field(default_factory=list)
    timer_end: datetime | None = None       # Cuándo acaba la ronda en curso
    timer_running: bool = False

    @property
    def current_round(self) -> Round | None:
        """La última ronda con emparejamientos ya publicados.

        Es la que interesa en una Nexus Night: la que se está jugando ahora
        o, si el torneo ha acabado, la última que se jugó.
        """
        ready = [r for r in self.rounds if r.pairings_ready]
        return max(ready, key=lambda r: r.number) if ready else None

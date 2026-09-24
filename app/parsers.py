"""Traducen el JSON de la API de Carde.io a nuestros modelos.

Son funciones puras: reciben un dict y devuelven modelos, sin red de por
medio. Por eso se pueden testear con los JSON de ejemplo de tests/fixtures.
"""
from datetime import datetime

from app.models import Event, Match, Player, Round


def _parse_dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def parse_event(data: dict) -> Event:
    """JSON de /events/{id}/ -> Event."""
    rounds = [
        Round(
            id=r["id"],
            number=r["round_number"],
            status=r["status"],
            pairings_ready=r.get("pairings_status") == "GENERATED",
        )
        for phase in data.get("tournament_phases", [])
        for r in phase.get("rounds", [])
    ]
    return Event(
        id=data["id"],
        name=data["name"],
        store=(data.get("store") or {}).get("name", ""),
        start=_parse_dt(data["start_datetime"]),
        lifecycle=(data.get("settings") or {}).get("event_lifecycle_status", ""),
        rounds=rounds,
        timer_end=_parse_dt(data.get("timer_end_datetime")),
        timer_running=bool(data.get("timer_is_running")),
    )


def _parse_player(relationship: dict) -> Player:
    """Un elemento de `player_match_relationships` -> Player.

    Ojo: el nick está en `user_event_status.best_identifier`. El
    `player.best_identifier` es el nombre real con la inicial del apellido,
    y ese no lo queremos en una pantalla pública.
    """
    status = relationship["user_event_status"]
    return Player(
        nick=status["best_identifier"],
        wins=status.get("matches_won", 0),
        losses=status.get("matches_lost", 0),
        draws=status.get("matches_drawn", 0),
        points=status.get("total_match_points", 0),
    )


def parse_match(data: dict) -> Match:
    """Un elemento de `results` de /tournament-rounds/{id}/matches/paginated/ -> Match."""
    relationships = sorted(data["player_match_relationships"], key=lambda r: r["player_order"])
    players = [_parse_player(r) for r in relationships]

    # `winning_player` es un id de usuario, no un nick: hay que buscarlo.
    winner_nick = None
    for rel, player in zip(relationships, players):
        if rel["player"]["id"] == data.get("winning_player"):
            winner_nick = player.nick

    is_draw = bool(data.get("match_is_intentional_draw") or data.get("match_is_unintentional_draw"))
    score = None
    if data.get("status") == "COMPLETE" and not data.get("match_is_bye"):
        score = f"{data.get('games_won_by_winner', 0)}-{data.get('games_won_by_loser', 0)}"

    return Match(
        table=data.get("table_number"),
        player_a=players[0],
        player_b=players[1] if len(players) > 1 else None,
        status=data.get("status", ""),
        winner_nick=winner_nick,
        is_draw=is_draw,
        score=score,
    )

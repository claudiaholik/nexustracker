"""Cliente HTTP de la API pública de Carde.io para Riftbound.

Solo lectura y sin login: son los mismos endpoints que usa el locator
(locator.riftbound.uvsgames.com) para mostrar los eventos.
"""
import time

import httpx

from app.models import Event, Match
from app.parsers import parse_event, parse_match

BASE_URL = "https://api.cloudflare.riftbound.uvsgames.com/hydraproxy/api/v2"

# Muchos móviles pueden abrir el visor a la vez. Para no bombardear la API
# de Carde.io, guardamos cada respuesta unos segundos y la reutilizamos.
CACHE_SECONDS = 15


class CardeioClient:
    def __init__(self, http: httpx.AsyncClient | None = None):
        self._http = http or httpx.AsyncClient(base_url=BASE_URL, timeout=10)
        self._cache: dict[str, tuple[float, object]] = {}

    async def _get_json(self, path: str, params: dict | None = None):
        key = f"{path}?{params}"
        cached = self._cache.get(key)
        if cached and time.monotonic() - cached[0] < CACHE_SECONDS:
            return cached[1]

        response = await self._http.get(path, params=params)
        response.raise_for_status()
        data = response.json()
        self._cache[key] = (time.monotonic(), data)
        return data

    async def get_event(self, event_id: int) -> Event:
        data = await self._get_json(f"/events/{event_id}/")
        return parse_event(data)

    async def get_matches(self, round_id: int) -> list[Match]:
        """Todos los emparejamientos de una ronda, recorriendo todas las páginas."""
        matches: list[Match] = []
        page = 1
        while page:
            data = await self._get_json(
                f"/tournament-rounds/{round_id}/matches/paginated/",
                params={"page": page, "page_size": 50},
            )
            matches += [parse_match(m) for m in data["results"]]
            page = data.get("next_page_number")  # None en la última página
        return sorted(matches, key=lambda m: (m.table is None, m.table or 0))

    # TODO(Clau): get_standings(event_id) -> list[Player]
    #   Endpoint: /events/{event_id}/registrations/  (paginado igual que los matches)
    #   Pista: cada elemento de "results" tiene "best_identifier" (el nick),
    #   "matches_won", "matches_lost", "matches_drawn", "total_match_points"
    #   y "final_place_in_standings". Mira cómo está hecho get_matches.

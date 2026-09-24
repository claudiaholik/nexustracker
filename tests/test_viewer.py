"""Tests del visor, sin red: la API de Carde.io se simula con los JSON de fixtures/."""
import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app import main
from app.client import BASE_URL, CardeioClient
from app.parsers import parse_event, parse_match

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def fake_api(request: httpx.Request) -> httpx.Response:
    """Hace de servidor de Carde.io: devuelve el fixture según la URL."""
    path = request.url.path
    if path.endswith("/events/111/"):
        return httpx.Response(200, json=load("event.json"))
    if path.endswith("/tournament-rounds/902/matches/paginated/"):
        page = request.url.params.get("page", "1")
        return httpx.Response(200, json=load(f"matches_page{page}.json"))
    return httpx.Response(404)


@pytest.fixture
def web():
    """App con el cliente apuntando a la API falsa."""
    http = httpx.AsyncClient(base_url=BASE_URL, transport=httpx.MockTransport(fake_api))
    main.client = CardeioClient(http)
    return TestClient(main.app)


# --- Parsers -----------------------------------------------------------------

def test_current_round_is_last_with_pairings():
    event = parse_event(load("event.json"))
    assert event.current_round.number == 2  # la 3 aún no tiene pairings


def test_match_uses_nick_not_real_name():
    match = parse_match(load("matches_page1.json")["results"][0])
    assert match.player_a.nick == "KitsuneAhri"
    assert "Ana" not in match.player_a.nick


def test_finished_match_has_winner_and_score():
    match = parse_match(load("matches_page1.json")["results"][0])
    assert match.winner_nick == "KitsuneAhri"
    assert match.score == "2-1"


def test_draw_and_bye():
    draw, bye = (parse_match(m) for m in load("matches_page2.json")["results"])
    assert draw.is_draw and draw.winner_nick is None
    assert bye.is_bye and bye.score is None


def test_search_is_case_insensitive():
    match = parse_match(load("matches_page1.json")["results"][0])
    assert match.involves("kitsune")
    assert match.involves("teemo")
    assert not match.involves("jinx")


# --- Rutas -------------------------------------------------------------------

def test_pairings_page_reads_all_pages_sorted_by_table(web):
    html = web.get("/e/111").text
    assert "Ronda 2" in html
    assert html.index("Jinxed") < html.index("KitsuneAhri")  # mesa 29 antes que 30
    assert "SoloBye" in html  # viene de la página 2


def test_real_names_never_shown(web):
    html = web.get("/e/111").text
    for real_name in ["Ana R", "Beto S", "Carla T", "Gus X"]:
        assert real_name not in html


def test_search_filters_matches(web):
    html = web.get("/e/111", params={"q": "volibear"}).text
    assert "VolibearHug" in html
    assert "KitsuneAhri" not in html


def test_home_accepts_full_locator_url(web):
    response = web.get(
        "/", params={"event": "https://locator.riftbound.uvsgames.com/events/111"},
        follow_redirects=False,
    )
    assert response.headers["location"] == "/e/111"


def test_unknown_event_returns_404(web):
    assert web.get("/e/999").status_code == 404


def test_tv_mode(web):
    html = web.get("/e/111/tv").text
    assert 'class="tv"' in html and "VolibearHug" in html

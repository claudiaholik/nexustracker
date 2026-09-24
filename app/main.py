"""Riftbuilder — visor de pairings para las Nexus Nights.

Arranque en local:
    uvicorn app.main:app --reload --host 0.0.0.0
y abre http://localhost:8000
"""
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.client import CardeioClient

BASE_DIR = Path(__file__).parent

app = FastAPI(title="Riftbuilder")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
client = CardeioClient()


async def _load(event_id: int):
    """Carga el evento y los pairings de su ronda actual."""
    try:
        event = await client.get_event(event_id)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=404, detail="No encuentro ese evento en Carde.io") from exc

    current = event.current_round
    matches = await client.get_matches(current.id) if current else []
    return event, current, matches


def _seconds_left(event) -> int | None:
    if not event.timer_end:
        return None
    return max(0, int((event.timer_end - datetime.now(timezone.utc)).total_seconds()))


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, event: str | None = None):
    """Portada: un campo para pegar el id o la URL del evento."""
    if event:
        # Acepta tanto "948273" como "https://locator.../events/948273"
        event_id = event.rstrip("/").split("/")[-1]
        if event_id.isdigit():
            return RedirectResponse(f"/e/{event_id}")
    return templates.TemplateResponse(request, "home.html", {"error": bool(event)})


@app.get("/e/{event_id}", response_class=HTMLResponse)
async def pairings(request: Request, event_id: int, q: str = ""):
    """Vista móvil: pairings de la ronda actual, con buscador por nick."""
    event, current, matches = await _load(event_id)
    if q:
        matches = [m for m in matches if m.involves(q)]
    return templates.TemplateResponse(
        request,
        "pairings.html",
        {
            "event": event,
            "round": current,
            "matches": matches,
            "q": q,
            "seconds_left": _seconds_left(event),
        },
    )


@app.get("/e/{event_id}/tv", response_class=HTMLResponse)
async def tv(request: Request, event_id: int):
    """Vista tele: todo en grande, sin buscador."""
    event, current, matches = await _load(event_id)
    return templates.TemplateResponse(
        request,
        "tv.html",
        {"event": event, "round": current, "matches": matches, "seconds_left": _seconds_left(event)},
    )


# TODO(Clau): ruta /e/{event_id}/standings con la clasificación.
#   1. Termina get_standings() en client.py.
#   2. Crea templates/standings.html copiando la estructura de pairings.html.
#   3. Añade un enlace "Clasificación" en la cabecera de pairings.html.

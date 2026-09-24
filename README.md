# Riftbuilder

Visor de pairings para torneos de **Riftbound** organizados con Carde.io, pensado para el móvil de los jugadores en las Nexus Nights.

Pegas el enlace del evento del locator y ves la ronda actual: tu mesa, tu rival, el temporizador y los resultados, con un buscador por nick. Se actualiza solo cada 30 segundos. También tiene un **modo tele** para proyectarlo en la tienda.

> Solo muestra **nicks**. La API también devuelve el nombre real con la inicial del apellido, y el visor lo descarta a propósito.

## Stack

- Python 3.11+ · FastAPI · Jinja2 · httpx
- Sin base de datos: lee en vivo de la API pública de Carde.io, con una caché de 15 s para no saturarla cuando hay muchos móviles abiertos
- Tests con pytest sin red: la API se simula con los JSON de `tests/fixtures/`

## Arrancarlo en Windows

```powershell
cd riftbuilder
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0
```

Abre <http://localhost:8000> y pega, por ejemplo, `https://locator.riftbound.uvsgames.com/events/948273`.

**Desde el móvil**, en la misma wifi: `http://<IP-del-portátil>:8000`. Para ver la IP del portátil, ejecuta `ipconfig` y busca la línea "Dirección IPv4". Si el móvil no conecta, lo más probable es que el firewall de Windows esté bloqueando el puerto 8000.

## Tests

```powershell
pytest
```

## Cómo está organizado

```
app/
  models.py    Modelos de dominio: Event, Round, Match, Player
  parsers.py   JSON de Carde.io -> modelos (funciones puras, fáciles de testear)
  client.py    Llamadas HTTP a la API, paginación y caché
  main.py      Rutas web: portada, /e/{id} (móvil) y /e/{id}/tv (tele)
  templates/   HTML con Jinja2
  static/      CSS y el JS del temporizador y la recarga automática
tests/
  fixtures/    JSON de ejemplo con la forma real de la API y jugadores inventados
```

Es la misma separación que en Kaori: el JSON de la API y el modelo que usa la app son cosas distintas, y los parsers traducen de uno a otro.

## Endpoints de Carde.io que usa

Base: `https://api.cloudflare.riftbound.uvsgames.com/hydraproxy/api/v2`

| Endpoint | Qué da |
|---|---|
| `/events/{id}/` | Evento, temporizador y lista de rondas |
| `/tournament-rounds/{round_id}/matches/paginated/?page=N` | Emparejamientos y resultados de una ronda |
| `/events/{id}/registrations/?page=N` | Jugadores y clasificación (todavía sin usar) |

Es una API interna, no documentada: puede cambiar sin avisar. Si algo deja de funcionar, lo primero es comparar su respuesta con los fixtures.

## Pendiente (para ti)

- [ ] **Clasificación**: tienes los pasos en los `TODO(Clau)` de `client.py` y `main.py`
- [ ] Probarlo contra un evento real y guardar una respuesta real, con los nicks cambiados, como fixture nuevo
- [ ] Publicarlo en algún sitio para que los jugadores lo abran sin depender de tu portátil (Render, Railway o Fly.io tienen plan gratuito)
- [ ] Dar el enlace de un evento concreto con un QR impreso en la mesa

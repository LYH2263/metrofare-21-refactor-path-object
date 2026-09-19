from fastapi import APIRouter

from app.routers import (
    dashboard,
    disruptions,
    edges,
    fares,
    history,
    quote,
    settings,
    stations,
)

api = APIRouter(prefix="/api")
for r in (dashboard, stations, edges, fares, quote, history, settings, disruptions):
    api.include_router(r.router)

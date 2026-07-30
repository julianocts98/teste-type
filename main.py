"""Application entry point for the Galactic Conflict API."""

from fastapi import FastAPI

from galaxy.database import initialize_database
from galaxy.routers import characters, missions, planets, starships
from galaxy.seeds import seed_database


app = FastAPI(
    title="Galactic Conflict API",
    version="1.1.0",
    description="An intentionally flawed Star Wars API for QA automation practice.",
)
app.include_router(planets.router)
app.include_router(characters.router)
app.include_router(missions.router)
app.include_router(starships.router)


@app.on_event("startup")
def startup() -> None:
    initialize_database()
    seed_database()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "operational", "service": "galactic-conflict-api"}

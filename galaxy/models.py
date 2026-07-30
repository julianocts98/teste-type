"""SQLAlchemy models for the Galactic Conflict API."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from galaxy.database import Base


class Planet(Base):
    __tablename__ = "planets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    terrain: Mapped[str] = mapped_column(String(100))
    population: Mapped[int] = mapped_column(Integer)
    characters: Mapped[list["Character"]] = relationship(back_populates="homeworld")


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    species: Mapped[str] = mapped_column(String(80))
    side: Mapped[str] = mapped_column(String(20))
    force_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    homeworld_id: Mapped[int | None] = mapped_column(ForeignKey("planets.id"), nullable=True)
    homeworld: Mapped[Planet | None] = relationship(back_populates="characters")


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    target: Mapped[str] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(String(20), default="planned")
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("characters.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Starship(Base):
    __tablename__ = "starships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    model: Mapped[str] = mapped_column(String(120))
    manufacturer: Mapped[str] = mapped_column(String(120))
    crew: Mapped[int] = mapped_column(Integer)
    fuel_level: Mapped[int] = mapped_column(Integer, default=100)
    hyperdrive_rating: Mapped[float] = mapped_column(default=1.0)


class SeedState(Base):
    """Records one-time initialization work performed for a database."""

    __tablename__ = "seed_state"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)

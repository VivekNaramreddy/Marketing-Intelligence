from datetime import datetime, timezone

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .storage import Base


class Workspace(Base):
    __tablename__ = 'workspaces'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    primary_brand: Mapped[str | None]
    competitors: Mapped[list | None] = mapped_column(JSON, nullable=True)


class ImportBatch(Base):
    __tablename__ = 'imports'
    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey('workspaces.id'))
    filename: Mapped[str]
    created_at: Mapped[str] = mapped_column(default=lambda: datetime.now(timezone.utc).isoformat())
    raw_rows: Mapped[list] = mapped_column(JSON)


class Observation(Base):
    __tablename__ = 'observations'
    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey('workspaces.id'))
    import_id: Mapped[int] = mapped_column(ForeignKey('imports.id'))
    source_row: Mapped[int]
    brand: Mapped[str]
    platform: Mapped[str]
    date: Mapped[str | None]
    followers: Mapped[float | None]
    engagement_rate: Mapped[float | None]
    views: Mapped[float | None]
    likes: Mapped[float | None]
    comments: Mapped[float | None]
    shares: Mapped[float | None]
    posts: Mapped[float | None]

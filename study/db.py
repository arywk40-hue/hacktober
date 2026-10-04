"""Persistent SQLite records for local subjects, documents, and verifier audits."""

from contextlib import contextmanager
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Integer, String, UniqueConstraint, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


def uid():
    return uuid4().hex


def now():
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Record(Base):
    __tablename__ = "records"
    __table_args__ = (UniqueConstraint("kind", "scope", "key", name="record_key"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=uid)
    kind: Mapped[str] = mapped_column(String(30), index=True)
    scope: Mapped[str] = mapped_column(String(128), index=True)
    key: Mapped[str] = mapped_column(String(160))
    payload: Mapped[dict] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __mapper_args__ = {"version_id_col": version}


class Database:
    def __init__(self, url):
        self.engine = create_engine(
            url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {}
        )
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)

    def create(self):
        Base.metadata.create_all(self.engine)

    @contextmanager
    def transaction(self):
        with self.sessions.begin() as session:
            yield session

    @staticmethod
    def get(session, kind, ident, lock=False):
        query = select(Record).where(Record.id == ident, Record.kind == kind)
        if lock:
            query = query.with_for_update()
        row = session.scalar(query)
        if row is None:
            raise LookupError(f"{kind} not found")
        return row

    @staticmethod
    def find(session, kind, scope=None):
        query = select(Record).where(Record.kind == kind).order_by(Record.created_at, Record.id)
        if scope is not None:
            query = query.where(Record.scope == scope)
        return list(session.scalars(query))

    @staticmethod
    def add(session, kind, scope, payload, key=None, ident=None):
        ident = ident or uid()
        row = Record(id=ident, kind=kind, scope=scope, key=key or ident, payload=payload)
        session.add(row)
        session.flush()
        return row


def public(row):
    return {"id": row.id, **row.payload}

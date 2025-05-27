import uuid
from datetime import datetime
from archilog.config import config

from sqlalchemy import create_engine,Table, MetaData, Column, String, Float, Uuid, select, DateTime, func, delete, update

from dataclasses import dataclass

engine = create_engine(config.DATABASE_URL, echo=config.DEBUG)
metadata = MetaData()

entries_table = Table(
    "entries",
    metadata,
    Column("id", Uuid, primary_key = True, default=uuid.uuid4),
    Column("name", String, nullable = False),
    Column("date", DateTime, nullable = False, default=func.now()),
    Column("amount", Float, nullable = False),
    Column("category", String, nullable = True)
)

def init_db():
    metadata.create_all(engine)

@dataclass
class Entry:
    id: uuid.UUID
    name: str
    date : datetime
    amount: float
    category: str | None

def create_entry(name: str, amount: float, category: str | None = None) -> None:
    with engine.begin() as conn:
        stmt = entries_table.insert().values(name=name, amount=amount, category=category)
        result = conn.execute(stmt)


def get_entry(id: uuid.UUID) -> Entry:
    stmt = select(entries_table).where(entries_table.c.id == id)
    with engine.begin() as conn:
        result = conn.execute(stmt)
        entry = result.fetchone()
        if entry:
            return Entry(entry.id, entry.name, entry.date, entry.amount, entry.category)
        else:
            raise Exception("Entry not found")


def get_all_entries() -> list[Entry]:
    stmt = select(entries_table)
    with engine.begin() as conn:
        results = conn.execute(stmt).fetchall()
        return [Entry(*r) for r in results]


def update_entry(id: uuid.UUID, name: str, amount: float, category: str | None) -> None:
    stmt = update(entries_table).where(entries_table.c.id == id).values(name=name, amount=amount, category=category)
    with engine.begin() as conn:
        conn.execute(stmt)


def delete_entry(id: uuid.UUID) -> None:
    stmt = delete(entries_table).where(entries_table.c.id == id)    
    with engine.begin() as conn:
        conn.execute(stmt)
import sqlite3
import uuid

from dataclasses import dataclass
from sqlalchemy import *

db_url = "data.db"
db = None

engine = create_engine("sqlite:///data.db", echo=True)
metadata = MetaData()

entries_table = Table(
    "entries",
    metadata,
    Column("id", String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
    Column("name", String, nullable=False),
    Column("amount", Float, nullable=False),
    Column("category", String, nullable=True)
)

def get_db():
    global db
    if db is None:
        db = sqlite3.connect(db_url)
    return db


def init_db():
    with get_db() as db:
        db.execute("""
            create table entries
            (
                id int primary key not null,
                name text not null,
                amount real not null,
                category text
            )
        """)


@dataclass
class Entry:
    id: uuid.UUID
    name: str
    amount: float
    category: str | None

    @classmethod
    def from_db(cls, id: str, name: str, amount: float, category: str | None):
        return cls(
            uuid.UUID(id),
            name,
            amount,
            category,
        )


def create_entry(name: str, amount: float, category: str | None = None) -> None:
    with engine.begin() as conn:
        stmt = entries_table.insert().values(name=name, amount=amount, category=category)
        result = conn.execute(stmt)


def get_entry(id: uuid.UUID) -> Entry:
    with get_db() as db:
        result = db.execute("select * from entries where id = ?", (id.hex,)).fetchone()
        if result:
            return Entry.from_db(*result)
        else:
            raise Exception("Entry not found")


def get_all_entries() -> list[Entry]:
    with get_db() as db:
        results = db.execute("select * from entries").fetchall()
        return [Entry.from_db(*r) for r in results]


def update_entry(id: uuid.UUID, name: str, amount: float, category: str | None) -> None:
    with get_db() as db:
        db.execute(
            "update entries set name = ?, amount = ?, category = ? where id = ?",
            (name, amount, category, id.hex),
        )


def delete_entry(id: uuid.UUID) -> None:
    with get_db() as db:
        db.execute("delete from entries where id = ?", (id.hex,))

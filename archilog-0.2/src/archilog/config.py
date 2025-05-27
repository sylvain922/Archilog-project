from dataclasses import dataclass
import os

@dataclass
class Config:
    DATABASE_URL: str
    DEBUG: bool

config = Config(
    DATABASE_URL=os.getenv("ARCHILOG_DATABASE_URL", "sqlite:///data.db"),
    DEBUG=os.getenv("ARCHILOG_DEBUG", "False") == "True",
)
"""Configuration: every setting that can change between environments."""
import os


class Config:
    DB_PATH = os.environ.get("DB_PATH", "tasks.db")
    MAX_TITLE_LENGTH = 200

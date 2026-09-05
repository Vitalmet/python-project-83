from collections.abc import Generator
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

from page_analyzer.config import Config


def get_db_connection() -> psycopg2.extensions.connection:
    conn = psycopg2.connect(
        Config.DATABASE_URL,
        cursor_factory=RealDictCursor,
    )
    return conn


@contextmanager
def db_connection() -> Generator:
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def db_cursor() -> Generator:
    with db_connection() as conn:
        cur = conn.cursor()
        try:
            yield cur, conn
        finally:
            cur.close()

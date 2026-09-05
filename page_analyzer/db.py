from collections.abc import Generator
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

from page_analyzer.config import Config


def get_db_connection() -> psycopg2.extensions.connection:
    database_url = Config.DATABASE_URL
    if 'sslmode' not in database_url:
        separator = '&' if '?' in database_url else '?'
        database_url += f'{separator}sslmode=require'
    conn = psycopg2.connect(
        database_url,
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

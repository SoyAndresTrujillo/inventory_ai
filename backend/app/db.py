import os
from pathlib import Path

from dotenv import load_dotenv
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://inventory:inventory@localhost:5433/inventory"
)

pool = ConnectionPool(DATABASE_URL, min_size=1, max_size=10, open=False, kwargs={"row_factory": dict_row})


def init_schema() -> None:
    sql = (Path(__file__).resolve().parent / "schema.sql").read_text()
    with pool.connection() as conn:
        conn.execute(sql)

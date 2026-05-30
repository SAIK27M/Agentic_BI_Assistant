from backend.db.database import get_connection
import pandas as pd


def execute(sql):
    conn = get_connection()
    try:
        conn.execute("PRAGMA query_only = ON")
        return pd.read_sql_query(sql, conn)
    finally:
        conn.close()

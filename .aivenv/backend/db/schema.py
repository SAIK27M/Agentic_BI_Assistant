import re

import pandas as pd

from backend.db.database import get_connection


IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def is_safe_identifier(name):
    return bool(IDENTIFIER_RE.match(name or ""))


def quote_identifier(name):
    if not is_safe_identifier(name):
        raise ValueError(f"Unsafe identifier: {name}")
    return f'"{name}"'


def list_tables():
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
              AND name NOT LIKE '_agent_%'
            ORDER BY name
            """
        ).fetchall()
        return [row[0] for row in rows]
    finally:
        conn.close()


def get_table_schema(table_name):
    table = quote_identifier(table_name)
    conn = get_connection()
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        if not rows:
            raise ValueError(f"Table not found: {table_name}")
        return [{"name": row[1], "type": row[2] or "TEXT"} for row in rows]
    finally:
        conn.close()


def get_schema_context(table_name=None):
    tables = [table_name] if table_name else list_tables()
    lines = []
    for table in tables:
        columns = get_table_schema(table)
        column_text = ", ".join(f"{col['name']} {col['type']}" for col in columns)
        lines.append(f"Table: {table}({column_text})")
        sample_rows = preview_table(table, limit=3)
        if sample_rows:
            lines.append(f"Sample rows: {sample_rows}")
    return "\n".join(lines)


def preview_table(table_name, limit=5):
    table = quote_identifier(table_name)
    conn = get_connection()
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT ?", conn, params=(limit,))
        return df.to_dict(orient="records")
    finally:
        conn.close()


def normalize_dataframe(df):
    normalized = df.copy()

    for column in normalized.columns:
        name = str(column).lower()
        if not any(part in name for part in ["date", "time", "month", "year"]):
            continue

        parsed = pd.to_datetime(normalized[column], errors="coerce", dayfirst=True)
        valid_count = parsed.notna().sum()
        if valid_count >= max(1, int(len(normalized) * 0.8)):
            normalized[column] = parsed.dt.strftime("%Y-%m-%d")

    return normalized


def save_dataframe(table_name, df):
    if not is_safe_identifier(table_name):
        raise ValueError("Use a simple table name with letters, numbers, and underscores.")

    df = normalize_dataframe(df)

    conn = get_connection()
    try:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    finally:
        conn.close()

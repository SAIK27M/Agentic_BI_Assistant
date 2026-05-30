from backend.utils.llm import generate


def clean_sql(sql):
    sql = sql.strip()
    if sql.startswith("```"):
        sql = sql.strip("`").removeprefix("sql").strip()
    return sql.rstrip(";") + ";"


def generate_sql(user_query, schema_context, conversation_context=""):
    prompt = f"""
You are a SQLite expert for a BI assistant.

Database schema:
{schema_context}

Recent conversation context:
{conversation_context or "None"}

User question:
{user_query}

Rules:
- Return only one SQLite SELECT query.
- Use only tables and columns from the schema.
- Quote table and column names with double quotes.
- Date columns are stored as YYYY-MM-DD when uploaded; use that format for date filters.
- Use sample rows to match exact text values.
- Prefer readable aliases for aggregated columns.
- Do not include markdown, explanation, comments, or multiple statements.
"""
    return clean_sql(generate(prompt))

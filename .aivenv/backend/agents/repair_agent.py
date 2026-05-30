from backend.utils.llm import generate
from backend.agents.sql_agent import clean_sql


def repair_sql(user_query, schema_context, failed_sql, error_message):
    prompt = f"""
You repair SQLite SELECT queries for a BI assistant.

Database schema:
{schema_context}

User question:
{user_query}

Failed SQL:
{failed_sql}

Database error:
{error_message}

Return only one corrected SQLite SELECT query. Do not include markdown.
"""
    return clean_sql(generate(prompt))

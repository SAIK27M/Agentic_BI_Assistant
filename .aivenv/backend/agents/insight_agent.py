import json

from backend.utils.llm import generate


def generate_insight(user_query, rows):
    sample_rows = rows[:20]
    if not sample_rows:
        return "No rows matched the question."

    prompt = f"""
You are a concise BI analyst.

User question:
{user_query}

Query result JSON:
{json.dumps(sample_rows, default=str)}

Write 2-3 short business insights. Mention exact values when useful.
"""
    return generate(prompt).strip()

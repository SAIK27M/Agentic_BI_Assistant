import json
import re

from backend.utils.llm import generate


DEFAULT_PLAN = {
    "intent": "answer_question",
    "tools": ["profile", "memory", "sql", "validate", "execute", "chart", "insight"],
    "steps": [
        "Inspect the selected table profile.",
        "Use relevant prior memory if available.",
        "Generate one safe SQLite SELECT query.",
        "Validate and execute the SQL.",
        "Recommend a chart when the result has chartable structure.",
        "Generate a concise insight from the result.",
    ],
}


def _extract_json(text):
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def plan_analysis(question, schema_context, profile_text, memory_text):
    prompt = f"""
You are the planning agent for an agentic BI assistant.

User question:
{question}

Schema and samples:
{schema_context}

Data profile:
{profile_text}

Relevant memory:
{memory_text}

Choose a compact analysis strategy. Return JSON only with:
- intent: short snake_case label
- tools: ordered list chosen from ["profile", "memory", "sql", "validate", "execute", "repair", "chart", "insight"]
- steps: 3 to 6 short natural language steps

Rules:
- Use sql, validate, and execute for data questions.
- Use chart when the user asks for trend, compare, distribution, by date, by category, or when multiple rows are useful.
- Use insight when the user asks why, summarize, explain, analyze, trend, or compare.
- Use repair only if SQL execution fails; include it as a possible tool when the question is complex.
"""
    plan = _extract_json(generate(prompt))
    if not plan:
        return DEFAULT_PLAN

    tools = plan.get("tools") or DEFAULT_PLAN["tools"]
    allowed = {"profile", "memory", "sql", "validate", "execute", "repair", "chart", "insight"}
    plan["tools"] = [tool for tool in tools if tool in allowed] or DEFAULT_PLAN["tools"]
    plan["steps"] = plan.get("steps") or DEFAULT_PLAN["steps"]
    plan["intent"] = plan.get("intent") or DEFAULT_PLAN["intent"]
    return plan

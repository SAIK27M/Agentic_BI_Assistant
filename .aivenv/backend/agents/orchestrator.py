from backend.agents.langchain_tools import invoke_tool
from backend.agents.memory_agent import memory_to_text
from backend.agents.planner_agent import plan_analysis
from backend.agents.profile_agent import profile_to_text
from backend.db.schema import get_schema_context


def run_agentic_query(request):
    schema_context = get_schema_context(request.table)
    profile = invoke_tool("profile_table", table_name=request.table) if request.table else None
    profile_text = profile_to_text(profile) if profile else "No selected table profile."
    memories = invoke_tool("recall_memory", table_name=request.table, limit=5)
    memory_text = memory_to_text(memories)

    try:
        plan = plan_analysis(request.question, schema_context, profile_text, memory_text)
    except Exception as exc:
        plan = {
            "intent": "answer_question",
            "tools": ["profile", "memory", "sql", "validate", "execute", "chart", "insight"],
            "steps": [f"Planner unavailable, using default SQL workflow: {exc}"],
        }

    enriched_context = "\n\n".join(
        [
            schema_context,
            "Data profile:",
            profile_text,
            "Long-term memory:",
            memory_text,
            "Recent conversation context:",
            request.conversation_context or "None",
        ]
    )

    try:
        sql = invoke_tool(
            "generate_sql",
            question=request.question,
            schema_context=enriched_context,
            conversation_context=request.conversation_context,
        )
    except Exception as exc:
        return {"error": f"Could not generate SQL: {exc}", "plan": plan, "profile": profile, "memory": memories}

    if not invoke_tool("validate_sql", sql=sql):
        return {"error": "Unsafe query", "sql": sql, "plan": plan, "profile": profile, "memory": memories}

    repaired = False
    last_error = None
    try:
        rows = invoke_tool("execute_sql", sql=sql)
    except Exception as exc:
        last_error = str(exc)
        for _ in range(request.max_repairs):
            try:
                sql = invoke_tool(
                    "repair_sql",
                    question=request.question,
                    schema_context=enriched_context,
                    failed_sql=sql,
                    error_message=last_error,
                )
                repaired = True
                if not invoke_tool("validate_sql", sql=sql):
                    return {
                        "error": "Repaired SQL was unsafe.",
                        "sql": sql,
                        "plan": plan,
                        "profile": profile,
                        "memory": memories,
                    }
                rows = invoke_tool("execute_sql", sql=sql)
                break
            except Exception as repair_exc:
                last_error = str(repair_exc)
        else:
            return {
                "error": f"Could not execute SQL: {last_error}",
                "sql": sql,
                "plan": plan,
                "profile": profile,
                "memory": memories,
            }

    row_count = len(rows)
    chart = invoke_tool("recommend_chart", rows=rows) if "chart" in plan.get("tools", []) else {"type": "table"}

    if "insight" in plan.get("tools", []):
        try:
            insight = invoke_tool("generate_insight", question=request.question, rows=rows)
        except Exception as exc:
            insight = f"Insight generation unavailable: {exc}"
    elif row_count:
        insight = "Query completed successfully."
    else:
        insight = "No rows matched the question."

    invoke_tool(
        "remember_interaction",
        table_name=request.table,
        question=request.question,
        sql=sql,
        insight=insight,
        row_count=row_count,
    )

    return {
        "sql": sql,
        "data": rows,
        "row_count": row_count,
        "chart": chart,
        "insight": insight,
        "repaired": repaired,
        "plan": plan,
        "profile": profile,
        "memory": memories,
    }

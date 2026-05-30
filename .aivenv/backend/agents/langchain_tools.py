try:
    from langchain_core.tools import tool
except ImportError:
    def tool(name=None):
        def decorator(func):
            class LocalTool:
                def __init__(self, fn):
                    self.name = name or fn.__name__
                    self.description = fn.__doc__ or ""
                    self.fn = fn

                def invoke(self, args):
                    return self.fn(**args)

            return LocalTool(func)

        return decorator

from backend.agents.chart_agent import recommend_chart
from backend.agents.executor import execute
from backend.agents.insight_agent import generate_insight
from backend.agents.memory_agent import recall_memory, remember_interaction
from backend.agents.profile_agent import profile_table
from backend.agents.repair_agent import repair_sql
from backend.agents.sql_agent import generate_sql
from backend.agents.validator import validate


@tool("profile_table")
def profile_table_tool(table_name: str) -> dict:
    """Inspect a table and return semantic column types plus quality notes."""
    return profile_table(table_name)


@tool("recall_memory")
def recall_memory_tool(table_name: str, limit: int = 5) -> list[dict]:
    """Recall prior BI questions, SQL, insights, and row counts for a table."""
    return recall_memory(table_name, limit=limit)


@tool("generate_sql")
def generate_sql_tool(question: str, schema_context: str, conversation_context: str = "") -> str:
    """Generate one safe SQLite SELECT query for a BI question."""
    return generate_sql(question, schema_context, conversation_context)


@tool("validate_sql")
def validate_sql_tool(sql: str) -> bool:
    """Validate that generated SQL is read-only and safe to execute."""
    return validate(sql)


@tool("execute_sql")
def execute_sql_tool(sql: str) -> list[dict]:
    """Execute a SQLite SELECT query and return rows as dictionaries."""
    return execute(sql).to_dict(orient="records")


@tool("repair_sql")
def repair_sql_tool(question: str, schema_context: str, failed_sql: str, error_message: str) -> str:
    """Repair a failed SQLite SELECT query using the database error message."""
    return repair_sql(question, schema_context, failed_sql, error_message)


@tool("recommend_chart")
def recommend_chart_tool(rows: list[dict]) -> dict:
    """Recommend a chart type and columns for query result rows."""
    return recommend_chart(rows)


@tool("generate_insight")
def generate_insight_tool(question: str, rows: list[dict]) -> str:
    """Generate concise business insights from query result rows."""
    return generate_insight(question, rows)


@tool("remember_interaction")
def remember_interaction_tool(table_name: str, question: str, sql: str, insight: str, row_count: int) -> str:
    """Persist a completed BI interaction to local SQLite memory."""
    remember_interaction(table_name, question, sql, insight, row_count)
    return "remembered"


LANGCHAIN_TOOLS = [
    profile_table_tool,
    recall_memory_tool,
    generate_sql_tool,
    validate_sql_tool,
    execute_sql_tool,
    repair_sql_tool,
    recommend_chart_tool,
    generate_insight_tool,
    remember_interaction_tool,
]


TOOLS_BY_NAME = {agent_tool.name: agent_tool for agent_tool in LANGCHAIN_TOOLS}


def invoke_tool(name, **kwargs):
    return TOOLS_BY_NAME[name].invoke(kwargs)

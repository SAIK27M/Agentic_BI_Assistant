from backend.agents.chart_agent import recommend_chart
from backend.agents.executor import execute
from backend.agents.insight_agent import generate_insight
from backend.agents.memory_agent import recall_memory, remember_interaction
from backend.agents.profile_agent import profile_table
from backend.agents.repair_agent import repair_sql
from backend.agents.sql_agent import generate_sql
from backend.agents.validator import validate
from backend.db.schema import get_schema_context, list_tables, preview_table

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    raise RuntimeError("Install the 'mcp' package to run this MCP server.") from exc


mcp = FastMCP("Agentic BI MCP Server")


@mcp.tool()
def list_bi_tables() -> list[str]:
    """List available BI tables in the local SQLite database."""
    return list_tables()


@mcp.tool()
def get_bi_schema_context(table_name: str) -> str:
    """Return schema and sample rows for a BI table."""
    return get_schema_context(table_name)


@mcp.tool()
def preview_bi_table(table_name: str, limit: int = 5) -> list[dict]:
    """Preview rows from a BI table."""
    return preview_table(table_name, limit=limit)


@mcp.tool()
def profile_bi_table(table_name: str) -> dict:
    """Inspect a BI table and return semantic column types and quality notes."""
    return profile_table(table_name)


@mcp.tool()
def recall_bi_memory(table_name: str, limit: int = 5) -> list[dict]:
    """Recall prior questions, SQL, insights, and row counts for a BI table."""
    return recall_memory(table_name, limit=limit)


@mcp.tool()
def generate_bi_sql(question: str, table_name: str, conversation_context: str = "") -> str:
    """Generate one SQLite SELECT query for a BI question."""
    return generate_sql(question, get_schema_context(table_name), conversation_context)


@mcp.tool()
def validate_bi_sql(sql: str) -> bool:
    """Validate that SQL is read-only and safe."""
    return validate(sql)


@mcp.tool()
def execute_bi_sql(sql: str) -> list[dict]:
    """Execute a safe SQLite SELECT query and return rows."""
    return execute(sql).to_dict(orient="records")


@mcp.tool()
def repair_bi_sql(question: str, table_name: str, failed_sql: str, error_message: str) -> str:
    """Repair a failed BI SQL query."""
    return repair_sql(question, get_schema_context(table_name), failed_sql, error_message)


@mcp.tool()
def recommend_bi_chart(rows: list[dict]) -> dict:
    """Recommend a chart for query result rows."""
    return recommend_chart(rows)


@mcp.tool()
def generate_bi_insight(question: str, rows: list[dict]) -> str:
    """Generate concise business insights from query result rows."""
    return generate_insight(question, rows)


@mcp.tool()
def remember_bi_interaction(table_name: str, question: str, sql: str, insight: str, row_count: int) -> str:
    """Save a BI interaction to local memory."""
    remember_interaction(table_name, question, sql, insight, row_count)
    return "remembered"


def main():
    mcp.run()


if __name__ == "__main__":
    main()

from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient


def create_local_mcp_client():
    app_root = Path(__file__).resolve().parents[2]
    python_path = app_root / "Scripts" / "python.exe"

    return MultiServerMCPClient(
        {
            "agentic_bi": {
                "command": str(python_path),
                "args": ["-m", "backend.mcp_server"],
                "cwd": str(app_root),
                "transport": "stdio",
            }
        }
    )


async def load_local_mcp_tools():
    client = create_local_mcp_client()
    return await client.get_tools()

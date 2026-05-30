# Agentic BI Assistant

An agentic BI assistant that lets users upload CSV/XLSX datasets, ask natural-language questions, generate safe SQLite queries with Groq, visualize results, and receive concise business insights.

The project uses:

- FastAPI backend
- Streamlit frontend
- SQLite local storage
- Groq LLM API
- LangChain tool wrappers
- MCP server for exposing BI tools to other MCP-compatible clients
- API-key authentication for protected backend routes

## Features

- Upload CSV or Excel files and save them as local SQLite tables
- Ask natural-language BI questions
- Generate and validate read-only SQLite SQL
- Repair failed SQL queries with an LLM
- Detect date, measure, category, and text columns through profiling
- Recommend charts for trends, comparisons, and metrics
- Generate business insights from query results
- Store local agent memory for previous questions and SQL
- Expose custom BI tools through LangChain and MCP

## Project Structure

```text
.aivenv/
  backend/
    agents/
      sql_agent.py
      planner_agent.py
      orchestrator.py
      profile_agent.py
      memory_agent.py
      langchain_tools.py
    db/
      database.py
      schema.py
      seed.py
    auth.py
    main.py
    mcp_server.py
  frontend/
    app.py
  requirements.txt
.env.example
README.md
```

## Setup

Create and activate a Python virtual environment. On Windows PowerShell:

```powershell
python -m venv .aivenv
.\.aivenv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
.\.aivenv\Scripts\python.exe -m pip install -r .\.aivenv\requirements.txt
```

Create your local `.env` from the example:

```powershell
Copy-Item .env.example .env
```

Fill in:

```env
GROQ_API_KEY=your-groq-api-key
AGENTIC_BI_API_KEY=your-local-api-key
```

Do not commit `.env`.

## Run The Backend

From the project root:

```powershell
.\.aivenv\Scripts\python.exe -m uvicorn backend.main:app --app-dir .\.aivenv --host 127.0.0.1 --port 8000 --reload
```

Health check:

```text
http://127.0.0.1:8000/health
```

Protected routes require:

```http
X-API-Key: your-local-api-key
```

## Run The Frontend

From the project root:

```powershell
.\.aivenv\Scripts\python.exe -m streamlit run .\.aivenv\frontend\app.py
```

The Streamlit app reads `AGENTIC_BI_API_KEY` from `.env` and sends it to the backend through the `X-API-Key` header.

## Example Questions

After uploading a sales dataset, select the uploaded table as the active table and ask:

```text
Show weekly sales trend by date
Show average weekly sales trend by date for store
Show revenue by region
Which product has the highest revenue?
Summarize the sales trend
```

For trend charts, include a grouping such as `by date`, `monthly`, `by region`, or `by product`.

## Authentication

The backend uses simple API-key authentication.

The key is stored locally in `.env`:

```env
AGENTIC_BI_API_KEY=your-local-api-key
```

The frontend sends it as:

```http
X-API-Key: your-local-api-key
```

The backend compares the request header with the configured `.env` value using `secrets.compare_digest`.

This is suitable for local demos, internal tools, and MVPs. For production with real users, consider JWT/OAuth, HTTPS, roles, and user-level permissions.

## LangChain Integration

Custom project agents are wrapped as LangChain tools in:

```text
.aivenv/backend/agents/langchain_tools.py
```

The orchestrator calls these tool wrappers, so your custom logic remains the core implementation while LangChain provides a standard tool interface.

## MCP Integration

The MCP server is defined in:

```text
.aivenv/backend/mcp_server.py
```

Run it locally:

```powershell
cd .aivenv
.\Scripts\python.exe -m backend.mcp_server
```

Example MCP config:

```text
.aivenv/mcp_config.example.json
```

Use MCP when another AI client or another project needs to call your BI tools without directly importing your Python code.

## Data Storage

Uploaded files are stored locally in SQLite:

```text
.aivenv/data.db
```

This file is ignored by Git. In production, replace local SQLite with a managed database such as Postgres, MySQL, Snowflake, BigQuery, or another warehouse.

## Git Safety

The repository ignores:

- `.env`
- local SQLite database files
- virtual environment folders
- machine-specific MCP config
- Python cache files

Before pushing, confirm secrets are not staged:

```powershell
git status
```


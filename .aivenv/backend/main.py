from fastapi import Depends, FastAPI
from pydantic import BaseModel

import pandas as pd

from backend.agents.orchestrator import run_agentic_query
from backend.auth import require_api_key
from backend.db.schema import (
    get_table_schema,
    list_tables,
    preview_table,
    save_dataframe,
)

app = FastAPI()


class QueryRequest(BaseModel):
    question: str
    table: str | None = None
    conversation_context: str = ""
    max_repairs: int = 1


class UploadRequest(BaseModel):
    table_name: str
    rows: list[dict]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tables", dependencies=[Depends(require_api_key)])
def tables():
    return {"tables": list_tables()}


@app.get("/schema", dependencies=[Depends(require_api_key)])
def schema(table: str | None = None):
    if table:
        return {
            "table": table,
            "columns": get_table_schema(table),
            "preview": preview_table(table),
        }

    return {
        "tables": [
            {
                "table": table_name,
                "columns": get_table_schema(table_name),
                "preview": preview_table(table_name),
            }
            for table_name in list_tables()
        ]
    }


@app.post("/upload", dependencies=[Depends(require_api_key)])
def upload(payload: UploadRequest):
    if not payload.rows:
        return {"error": "Uploaded data is empty."}

    try:
        df = pd.DataFrame(payload.rows)
        save_dataframe(payload.table_name, df)
        return {
            "table": payload.table_name,
            "rows": len(df),
            "columns": list(df.columns),
        }
    except Exception as exc:
        return {"error": f"Could not upload dataset: {exc}"}


@app.get("/query", dependencies=[Depends(require_api_key)])
def query(q: str):
    request = QueryRequest(question=q)
    return run_query(request)


@app.post("/query", dependencies=[Depends(require_api_key)])
def run_query(request: QueryRequest):
    return run_agentic_query(request)

import os
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from backend.config import load_env_file


API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_configured_api_key():
    load_env_file()
    return os.getenv("AGENTIC_BI_API_KEY", "").strip()


def require_api_key(api_key: str | None = Depends(API_KEY_HEADER)):
    expected_api_key = get_configured_api_key()
    if not expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AGENTIC_BI_API_KEY is not configured on the backend.",
        )

    if not api_key or not secrets.compare_digest(api_key, expected_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )

    return True

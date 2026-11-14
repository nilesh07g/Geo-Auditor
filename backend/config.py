"""Configuration settings for GEO Auditor API."""

import os
from typing import List
from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = "GEO Auditor API"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"

    # HTTP Fetcher Settings
    HTTP_TIMEOUT: float = 15.0  # seconds per page fetch
    MAX_CONTENT_PAGES: int = 3  # homepage + about + 1 service page
    # Modern browser User-Agent to pass Cloudflare/WAF checks on SMB and SaaS marketing sites
    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 "
        "GEOAuditor/1.0"
    )

    # CORS Allowed Origins
    CORS_ORIGINS: List[str] = [
        "https://geo-auditor-frontend.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # LLM Settings (Optional for experimental probe)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")


settings = Settings()

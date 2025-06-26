from fastapi import FastAPI

from mcp.core.config import get_settings
from mcp.api.v1.routes import api_router

settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)

# Mount versioned API router
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", summary="Root endpoint")
async def root() -> dict[str, str]:
    return {"message": f"Welcome to {settings.app_name}"} 
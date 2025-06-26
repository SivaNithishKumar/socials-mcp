from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="Health-check endpoint")
async def health() -> dict[str, str]:
    """Simple endpoint for liveness probes."""
    return {"status": "ok"} 
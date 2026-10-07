from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import engine
from app.core.redis import redis_client


router = APIRouter(prefix="/api/v1")


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "dqbh-backend",
    }


@router.get("/health/database")
def database_health():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "database": "connected",
        "result": value,
    }


@router.get("/health/redis")
def redis_health():
    result = redis_client.ping()

    return {
        "redis": "connected",
        "ping": result,
    }
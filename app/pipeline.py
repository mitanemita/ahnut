"""Конвейер генерации (этап 4): анкета → JSON открытки от нейросети → сборка → проверка."""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order


async def run(s: AsyncSession, order: Order) -> dict:
    raise HTTPException(501, "Генерация появится на этапе 4")

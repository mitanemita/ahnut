"""Служебные команды на сервере.

Удалить персональные данные по запросу (152-ФЗ), по номеру заказа или email:
    docker compose exec web python -m app.admin purge <id-заказа | email>
Запустить фоновые задачи вручную (напоминания, удаление по сроку):
    docker compose exec web python -m app.admin housekeeping
"""
import asyncio
import sys

from sqlalchemy import or_, select

from app.db import SessionLocal
from app.models import Order
from app.publish import housekeeping, purge


async def main(argv: list[str]) -> None:
    async with SessionLocal() as s:
        if argv[:1] == ["purge"] and len(argv) == 2:
            orders = (await s.execute(select(Order).where(or_(Order.public_id == argv[1], Order.email == argv[1])))).scalars().all()
            for o in orders:
                await purge(s, o)
            await s.commit()
            print(f"удалено заказов: {len(orders)}")
        elif argv[:1] == ["housekeeping"]:
            print(await housekeeping(s))
        else:
            print(__doc__)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))

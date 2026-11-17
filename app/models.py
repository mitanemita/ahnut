"""ORM-модели. Этап 1 — только заказ-заготовка; поля оплаты/анкеты добавятся на этапе 2."""
import secrets
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def new_public_id() -> str:
    # 128 бит случайности: неугадываемый id для ссылок /c/<id> и /order/<id>
    return secrets.token_urlsafe(16)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, default=new_public_id)
    tier: Mapped[str] = mapped_column(String(16))  # zapiska | svidanie | prince
    status: Mapped[str] = mapped_column(String(24), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

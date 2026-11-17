"""ORM-модели."""
import secrets
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def new_public_id() -> str:
    # 128 бит случайности: неугадываемый id для ссылок /c/<id> и /order/<id>
    return secrets.token_urlsafe(16)


class OrderStatus:
    DRAFT = "draft"                      # выбор/анкета, не оплачен
    AWAITING_PAYMENT = "awaiting_payment"
    PAID = "paid"                        # оплачен, ждём завершения анкеты
    QUEUED = "queued"                    # оплачен + анкета готова → передан в конвейер
    GENERATING = "generating"
    READY = "ready"                      # предпросмотр
    PUBLISHED = "published"
    FAILED = "failed"
    REFUNDED = "refunded"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, default=new_public_id)
    tier: Mapped[str] = mapped_column(String(16))  # zapiska | svidanie | prince
    status: Mapped[str] = mapped_column(String(24), default=OrderStatus.DRAFT)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    recipient: Mapped[str | None] = mapped_column(String(24))
    occasion: Mapped[str | None] = mapped_column(String(32))
    tone: Mapped[str | None] = mapped_column(String(24))
    email: Mapped[str | None] = mapped_column(String(254))
    amount_rub: Mapped[int] = mapped_column(Integer, default=0)

    # Оплата: выставляется ТОЛЬКО после проверки платежа через API ЮKassa
    paid: Mapped[bool] = mapped_column(Boolean, default=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    answers: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    answers_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    pd_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    generation_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    photos: Mapped[list[str] | None] = mapped_column(JSON)  # имена файлов в data/files/orders/<public_id>/
    refs: Mapped[list[str] | None] = mapped_column(JSON)    # картинки-референсы («Принц»)
    music: Mapped[str | None] = mapped_column(String(64))   # свой трек («Принц»)
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Card(Base):
    """Версии открытки: генерация и каждая правка — новая запись (можно откатиться)."""
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    kind: Mapped[str] = mapped_column(String(16), default="generate")  # generate | edit
    spec: Mapped[dict[str, Any]] = mapped_column(JSON)
    usage: Mapped[dict[str, Any] | None] = mapped_column(JSON)  # токены — для подсчёта себестоимости
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    yookassa_id: Mapped[str] = mapped_column(String(64), unique=True)
    kind: Mapped[str] = mapped_column(String(16), default="order")  # order | extension
    amount_rub: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24))  # pending | waiting_for_capture | succeeded | canceled
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

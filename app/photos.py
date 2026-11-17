"""Фото заказа: сжатие, удаление EXIF (там бывает GPS), хранение на диске сервера, отдача файлами."""
import io
import secrets
from pathlib import Path

from PIL import Image, ImageOps

from app.config import settings

MAX_SIDE = 1280
MAX_UPLOAD = 15 * 1024 * 1024


class PhotoError(ValueError):
    pass


def order_dir(public_id: str) -> Path:
    d = Path(settings.files_dir) / "orders" / public_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_photo(public_id: str, data: bytes) -> str:
    if len(data) > MAX_UPLOAD:
        raise PhotoError("Файл больше 15 МБ")
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception as e:  # noqa: BLE001
        raise PhotoError("Это не похоже на фото (нужен JPG, PNG, WEBP или HEIC, сохранённый как JPG)") from e
    im = ImageOps.exif_transpose(im)  # повернуть по EXIF, затем EXIF выбрасываем
    im = im.convert("RGB")
    im.thumbnail((MAX_SIDE, MAX_SIDE))
    name = f"p_{secrets.token_urlsafe(8)}.jpg"
    out = io.BytesIO()
    im.save(out, "JPEG", quality=82, optimize=True, progressive=True)  # без exif=
    (order_dir(public_id) / name).write_bytes(out.getvalue())
    return name


def photo_path(public_id: str, name: str) -> Path:
    if "/" in name or ".." in name or not name.startswith("p_"):
        raise PhotoError("bad name")
    return Path(settings.files_dir) / "orders" / public_id / name


def delete_photo(public_id: str, name: str) -> None:
    p = photo_path(public_id, name)
    if p.exists():
        p.unlink()

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


# ---------- референсы («Принц»): та же обработка, что у фото, другой префикс ----------

def save_ref(public_id: str, data: bytes) -> str:
    name = save_photo(public_id, data)
    new = "r_" + name[2:]
    (order_dir(public_id) / name).rename(order_dir(public_id) / new)
    return new


# ---------- музыка («Принц») ----------
MAX_MUSIC = 12 * 1024 * 1024
AUDIO_SIGNATURES = (  # (сигнатура, смещение, расширение, MIME)
    (b"ID3", 0, "mp3", "audio/mpeg"), (b"\xff\xfb", 0, "mp3", "audio/mpeg"), (b"\xff\xf3", 0, "mp3", "audio/mpeg"),
    (b"\xff\xf2", 0, "mp3", "audio/mpeg"), (b"ftyp", 4, "m4a", "audio/mp4"), (b"OggS", 0, "ogg", "audio/ogg"),
)
AUDIO_MIME = {"mp3": "audio/mpeg", "m4a": "audio/mp4", "ogg": "audio/ogg"}


def save_music(public_id: str, data: bytes) -> str:
    if len(data) > MAX_MUSIC:
        raise PhotoError("Файл больше 12 МБ")
    for sig, off, ext, _ in AUDIO_SIGNATURES:
        if data[off:off + len(sig)] == sig:
            name = f"m_{secrets.token_urlsafe(8)}.{ext}"
            (order_dir(public_id) / name).write_bytes(data)
            return name
    raise PhotoError("Нужен аудиофайл MP3, M4A или OGG")


def file_path(public_id: str, name: str) -> Path:
    """Любой файл заказа: p_ — фото, r_ — референс, m_ — музыка."""
    if "/" in name or "\\" in name or ".." in name or name[:2] not in ("p_", "r_", "m_"):
        raise PhotoError("bad name")
    return Path(settings.files_dir) / "orders" / public_id / name


def mime_for(name: str) -> str:
    return AUDIO_MIME.get(name.rsplit(".", 1)[-1], "image/jpeg") if name.startswith("m_") else "image/jpeg"

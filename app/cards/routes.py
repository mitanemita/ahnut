from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.cards.presets import all_presets, preset_spec
from app.cards.render import render

router = APIRouter()
DEMO_PHOTOS = [f"/static/demo/photo{i}.jpg" for i in range(6)]


@router.get("/demo/{name}", response_class=HTMLResponse)
async def demo(name: str):
    if name not in all_presets():
        raise HTTPException(404)
    meta = all_presets()[name]["meta"]
    return render(preset_spec(name), DEMO_PHOTOS, recipient=meta["recipients"][0])

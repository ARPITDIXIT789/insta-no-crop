from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image, ImageFilter
import io

app = FastAPI()

@app.post("/convert")
async def convert(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Unsupported format")

    # Original image
    original = Image.open(file.file).convert("RGB")

    # ---------- BLUR BACKGROUND ----------
    bg = original.copy()
    bg = bg.resize((1080, 1080))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=40))

    # ---------- FOREGROUND IMAGE ----------
    fg = original.copy()
    fg.thumbnail((1080, 1080))

    x = (1080 - fg.width) // 2
    y = (1080 - fg.height) // 2

    bg.paste(fg, (x, y))

    buffer = io.BytesIO()
    bg.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="image/png")

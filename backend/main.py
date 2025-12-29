from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image, ImageFilter, ImageEnhance
import io

app = FastAPI()

@app.post("/convert")
async def convert(
    file: UploadFile = File(...),
    blur: int = Form(40),
    bgcolor: str = Form("#000000"),
    mode: str = Form("blur")
):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Unsupported format")

    original = Image.open(file.file).convert("RGB")

    # Foreground
    fg = original.copy()
    fg.thumbnail((1080, 1080))
    x = (1080 - fg.width) // 2
    y = (1080 - fg.height) // 2

    # ---------- MODE HANDLING ----------
    if mode == "color":
        bg = Image.new("RGB", (1080, 1080), bgcolor)

    else:
        bg = original.copy().resize((1080, 1080))
        bg = bg.filter(ImageFilter.GaussianBlur(radius=blur))

        if mode == "ai":
            # 🔥 AI-LIKE ENHANCEMENT (lightweight)
            bg = ImageEnhance.Contrast(bg).enhance(1.4)
            bg = ImageEnhance.Brightness(bg).enhance(1.1)
            bg = ImageEnhance.Color(bg).enhance(1.3)

    bg.paste(fg, (x, y))

    buffer = io.BytesIO()
    bg.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="image/png")

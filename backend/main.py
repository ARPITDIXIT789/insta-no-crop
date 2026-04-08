from __future__ import annotations

import io
import re
from typing import Literal

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

app = FastAPI(title="Insta No Crop API", version="1.1.0")

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

Quality = Literal["normal", "hd", "ultra"]
Mode = Literal["blur", "ai", "color"]

QUALITY_TO_SIZE = {"normal": 1080, "hd": 2160, "ultra": 3840}
MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # keep under 20 MB nginx limit
MIN_BLUR, MAX_BLUR = 3, 80


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/convert")
async def convert(
    file: UploadFile = File(...),
    blur: int = Form(35),
    mode: Mode = Form("blur"),
    bgcolor: str = Form("#000000"),
    quality: Quality = Form("normal"),
    enhance_face: bool = Form(False),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid image type")

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 15 MB)")

    blur = int(max(MIN_BLUR, min(MAX_BLUR, blur)))
    mode = mode.lower()
    quality = quality.lower()

    if mode not in {"blur", "ai", "color"}:
        raise HTTPException(status_code=400, detail="Invalid background mode")
    if quality not in QUALITY_TO_SIZE:
        raise HTTPException(status_code=400, detail="Invalid quality value")
    if mode == "color" and not re.match(r"^#[0-9a-fA-F]{6}$", bgcolor):
        raise HTTPException(status_code=400, detail="Invalid hex color")

    try:
        image = Image.open(file.file).convert("RGB")
        image = ImageOps.exif_transpose(image)  # honor camera orientation
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or corrupted image")

    if enhance_face:
        image = enhance_face_only(image)

    canvas_size = QUALITY_TO_SIZE[quality]
    output = compose_canvas(
        image, mode=mode, blur=blur, bgcolor=bgcolor, canvas_size=canvas_size
    )

    buf = io.BytesIO()
    output.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


def enhance_face_only(pil_img: Image.Image) -> Image.Image:
    """
    Sharpen and slightly boost contrast only within detected faces
    to emulate Remini-style clarity without overprocessing the scene.
    """
    img = np.array(pil_img)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5,
        minSize=(80, 80),
    )

    if len(faces) == 0:
        return pil_img

    for (x, y, w, h) in faces:
        face = pil_img.crop((x, y, x + w, y + h))

        face = ImageEnhance.Sharpness(face).enhance(2.5)
        face = ImageEnhance.Contrast(face).enhance(1.35)
        face = ImageEnhance.Color(face).enhance(1.05)
        face = face.filter(ImageFilter.DETAIL)

        pil_img.paste(face, (x, y))

    return pil_img


def compose_canvas(
    image: Image.Image,
    *,
    mode: Mode,
    blur: int,
    bgcolor: str,
    canvas_size: int,
) -> Image.Image:
    fg = image.copy()
    fg.thumbnail((canvas_size, canvas_size), Image.Resampling.LANCZOS)

    if mode == "color":
        background = Image.new("RGB", (canvas_size, canvas_size), bgcolor)
    elif mode == "ai":
        background = smart_background(image, canvas_size, blur)
    else:  # classic blur
        background = image.copy().resize(
            (canvas_size, canvas_size), Image.Resampling.LANCZOS
        )
        background = background.filter(ImageFilter.GaussianBlur(radius=blur))

    x = (canvas_size - fg.width) // 2
    y = (canvas_size - fg.height) // 2
    background.paste(fg, (x, y))
    return background


def smart_background(image: Image.Image, canvas_size: int, blur: int) -> Image.Image:
    """
    AI-ish background: smooth radial gradient from dominant colors
    blended with a softened source texture to keep context.
    """
    small = image.resize((48, 48), Image.Resampling.BILINEAR)
    arr = np.array(small).reshape(-1, 3)
    mean = tuple(np.clip(arr.mean(axis=0), 0, 255).astype("uint8"))
    dark = tuple(np.clip(np.array(mean) * 0.65, 0, 255).astype("uint8"))

    yy, xx = np.ogrid[:canvas_size, :canvas_size]
    dist = np.sqrt((xx - canvas_size / 2) ** 2 + (yy - canvas_size / 2) ** 2)
    dist = dist / dist.max()
    mask = Image.fromarray(np.clip((1 - dist) * 255, 0, 255).astype("uint8"))

    base = Image.new("RGB", (canvas_size, canvas_size), dark)
    overlay = Image.new("RGB", (canvas_size, canvas_size), mean)
    gradient_bg = Image.composite(overlay, base, mask)

    softened = image.copy().resize(
        (canvas_size, canvas_size), Image.Resampling.LANCZOS
    )
    softened = softened.filter(ImageFilter.GaussianBlur(radius=max(blur * 0.6, 12)))

    return Image.blend(softened, gradient_bg, alpha=0.35)

from __future__ import annotations

import io
import json
import os
import re
from typing import Literal

import cv2
import numpy as np
import requests
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
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
AI_REQUEST_TIMEOUT = 25


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
    image = validate_and_read_image(file)

    blur = int(max(MIN_BLUR, min(MAX_BLUR, blur)))
    mode = mode.lower()
    quality = quality.lower()

    if mode not in {"blur", "ai", "color"}:
        raise HTTPException(status_code=400, detail="Invalid background mode")
    if quality not in QUALITY_TO_SIZE:
        raise HTTPException(status_code=400, detail="Invalid quality value")
    if mode == "color" and not re.match(r"^#[0-9a-fA-F]{6}$", bgcolor):
        raise HTTPException(status_code=400, detail="Invalid hex color")

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


@app.post("/ai/suggest-settings")
async def ai_suggest_settings(
    file: UploadFile = File(...),
    goal: str = Form("balanced"),
) -> dict[str, object]:
    image = validate_and_read_image(file)
    signals = extract_image_signals(image)

    ai_error = None
    ai_raw_response: dict[str, object] | None = None
    if OPENAI_API_KEY:
        try:
            ai_raw_response = ask_openai_for_settings(signals, goal)
        except Exception as exc:
            ai_error = str(exc)

    if ai_raw_response:
        settings = normalize_settings(ai_raw_response, signals)
        source = "ai"
    else:
        settings = heuristic_settings(signals, goal)
        source = "fallback"

    response: dict[str, object] = {
        "source": source,
        "settings": settings,
        "signals": {
            "width": signals["width"],
            "height": signals["height"],
            "orientation": signals["orientation"],
            "dominant_color": signals["dominant_color"],
            "brightness": signals["brightness"],
            "face_detected": signals["face_detected"],
        },
    }
    if ai_error:
        response["ai_error"] = ai_error
    return response


def validate_and_read_image(file: UploadFile) -> Image.Image:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid image type")

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image too large (max 15 MB)")

    try:
        image = Image.open(file.file).convert("RGB")
        image = ImageOps.exif_transpose(image)  # honor camera orientation
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or corrupted image")
    return image


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


def extract_image_signals(image: Image.Image) -> dict[str, object]:
    width, height = image.size
    orientation = "square"
    if height > width:
        orientation = "portrait"
    elif width > height:
        orientation = "landscape"

    small = image.resize((96, 96), Image.Resampling.BILINEAR)
    arr = np.array(small)

    brightness = float(np.mean(arr))
    saturation = float(np.mean(np.array(small.convert("HSV"))[:, :, 1]))

    quantized = small.convert("P", palette=Image.Palette.ADAPTIVE, colors=5).convert("RGB")
    colors = quantized.getcolors(96 * 96) or []
    dominant = max(colors, key=lambda item: item[0])[1] if colors else (15, 23, 42)

    face_detected = detect_face(image)
    return {
        "width": width,
        "height": height,
        "orientation": orientation,
        "brightness": round(brightness, 2),
        "saturation": round(saturation, 2),
        "dominant_color": rgb_to_hex(dominant),
        "face_detected": face_detected,
    }


def detect_face(image: Image.Image) -> bool:
    sample = image.copy()
    sample.thumbnail((720, 720), Image.Resampling.BILINEAR)
    gray = cv2.cvtColor(np.array(sample), cv2.COLOR_RGB2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5,
        minSize=(70, 70),
    )
    return bool(len(faces))


def ask_openai_for_settings(signals: dict[str, object], goal: str) -> dict[str, object]:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an image editing assistant. Return strict JSON with keys: "
                    "mode (blur|ai|color), blur (3-80), bgcolor (#RRGGBB), "
                    "quality (normal|hd|ultra), enhance_face (boolean), reason (string)."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "goal": goal,
                        "image_signals": signals,
                        "task": "Recommend settings for Instagram no-crop output.",
                    }
                ),
            },
        ],
    }
    response = requests.post(
        OPENAI_API_URL,
        headers=headers,
        json=payload,
        timeout=AI_REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return json.loads(content)


def normalize_settings(
    raw: dict[str, object],
    signals: dict[str, object],
) -> dict[str, object]:
    mode = str(raw.get("mode", "ai")).lower()
    if mode not in {"blur", "ai", "color"}:
        mode = "ai"

    blur = int(raw.get("blur", 35))
    blur = int(max(MIN_BLUR, min(MAX_BLUR, blur)))

    quality = str(raw.get("quality", "normal")).lower()
    if quality not in QUALITY_TO_SIZE:
        quality = pick_quality(signals["width"], signals["height"])

    bgcolor = str(raw.get("bgcolor", signals["dominant_color"]))
    if not re.match(r"^#[0-9a-fA-F]{6}$", bgcolor):
        bgcolor = str(signals["dominant_color"])

    enhance_face = bool(raw.get("enhance_face", signals["face_detected"]))
    reason = str(raw.get("reason", "AI recommended these settings from image metadata."))

    return {
        "mode": mode,
        "blur": blur,
        "quality": quality,
        "bgcolor": bgcolor,
        "enhance_face": enhance_face,
        "reason": reason,
    }


def heuristic_settings(signals: dict[str, object], goal: str) -> dict[str, object]:
    width = int(signals["width"])
    height = int(signals["height"])
    orientation = str(signals["orientation"])
    brightness = float(signals["brightness"])
    dominant_color = str(signals["dominant_color"])
    face_detected = bool(signals["face_detected"])
    goal_lc = goal.lower().strip()

    mode: Mode = "ai"
    if "minimal" in goal_lc or "clean" in goal_lc:
        mode = "color"
    elif orientation == "square":
        mode = "blur"

    blur = 34 if orientation == "portrait" else 24
    if "soft" in goal_lc:
        blur += 8
    if "sharp" in goal_lc:
        blur -= 6
    blur = int(max(MIN_BLUR, min(MAX_BLUR, blur)))

    quality = pick_quality(width, height)

    # Keep solid color slightly darker on bright photos for better contrast
    bgcolor = dominant_color
    if brightness > 165:
        bgcolor = darken_hex(dominant_color, 0.55)
    elif brightness < 95:
        bgcolor = darken_hex(dominant_color, 0.85)

    return {
        "mode": mode,
        "blur": blur,
        "quality": quality,
        "bgcolor": bgcolor,
        "enhance_face": face_detected,
        "reason": "Fallback recommendation generated from local image analysis.",
    }


def pick_quality(width: int, height: int) -> Quality:
    max_side = max(width, height)
    if max_side >= 3200:
        return "ultra"
    if max_side >= 1900:
        return "hd"
    return "normal"


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def darken_hex(hex_color: str, factor: float) -> str:
    value = hex_color.lstrip("#")
    r = int(value[0:2], 16)
    g = int(value[2:4], 16)
    b = int(value[4:6], 16)
    r = int(max(0, min(255, r * factor)))
    g = int(max(0, min(255, g * factor)))
    b = int(max(0, min(255, b * factor)))
    return rgb_to_hex((r, g, b))

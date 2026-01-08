from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image, ImageFilter, ImageEnhance
import io
import numpy as np
import cv2
import mediapipe as mp

app = FastAPI()

# ---------- AI FACE DETECTOR ----------
mp_face = mp.solutions.face_detection.FaceDetection(
    model_selection=0,
    min_detection_confidence=0.6
)

@app.post("/convert")
async def convert(
    file: UploadFile = File(...),
    blur: int = Form(35),
    bgcolor: str = Form("#000000"),
    mode: str = Form("blur"),          # blur | color | ai
    quality: str = Form("normal")      # normal | hd | ultra
):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Unsupported image format")

    original = Image.open(file.file).convert("RGB")

    # ---------- OUTPUT SIZE ----------
    if quality == "hd":
        size = 2160
    elif quality == "ultra":
        size = 3840
    else:
        size = 1080

    # ---------- FOREGROUND ----------
    fg = original.copy()
    fg.thumbnail((size, size))
    x = (size - fg.width) // 2
    y = (size - fg.height) // 2

    # ---------- BACKGROUND ----------
    if mode == "color":
        bg = Image.new("RGB", (size, size), bgcolor)

    else:
        bg = original.copy().resize((size, size))
        bg = bg.filter(ImageFilter.GaussianBlur(radius=blur))

        if mode == "ai":
            # 🔥 AI SMART BACKGROUND (LIGHTWEIGHT & FAST)
            bg = ImageEnhance.Contrast(bg).enhance(1.35)
            bg = ImageEnhance.Brightness(bg).enhance(1.1)
            bg = ImageEnhance.Color(bg).enhance(1.25)

            # ---------- FACE PRESERVE ----------
            np_img = np.array(bg)
            rgb = cv2.cvtColor(np_img, cv2.COLOR_BGR2RGB)
            result = mp_face.process(rgb)

            if result.detections:
                orig_np = np.array(original.resize((size, size)))
                for det in result.detections:
                    box = det.location_data.relative_bounding_box
                    h, w, _ = orig_np.shape

                    x1 = int(box.xmin * w)
                    y1 = int(box.ymin * h)
                    bw = int(box.width * w)
                    bh = int(box.height * h)

                    np_img[y1:y1+bh, x1:x1+bw] = orig_np[y1:y1+bh, x1:x1+bw]

                bg = Image.fromarray(np_img)

    # ---------- COMPOSE ----------
    bg.paste(fg, (x, y))

    buffer = io.BytesIO()
    bg.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="image/png")

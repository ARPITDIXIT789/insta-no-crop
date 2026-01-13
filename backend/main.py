from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image, ImageEnhance, ImageFilter
import io
import cv2
import numpy as np

app = FastAPI()

# Load face detector once
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

@app.post("/convert")
async def convert(
    file: UploadFile = File(...),
    enhance_face: bool = False
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid image")

    # Read image
    try:
        image = Image.open(file.file).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image")

    if enhance_face:
        image = enhance_face_only(image)

    # --- Insta no crop (same as before) ---
    bg = image.copy().resize((1080, 1080))
    bg = bg.filter(ImageFilter.GaussianBlur(40))

    fg = image.copy()
    fg.thumbnail((1080, 1080))

    x = (1080 - fg.width) // 2
    y = (1080 - fg.height) // 2
    bg.paste(fg, (x, y))

    buf = io.BytesIO()
    bg.save(buf, format="PNG", optimize=True)
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")


def enhance_face_only(pil_img: Image.Image) -> Image.Image:
    # Convert to OpenCV
    img = np.array(pil_img)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5,
        minSize=(80, 80)
    )

    # If no face found → return original
    if len(faces) == 0:
        return pil_img

    for (x, y, w, h) in faces:
        face = pil_img.crop((x, y, x + w, y + h))

        # ✨ FACE ENHANCEMENT MAGIC
        face = ImageEnhance.Sharpness(face).enhance(2.5)
        face = ImageEnhance.Contrast(face).enhance(1.4)
        face = face.filter(ImageFilter.DETAIL)

        # Paste back
        pil_img.paste(face, (x, y))

    return pil_img

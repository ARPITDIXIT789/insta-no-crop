from fastapi import FastAPI, UploadFile, File
from fastapi.responses import Response
from PIL import Image, ImageFilter
import io

app = FastAPI()

SIZE = 1080

@app.post("/convert")
async def convert(file: UploadFile = File(...)):
    # Read image bytes (supports all formats Pillow can read)
    image_bytes = await file.read()
    original = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Background (blurred square)
    bg = original.resize((SIZE, SIZE))
    bg = bg.filter(ImageFilter.GaussianBlur(30))

    # Foreground (no crop)
    original.thumbnail((SIZE, SIZE))
    x = (SIZE - original.width) // 2
    y = (SIZE - original.height) // 2
    bg.paste(original, (x, y))

    # Output as JPEG (Instagram best)
    buf = io.BytesIO()
    bg.save(buf, format="JPEG", quality=95)
    buf.seek(0)

    return Response(content=buf.read(), media_type="image/jpeg")

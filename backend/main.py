from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image
import io

app = FastAPI()

@app.post("/convert")
async def convert(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Unsupported format")

    image = Image.open(file.file).convert("RGB")
    image.thumbnail((1080, 1080))

    canvas = Image.new("RGB", (1080, 1080), (0, 0, 0))
    x = (1080 - image.width) // 2
    y = (1080 - image.height) // 2
    canvas.paste(image, (x, y))

    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="image/png")

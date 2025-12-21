from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from PIL import Image, ImageFilter
import uuid

app = FastAPI()

INSTAGRAM_SIZE = (1080, 1080)

@app.post("/convert")
async def convert_image(file: UploadFile = File(...)):
    image = Image.open(file.file).convert("RGB")

    bg = image.resize(INSTAGRAM_SIZE)
    bg = bg.filter(ImageFilter.GaussianBlur(25))

    image.thumbnail(INSTAGRAM_SIZE)

    x = (INSTAGRAM_SIZE[0] - image.width) // 2
    y = (INSTAGRAM_SIZE[1] - image.height) // 2
    bg.paste(image, (x, y))

    filename = f"/tmp/{uuid.uuid4()}.jpg"
    bg.save(filename, "JPEG", quality=95)

    return FileResponse(filename, media_type="image/jpeg")

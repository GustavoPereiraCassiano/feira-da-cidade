import os, uuid
from PIL import Image
from flask import current_app
from werkzeug.utils import secure_filename

ALLOWED_IMAGES = {"jpg", "jpeg", "png", "webp"}
ALLOWED_VIDEOS = {"mp4", "webm"}

def save_media(file):
    if not file or not file.filename or "." not in file.filename:
        raise ValueError("Selecione um arquivo válido.")
    ext = file.filename.rsplit(".", 1)[1].lower()
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(folder, name)

    if ext in ALLOWED_IMAGES:
        try:
            image = Image.open(file.stream).convert("RGB")
            image.thumbnail((1920, 1920))
            quality = 85
            while True:
                image.save(path, "JPEG", quality=quality, optimize=True)
                if os.path.getsize(path) <= 200 * 1024 or quality <= 25:
                    break
                quality -= 10
            if os.path.getsize(path) > 200 * 1024:
                image.thumbnail((1400, 1400))
                image.save(path, "JPEG", quality=25, optimize=True)
            return name, "image"
        except Exception as exc:
            raise ValueError("Não foi possível processar a imagem.") from exc
    if ext in ALLOWED_VIDEOS:
        file.save(path)
        return name, "video"
    raise ValueError("Formato não permitido. Use JPG, PNG, WEBP, MP4 ou WEBM.")

def money(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

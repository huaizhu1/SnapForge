from fastapi import FastAPI, File, UploadFile, Form
from logic import ImageProcessor

import tempfile
import shutil
import os

app = FastAPI(title="SnapForge API")
processor = ImageProcessor()

@app.post("/process/")
def process_image(
    file: UploadFile = File(...),
    prefix: str = Form("api"),
    convert_format: str = Form(""),
    resize_width: int = Form(0),
    resize_height: int = Form(0),
    watermark_text: str = Form(""),
    watermark_pos: str = Form("bottom-right"),
    filter_type: str = Form(""),
    rotate: int = Form(0)
):
    temp_dir = tempfile.mkdtemp()
    try:
        path = os.path.join(temp_dir, file.filename)
        with open(path, "wb") as out:
            out.write(file.file.read())
        watermark = {"text": watermark_text, "pos": watermark_pos} if watermark_text else None
        args = {
            "files": [path],
            "prefix": prefix,
            "convert_format": convert_format,
            "resize_enabled": resize_width>0 and resize_height>0,
            "resize_width": resize_width or None,
            "resize_height": resize_height or None,
            "watermark": watermark,
            "filter_type": filter_type or None,
            "rotate": rotate,
        }
        _, _, res_paths = processor.batch_process(**args)
        with open(res_paths[0], "rb") as fin:
            content = fin.read()
        return {"filename": os.path.basename(res_paths[0]), "content": content.hex()}
    finally:
        shutil.rmtree(temp_dir)
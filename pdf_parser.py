from pathlib import Path
import fitz
import numpy as np
import base64

from PIL import Image
import io


class PDFParser:
    def __init__(self):
        pass

    def update_file(self, file_path: Path):
        self.file_path = file_path
        self.doc = fitz.open(str(self.file_path))  # Ensure the path is converted to string

    def get_page_image(self, page_number: int, scale: float = 2.0):
        page = self.doc.load_page(page_number)
        mat = fitz.Matrix(scale, scale)  # Scale using fitz.Matrix
        pix = page.get_pixmap(matrix=mat)  # Apply the scaling
        img_data = pix.tobytes("png")  # Convert to PNG bytes

        # Convert bytes to PIL Image
        img = Image.open(io.BytesIO(img_data))
        return img

    def get_gpt_ready_page_image(self, page_number: int):
        page = self.doc.load_page(page_number)
        image = page.get_pixmap()
        image = image.tobytes("png")
        image = base64.b64encode(image).decode("utf-8")
        return image

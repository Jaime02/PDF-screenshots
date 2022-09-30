from pathlib import Path

import pytesseract
from pytesseract import image_to_string
from PIL import Image
pytesseract.pytesseract.tesseract_cmd = Path('..') / "Tesseract" / "tesseract.exe"


def perform_ocr(path: Path):
    image = Image.open(path)
    text = image_to_string(image, lang='eng')
    return text


if __name__ == '__main__':
    perform_ocr(Path('..') / "images")

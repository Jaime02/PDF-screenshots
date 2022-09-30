from pathlib import Path

from PySide6.QtWidgets import QApplication
from src.window import MainWindow
import pytesseract

pytesseract.pytesseract.tesseract_cmd = Path('.') / "Tesseract" / "tesseract.exe"

if __name__ == "__main__":
    app = QApplication()
    window = MainWindow()
    window.show()
    app.exec()

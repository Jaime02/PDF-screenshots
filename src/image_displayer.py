from pathlib import Path

from PIL.ImageQt import ImageQt
from PyPDF2 import PdfFileReader
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QWheelEvent
from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGraphicsScene,
    QGraphicsView,
    QStyle,
    QLabel,
    QMessageBox,
    QGraphicsPixmapItem,
)
from pdf2image import convert_from_path

from .step_slider import StepSlider


class PDFFile(QWidget):
    def __init__(self, path: str):
        super().__init__()

        self.path: Path = Path(path)
        self.page_count: int = len(PdfFileReader(path).pages)

        self.pages: dict[QPixmap] = {
            1: QPixmap.fromImage(ImageQt(convert_from_path(self.path, first_page=1, last_page=1)[0]))
        }

    def __str__(self):
        return self.path.name

    def update_page(self, number: int):
        if number not in self.pages:
            pixmap = QPixmap.fromImage(ImageQt(convert_from_path(self.path, first_page=number, last_page=number)[0]))
            self.pages[number] = pixmap

    def file_name(self):
        return self.path.name.split(".")[0]


class View(QGraphicsView):
    def __init__(self):
        QGraphicsView.__init__(self)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

    def wheelEvent(self, event: QWheelEvent):
        event.ignore()


class ImageDisplayer(QWidget):
    def __init__(self, window):
        super().__init__()

        self.window = window
        self.file: PDFFile = None
        self.current_page = 1

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.view = View()
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(Qt.black)
        self.view.setScene(self.scene)
        self.layout.addWidget(self.view)

        self.buttons_layout = QHBoxLayout()
        self.layout.addLayout(self.buttons_layout)

        self.go_to_first_page_button = QPushButton()
        self.go_to_first_page_button.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaSkipBackward")))
        self.buttons_layout.addWidget(self.go_to_first_page_button)
        self.go_to_first_page_button.clicked.connect(self.go_to_first_page)

        self.go_to_previous_page_button = QPushButton()
        self.go_to_previous_page_button.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaSeekBackward")))
        self.buttons_layout.addWidget(self.go_to_previous_page_button)
        self.go_to_previous_page_button.clicked.connect(self.go_to_previous_page)

        self.pages = QLabel("0/0")
        self.buttons_layout.addWidget(self.pages)

        self.go_to_next_page_button = QPushButton()
        self.go_to_next_page_button.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaSeekForward")))
        self.buttons_layout.addWidget(self.go_to_next_page_button)
        self.go_to_next_page_button.clicked.connect(self.go_to_next_page)

        self.go_to_last_page_button = QPushButton()
        self.go_to_last_page_button.setIcon(self.style().standardIcon(getattr(QStyle, "SP_MediaSkipForward")))
        self.buttons_layout.addWidget(self.go_to_last_page_button)
        self.go_to_last_page_button.clicked.connect(self.go_to_last_page)

        self.buttons_layout.addStretch()

        self.zoom = 100
        self.zoom_values = [25, 50, 75, 100, 125, 150, 200, 300, 400, 500, 600, 800]
        self.zoom_slider = StepSlider(self.zoom_values)
        self.zoom_slider.setValue(self.zoom)
        self.zoom_slider.valueChanged.connect(lambda: self.set_zoom(self.zoom_slider.value()))
        self.buttons_layout.addWidget(self.zoom_slider)

        self.zoom_label = QLabel(f"Zoom: {self.zoom}%")
        self.buttons_layout.addWidget(self.zoom_label)

        self.setMinimumSize(400, 400)

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        event.accept()

    def set_zoom(self, zoom: int):
        if zoom not in self.zoom_values:
            QMessageBox.critical(self, "Error", "Invalid zoom value")
            return

        self.zoom = zoom
        self.zoom_slider.setValue(self.zoom)
        self.zoom_label.setText(f"Zoom: {self.zoom}%")
        self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)

        transform = self.view.transform().scale(self.zoom / 100, self.zoom / 100)
        self.view.setTransform(transform)

    def update_file(self, file: PDFFile):
        self.file = file
        self.current_page = 1
        if file is None:
            self.pages.setText("0/0")
            return

        self.update_page()

        for item in self.scene.items():
            if isinstance(item, QGraphicsPixmapItem):
                self.view.fitInView(item, Qt.KeepAspectRatio)
                break

        self.set_zoom(self.zoom)

    def update_page(self):
        self.pages.setText(f"{self.current_page}/{self.file.page_count}")
        self.file.update_page(self.current_page)
        self.update_scene()

    def update_scene(self):
        # Take out all the items from the scene but don't delete them
        for item in self.scene.items():
            self.scene.removeItem(item)

        if self.file is None:
            return

        self.scene.addPixmap(self.file.pages[self.current_page])

        for i in range(self.window.rect_list_widget.count()):
            rect = self.window.rect_list_widget.itemWidget(self.window.rect_list_widget.item(i))

            if rect is None:
                break
            if rect.page != self.current_page:
                continue
            if not rect.drawable_rect.is_selected:
                continue

            self.scene.addItem(rect.drawable_rect)
            rect.drawable_rect.setPos(rect.drawable_rect.pos())

    def go_to_next_page(self):
        if self.file is None:
            return

        if self.current_page < self.file.page_count:
            self.current_page += 1
            self.update_page()

    def go_to_previous_page(self):
        if self.file is None:
            return

        if self.current_page > 1:
            self.current_page -= 1
            self.update_page()

    def go_to_first_page(self):
        self.go_to_page(1)

    def go_to_last_page(self):
        self.go_to_page(self.file.page_count)

    def go_to_page(self, page: int):
        if self.file is None:
            return
        self.current_page = page
        self.update_page()

    def zoom_in(self):
        if self.file is None:
            return

        if self.zoom < self.zoom_values[-1]:
            self.zoom = self.zoom_values[self.zoom_values.index(self.zoom) + 1]
            self.zoom_slider.setValue(self.zoom)
            self.set_zoom(self.zoom)

    def zoom_out(self):
        if self.file is None:
            return

        if self.zoom > self.zoom_values[0]:
            self.zoom = self.zoom_values[self.zoom_values.index(self.zoom) - 1]
            self.zoom_slider.setValue(self.zoom)
            self.set_zoom(self.zoom)

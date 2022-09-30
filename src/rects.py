from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPen, QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QMenu,
    QHBoxLayout,
    QLabel,
    QGraphicsRectItem,
    QGraphicsSceneHoverEvent,
    QGraphicsSceneMouseEvent,
    QGraphicsItem,
)

from .image_displayer import PDFFile


@dataclass
class PickleRect:
    x: int
    y: int
    width: int
    height: int
    name: str
    page: int


class SelectedResize(Enum):
    NONE = 0
    LEFT = 1
    TOP = 2
    RIGHT = 3
    BOTTOM = 4
    TOP_LEFT = 5
    TOP_RIGHT = 6
    BOTTOM_LEFT = 7
    BOTTOM_RIGHT = 8


class DrawableRect(QGraphicsRectItem):
    def __init__(self, *args):
        QGraphicsRectItem.__init__(self, *args)

        self.last_pos = None
        self.selected_edge = None
        self.is_selected = False

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        if change == QGraphicsItem.ItemPositionChange:
            if self.scene() is not None:
                self.scene().update()
        return QGraphicsRectItem.itemChange(self, change, value)

    def paint(self, painter, option, widget=None):
        QGraphicsRectItem.paint(self, painter, option, widget)
        painter.setPen(QPen(Qt.red, 10, Qt.SolidLine))
        painter.setBrush(Qt.transparent)
        painter.drawRect(self.rect())

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        t = 15  # threshold
        if event.pos().x() < t and event.pos().y() < t:
            self.setCursor(Qt.SizeFDiagCursor)
            self.selected_edge = SelectedResize.TOP_LEFT
        elif event.pos().x() > self.rect().width() - t and event.pos().y() > self.rect().height() - t:
            self.setCursor(Qt.SizeFDiagCursor)
            self.selected_edge = SelectedResize.BOTTOM_RIGHT
        elif event.pos().x() < t and event.pos().y() > self.rect().height() - t:
            self.setCursor(Qt.SizeBDiagCursor)
            self.selected_edge = SelectedResize.BOTTOM_LEFT
        elif event.pos().x() > self.rect().width() - t and event.pos().y() < t:
            self.setCursor(Qt.SizeBDiagCursor)
            self.selected_edge = SelectedResize.TOP_RIGHT
        elif event.pos().x() < t or event.pos().x() > self.rect().width() - t:
            self.setCursor(Qt.SizeHorCursor)
            self.selected_edge = SelectedResize.LEFT if event.pos().x() < 5 else SelectedResize.RIGHT
        elif event.pos().y() < t or event.pos().y() > self.rect().height() - t:
            self.setCursor(Qt.SizeVerCursor)
            self.selected_edge = SelectedResize.TOP if event.pos().y() < t else SelectedResize.BOTTOM
        else:
            self.setCursor(Qt.ArrowCursor)
            self.selected_edge = SelectedResize.NONE
        QGraphicsRectItem.hoverMoveEvent(self, event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if self.cursor().shape() != Qt.ArrowCursor:
            self.last_pos = event.screenPos()
        QGraphicsRectItem.mousePressEvent(self, event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if not self.is_selected:
            event.ignore()
            QGraphicsRectItem.mouseMoveEvent(self, event)
            return

        if self.last_pos is None:
            self.last_pos = event.screenPos()

        if self.selected_edge == SelectedResize.NONE:
            QGraphicsRectItem.mouseMoveEvent(self, event)
            return

        delta = event.screenPos() - self.last_pos
        self.last_pos = event.screenPos()

        self.prepareGeometryChange()
        if self.selected_edge == SelectedResize.LEFT:
            self.setRect(0, 0, self.rect().width() + delta.x(), self.rect().height())
            self.setPos(self.pos() + QPoint(delta.x(), 0))
        elif self.selected_edge == SelectedResize.RIGHT:
            self.setRect(0, 0, self.rect().width() + delta.x(), self.rect().height())
        elif self.selected_edge == SelectedResize.TOP:
            self.setRect(0, 0, self.rect().width(), self.rect().height() + delta.y())
            self.setPos(self.pos() + QPoint(0, delta.y()))
        elif self.selected_edge == SelectedResize.BOTTOM:
            self.setRect(0, 0, self.rect().width(), self.rect().height() + delta.y())
        elif self.selected_edge == SelectedResize.TOP_LEFT:
            self.setRect(0, 0, self.rect().width() + delta.x(), self.rect().height() + delta.y())
            self.setPos(self.pos() + QPoint(delta.x(), delta.y()))
        elif self.selected_edge == SelectedResize.TOP_RIGHT:
            self.setRect(0, 0, self.rect().width() + delta.x(), self.rect().height() + delta.y())
            self.setPos(self.pos() + QPoint(0, delta.y()))
        elif self.selected_edge == SelectedResize.BOTTOM_LEFT:
            self.setRect(0, 0, self.rect().width() + delta.x(), self.rect().height() + delta.y())
            self.setPos(self.pos() + QPoint(delta.x(), 0))
        elif self.selected_edge == SelectedResize.BOTTOM_RIGHT:
            self.setRect(0, 0, self.rect().width() + delta.x(), self.rect().height() + delta.y())

        self.setRect(self.rect().normalized())


class Rect(QWidget):
    def __init__(self, window, name: str, page: int):
        QWidget.__init__(self)

        self.window = window
        self.name = name
        self.page = page

        self.drawable_rect = DrawableRect(0, 0, 300, 150)
        self.drawable_rect.setPos(10, 10)

        self.main_layout = QHBoxLayout()
        self.setLayout(self.main_layout)

        self.label = QLabel(self.name)
        self.main_layout.addWidget(self.label)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos: QPoint):
        menu = QMenu()
        menu.addAction("Rename", self.window.rename_rect)
        menu.addAction("Remove", self.window.remove_rect)
        menu.exec(self.mapToGlobal(pos))

    def sizeHint(self):
        return self.minimumSizeHint()

    def crop_image(self, file: PDFFile) -> QPixmap:
        pixmap = file.pages[self.page]
        rect = self.drawable_rect.rect().toRect()
        offset = self.drawable_rect.pos().toPoint()
        rect.translate(offset)
        pixmap = pixmap.copy(rect.x(), rect.y(), rect.width(), rect.height())
        return pixmap

    def get_pickle(self):
        return PickleRect(
            self.drawable_rect.pos().x(),
            self.drawable_rect.pos().y(),
            self.drawable_rect.rect().width(),
            self.drawable_rect.rect().height(),
            self.name,
            self.page
        )

    @classmethod
    def from_pickle(cls, window, pickle_rect: PickleRect):
        rect = cls(window, pickle_rect.name, pickle_rect.page)
        rect.drawable_rect.setPos(pickle_rect.x, pickle_rect.y)
        rect.drawable_rect.setRect(0, 0, pickle_rect.width, pickle_rect.height)
        return rect

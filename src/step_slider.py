from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSlider, QSizePolicy


class StepSlider(QSlider):
    def __init__(self, values: list[int]):
        super().__init__()
        self.values = values
        self.setRange(0, len(values) - 1)
        self.setSingleStep(1)
        self.setOrientation(Qt.Horizontal)
        self.setTickPosition(QSlider.TicksBelow)
        self.setTickInterval(1)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

    def value(self) -> int:
        return self.values[super().value()]

    def setValue(self, value: int):
        super().setValue(self.values.index(value))

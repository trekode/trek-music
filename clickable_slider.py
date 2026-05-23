from PyQt6.QtWidgets import QSlider, QLabel
from PyQt6.QtCore import Qt, QPoint


class ClickableSlider(QSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setMouseTracking(True)

        self._tooltip_label = QLabel()
        self._tooltip_label.setObjectName("slider-tooltip")
        self._tooltip_label.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self._tooltip_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._tooltip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._tooltip_label.hide()


    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Calcular la posición proporcional del clic
            new_value = self.minimum() + ((self.maximum()-self.minimum()) * event.position().x() / self.width())
            new_value = max(self.minimum(), min(self.maximum(), int(new_value)))
            self.setValue(int(new_value))
            self.sliderMoved.emit(int(new_value))  # emitir señal para mover la canción
            self._update_tooltip()
        super().mousePressEvent(event)


    def mouseReleaseEvent(self, event):
        self._check_and_show(event.position().x())
        super().mouseReleaseEvent(event)


    def mouseMoveEvent(self, event):
        self._check_and_show(event.position().x())
        super().mouseMoveEvent(event)


    def leaveEvent(self, event):
        self._tooltip_label.hide()
        super().leaveEvent(event)


    def _check_and_show(self, cursor_x):
        if self.maximum() == 0:
            self._tooltip_label.hide()
            return

        handle_x = (self.value() - self.minimum()) / (self.maximum() - self.minimum()) * self.width()

        if abs(cursor_x - handle_x) <= 15:
            self._update_tooltip()
        else:
            self._tooltip_label.hide()


    def _update_tooltip(self):
        if self.maximum() == 0:
            return

        def ms_to_str(ms):
            s = int(ms) // 1000
            return f"{s // 60}:{s % 60:02d}"

        current = self.value()
        total = self.maximum()

        self._tooltip_label.setText(f"{ms_to_str(current)} / {ms_to_str(total)}")
        self._tooltip_label.adjustSize()

        handle_x = int((self.value() - self.minimum()) / (self.maximum() - self.minimum()) * self.width())

        global_pos = self.mapToGlobal(QPoint(handle_x, 0))
        x = global_pos.x() - self._tooltip_label.width() // 2
        y = global_pos.y() - self._tooltip_label.height() - 5


        self._tooltip_label.move(x, y)
        self._tooltip_label.show()


    def update_tooltip_if_visible(self):
        if self._tooltip_label.isVisible():
            self._update_tooltip()
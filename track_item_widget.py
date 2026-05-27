from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QSizePolicy, QSpacerItem
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from glow_label import GlowLabel
from utils.paths import resource_path


class TrackItemWidget(QWidget):
    def __init__(self, title: str, duration: str, track_path: str, parent=None):
        super().__init__(parent)

        self.track_path: str = track_path

        icon = QIcon(resource_path("assets/music_icon.png"))
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(15,15))
        icon_label.setFixedWidth(15)

        self.title_label = GlowLabel(title)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.title_label.setMinimumWidth(0)

        self.duration_label = GlowLabel(duration)
        self.duration_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.duration_label.setFixedWidth(35)    

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.addWidget(icon_label)
        layout.addWidget(self.title_label)
        layout.addSpacerItem(QSpacerItem(5, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        layout.addWidget(self.duration_label)

        self.setLayout(layout)

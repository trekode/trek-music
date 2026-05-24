from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QToolButton, QDockWidget
)
from PyQt6.QtCore import Qt, QSize

PLAYLIST_TITLE_FONT = QFont("Dubai", 12)


class DockTitleBar(QWidget):
    def __init__(self, dock: QDockWidget, title: str):
        super().__init__()
        self.dock = dock

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 1, 0, 1)
        layout.setSpacing(2)

        self.title_label = QLabel(title)
        self.title_label.setFont(PLAYLIST_TITLE_FONT)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.title_label.setContentsMargins(5,0,0,0)
        layout.addWidget(self.title_label, 1)

        self.float_btn = QToolButton()
        self.float_btn.setIcon(QIcon("assets/floating-dock.png"))
        self.float_btn.setIconSize(QSize(15,15))
        self.float_btn.setFixedSize(25, 25)
        self.float_btn.setCheckable(True)
        self.float_btn.setChecked(False)
        self.float_btn.clicked.connect(self.toggle_floating)
        layout.addWidget(self.float_btn)

        self.close_btn = QToolButton()
        self.close_btn.setIcon(QIcon("assets/close.png"))
        self.close_btn.setIconSize(QSize(15,15))
        self.close_btn.setFixedSize(25, 25)
        self.close_btn.clicked.connect(dock.close)
        layout.addWidget(self.close_btn)

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("dock_title_bar")


    def toggle_floating(self):
        self.dock.setFloating(not self.dock.isFloating())
        self.float_btn.setChecked(self.dock.isFloating())
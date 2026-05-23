from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget, QButtonGroup)


class CustomTabWidget(QWidget):
    tab_context_menu_requested = pyqtSignal(str)  # emits tab name

    def __init__(self, tabs_data: list[list], parent=None):
        """
        tabs_data: [tab_name, widget, tooltip] list
        Example:
        [
            ["Library", self.playlist, "Original order (never modified)"],
            ["Queue", self.queue_list, "Current playback order (editable)"]
        ]
        """
        super().__init__(parent)

        tabs_data = tabs_data

        # Create buttons and stacked widget
        self.stacked_widget = QStackedWidget()
        buttons = []
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)

        # Buttons Layout
        tab_layout = QHBoxLayout()
        tab_layout.setSpacing(0)
        tab_layout.setContentsMargins(0, 0, 0, 0)

        tabs_container = QWidget()
        tabs_container.setLayout(tab_layout)
        tabs_container.setObjectName("tabs_container")
        tabs_container.setContentsMargins(0,0,0,0)

        for idx, (name, widget, tooltip) in enumerate(tabs_data):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setToolTip(tooltip)
            btn.setContentsMargins(0,0,0,0)
            if idx == 0:
                btn.setChecked(True)
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, n=name: self.tab_context_menu_requested.emit(n))
            self.button_group.addButton(btn, idx)
            tab_layout.addWidget(btn)
            self.stacked_widget.addWidget(widget)
            buttons.append(btn)

        self.button_group.buttonClicked.connect(self.on_tab_clicked)

        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(tabs_container)
        main_layout.addWidget(self.stacked_widget)


    def on_tab_clicked(self, btn):
        idx = self.button_group.id(btn)
        self.stacked_widget.setCurrentIndex(idx)
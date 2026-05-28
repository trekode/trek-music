import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QDockWidget, QStatusBar, QWidget, \
    QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem, QStyleFactory, QSizePolicy, QSlider, QMenu
from PyQt6.QtGui import QPixmap, QAction, QKeySequence, QPainter, QFont, QCursor, QIcon
from PyQt6.QtCore import Qt, QStandardPaths, QPoint, QEvent, QTimer
from PyQt6.QtWidgets import QFileDialog
from mutagen import File
from clickable_slider import ClickableSlider
from marquee_label import MarqueeLabel
from custom_tab_widget import CustomTabWidget
from track_item_widget import TrackItemWidget
from dock_title_bar import DockTitleBar
from floating_volume_panel import FloatingVolumePanel
from player import Player
from utils.paths import resource_path


TRACK_NAME_FONT = QFont("Dubai", 14)
AUDIO_EXTENSIONS = (".mp3", ".wav", ".flac", ".ogg", ".m4a")


class MainWindow(QMainWindow):

# --------------------------------- INITIALIZATION ---------------------------------

    def  __init__(self):
        super().__init__()

        self.player = Player()
        self.player.playback_state_changed.connect(self.update_playback_state_style)
        self.player.shuffle_state_changed.connect(self.update_shuffle_button)
        self.player.volume_state_changed.connect(self.update_volume_button)
        self.player.track_changed.connect(self.update_current_track)
        self.player.playlist_changed.connect(self.update_queue_list)

        self.current_music_folder = ""
        self.track_paths_list = []
        self.list_view_mode = "original"
        self.current_main_size = "expanded"
        self.volume = round(self.player.audio_output.volume()*100)

        self.menu_mode = "simple"

        self._bg_pixmap = QPixmap(resource_path("assets/background.jpg"))
        self._bg_scaled = None
        self._bg_size = None

        self.wasPlaying = False

        self.inicialize_ui()

        self.create_status_bar()

        QApplication.instance().installEventFilter(self)
        

    def inicialize_ui(self):
        self.setGeometry(200,100,918,518)
        self.setWindowTitle("Trek Music")
        self.setWindowIcon(QIcon(resource_path("assets/window_icon.ico")))
        self.generate_main_window()
        self.create_dock()
        self.create_action()
        self.create_menu()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.show()


    def create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status_bar()


# --------------------------------- UI GENERATION ---------------------------------

    def generate_main_window(self):
        # WIDGETS

        self.main_widget = QWidget()
        self.main_widget.installEventFilter(self)

        self.player_image = QLabel()
        self.player_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.player_image.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.player_image.setContentsMargins(0,0,0,0)
        self.original_pixmap = QPixmap(resource_path("assets/player_image.jpg"))

        self.slider = ClickableSlider(Qt.Orientation.Horizontal, self)
        self.slider.setStyle(QStyleFactory.create("Fusion"))
        self.slider.setRange(0, 100)
        self.slider.setValue(0)
        self.slider.setEnabled(False)
        self.slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.slider.setFixedHeight(17)
        self.player.duration_changed.connect(lambda dur: (self.slider.setRange(0, dur), self.slider.setEnabled(True)))
        self.player.position_changed.connect(lambda pos: (self.slider.setValue(pos), self.slider.update_tooltip_if_visible()))
        self.player.position_changed.connect(
            lambda pos: self.slider.setValue(pos) if not self.slider.isSliderDown() else None)
        self.slider.sliderMoved.connect(lambda pos: self.player.set_position(pos))
        self.slider.sliderPressed.connect(self.slider_pressed)
        self.slider.sliderReleased.connect(self.slider_released)

        self.track_name = MarqueeLabel()
        self.track_name.setFont(TRACK_NAME_FONT)
        self.track_name.setObjectName("track_name")
        self.track_name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.track_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.track_name.setContentsMargins(0,0,0,0)

        self.reproduction_buttons_container = self.generate_reproduction_buttons()

        self.volume_button = QPushButton()
        self.volume_button.setObjectName("volume_button")
        self.volume_button.setToolTip("Mute")
        self.volume_button.clicked.connect(self.handle_volume_button_click)
        self.volume_button.setFixedSize(30, 30)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self.volume)  # Valor inicial
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.setToolTip(f"Volume: {self.volume}%")
        self.volume_slider.valueChanged.connect(self.change_volume)

        self.volume_toggle_button = QPushButton()
        self.volume_toggle_button.setObjectName("volume_toggle_button")
        self.volume_toggle_button.setToolTip("Open volume slider")
        self.volume_toggle_button.clicked.connect(self.toggle_floating_volume_slider)
        self.volume_toggle_button.setFixedSize(20, 30)
        self.volume_toggle_button.hide()

        self.floating_volume_slider = QSlider(Qt.Orientation.Vertical)
        self.floating_volume_slider.setToolTip(f"Volume: {self.volume}%")

        self.floating_volume_slider.setRange(0, 100)
        self.floating_volume_slider.setValue(int(self.player.audio_output.volume() * 100))
        self.floating_volume_slider.setFixedHeight(100)
        self.floating_volume_slider.valueChanged.connect(self.change_volume)

        self.floating_volume_panel = FloatingVolumePanel()
        self.floating_volume_panel.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.floating_volume_panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.floating_volume_panel.closed.connect(self.on_volume_panel_closed)

        self.floating_volume_panel_layout = QVBoxLayout(self.floating_volume_panel)
        self.floating_volume_panel_layout.setContentsMargins(3, 8, 3, 8)
        self.floating_volume_panel_layout.addWidget(self.floating_volume_slider)
        self.floating_volume_panel.hide()

        # LAYOUT

        self.setCentralWidget(self.main_widget)

        self.main_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)

        slider_layout = QVBoxLayout()
        slider_layout.setContentsMargins(9, 0, 9, 7)
        slider_layout.addStretch()
        slider_layout.addWidget(self.slider)
        slider_container = QWidget()
        slider_container.setLayout(slider_layout)

        self.track_inner_container = QWidget()
        self.track_inner_container.setMinimumWidth(40)
        self.track_inner_layout = QVBoxLayout()
        self.track_inner_layout.setContentsMargins(0, 0, 0, 0)
        self.track_inner_container.setLayout(self.track_inner_layout)

        self.track_inner_layout.addStretch()
        self.track_inner_layout.addWidget(self.track_name)
        self.track_inner_layout.addStretch()

        self.track_outer_container = QWidget()
        self.track_outer_container.setMinimumWidth(136)
        self.track_outer_layout = QHBoxLayout(self.track_outer_container)
        self.track_outer_layout.setContentsMargins(0,0,0,0)
        self.track_outer_layout.addWidget(self.track_inner_container)
        self.track_outer_layout.addStretch()

        self.volume_layout = QHBoxLayout()
        self.volume_layout.setContentsMargins(0,0,0,0)
        self.volume_layout.addStretch(5)
        self.volume_layout.addWidget(self.volume_button)
        self.volume_layout.addWidget(self.volume_toggle_button)
        self.volume_layout.addWidget(self.volume_slider)
        self.volume_layout.setSpacing(5)
        volume_container = QWidget()
        volume_container.setLayout(self.volume_layout)

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setContentsMargins(10,0,10,0)
        self.bottom_layout.setSpacing(10)

        self.bottom_layout.addWidget(self.track_outer_container, 1)
        self.bottom_layout.addStretch()
        self.bottom_layout.addWidget(self.reproduction_buttons_container)
        self.bottom_layout.addStretch()
        self.bottom_layout.addWidget(volume_container, 1)
        self.bottom_container = QWidget()
        self.bottom_container.setLayout(self.bottom_layout)

        image_container_layout = QHBoxLayout()
        image_container_layout.addWidget(self.player_image)
        self.image_container = QWidget()
        self.image_container.setContentsMargins(0,0,0,0)
        self.image_container.setLayout(image_container_layout)

        self.main_layout.setContentsMargins(5, 7, 5, 15)
        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(self.image_container, stretch=1)
        self.main_layout.addStretch(0)
        self.main_layout.addWidget(slider_container, stretch=0)
        self.main_layout.addWidget(self.bottom_container, stretch=0)


    def generate_reproduction_buttons(self):

        # WIDGETS

        self.play_pause_button = QPushButton()
        self.play_pause_button.setObjectName("play_pause_button")
        self.play_pause_button.clicked.connect(self.handle_play_pause_click)
        self.play_pause_button.setEnabled(False)

        self.next_button = QPushButton()
        self.next_button.setObjectName("next_button")
        self.next_button.clicked.connect(lambda: self.player.next_track(auto=False))
        self.next_button.setEnabled(False)

        self.previous_button = QPushButton()
        self.previous_button.setObjectName("previous_button")
        self.previous_button.clicked.connect(self.player.previous_track)
        self.previous_button.setEnabled(False)

        self.ten_forward_button = QPushButton()
        self.ten_forward_button.setObjectName("ten_forward_button")
        self.ten_forward_button.clicked.connect(lambda: self.player.skip_seconds(10))
        self.ten_forward_button.setEnabled(False)

        self.ten_backward_button = QPushButton()
        self.ten_backward_button.setObjectName("ten_backward_button")
        self.ten_backward_button.clicked.connect(lambda: self.player.skip_seconds(-10))
        self.ten_backward_button.setEnabled(False)

        self.repeat_button = QPushButton()
        self.repeat_button.setObjectName("repeat_button")
        self.repeat_button.setToolTip("Repeat")
        self.repeat_button.clicked.connect(self.handle_repeat_click)

        self.shuffle_button = QPushButton()
        self.shuffle_button.setObjectName("shuffle_button")
        self.shuffle_button.setToolTip("Shuffle")
        self.shuffle_button.clicked.connect(self.handle_shuffle_click)

        self.play_pause_button.setFixedSize(50, 50)
        self.ten_forward_button.setMaximumSize(42, 42)
        self.ten_backward_button.setMaximumSize(42, 42)
        self.next_button.setFixedSize(38, 38)
        self.previous_button.setFixedSize(38, 38)
        self.shuffle_button.setFixedSize(30, 30)
        self.repeat_button.setFixedSize(30, 30)

        # LAYOUT

        buttons_hbox = QHBoxLayout()
        buttons_hbox.setContentsMargins(15, 8, 15, 8)
        buttons_hbox.setSpacing(5)

        buttons_hbox.addWidget(self.shuffle_button)
        buttons_hbox.addWidget(self.previous_button)
        buttons_hbox.addWidget(self.ten_backward_button)
        buttons_hbox.addWidget(self.play_pause_button)
        buttons_hbox.addWidget(self.ten_forward_button)
        buttons_hbox.addWidget(self.next_button)
        buttons_hbox.addWidget(self.repeat_button)

        buttons_container = QWidget()
        buttons_container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        buttons_container.setObjectName("buttons_container")
        buttons_container.setLayout(buttons_hbox)

        return buttons_container


# --------------------------------- MENU ---------------------------------

    def create_action(self):
        self.open_files_action = QAction("Open Files", self)
        self.open_files_action.setShortcut(QKeySequence("Ctrl+O"))
        self.open_files_action.hovered.connect(lambda: self.update_status_bar("Load selected music files"))
        self.open_files_action.triggered.connect(self.open_files)

        self.open_folder_action = QAction("Open Folder", self)
        self.open_folder_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        self.open_folder_action.hovered.connect(lambda: self.update_status_bar("Open a folder and scan subfolders for music files"))
        self.open_folder_action.triggered.connect(self.open_folder)

        self.open_files_replace_action = QAction("Replace Playlist", self)
        self.open_files_replace_action.setShortcut(QKeySequence("Ctrl+O"))
        self.open_files_replace_action.hovered.connect(lambda: self.update_status_bar("Replace playlist with selected audio files"))
        self.open_files_replace_action.triggered.connect(lambda: self.open_files(replace=True))

        self.open_files_add_action = QAction("Add to Playlist", self)
        self.open_files_add_action.hovered.connect(lambda: self.update_status_bar("Add selected audio files to current playlists"))
        self.open_files_add_action.triggered.connect(lambda: self.open_files(replace=False))

        self.open_folder_replace_action = QAction("Replace Playlist", self)
        self.open_folder_replace_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        self.open_folder_replace_action.hovered.connect(lambda: self.update_status_bar("Replace playlist with all music files in folder"))
        self.open_folder_replace_action.triggered.connect(lambda: self.open_folder(replace=True))

        self.open_folder_add_action = QAction("Add to Playlist", self)
        self.open_folder_add_action.hovered.connect(lambda: self.update_status_bar("Add all music files in folder to current playlists"))
        self.open_folder_add_action.triggered.connect(lambda: self.open_folder(replace=False))

        self.view_playlist_action = QAction("Playlist Panel", self, checkable=True)
        self.view_playlist_action.setShortcut(QKeySequence("Ctrl+L"))
        self.view_playlist_action.hovered.connect(lambda: self.update_status_bar("Show or hide the playlist panel"))
        self.view_playlist_action.triggered.connect(self.view_playlist)
        self.view_playlist_action.setChecked(True)

        self.view_player_image_action = QAction("Player Image", self, checkable=True)
        self.view_player_image_action.setShortcut(QKeySequence("Ctrl+I"))
        self.view_player_image_action.hovered.connect(lambda: self.update_status_bar("Show or hide the player image"))
        self.view_player_image_action.triggered.connect(self.view_player_image)
        self.view_player_image_action.setChecked(True)

        self.view_fullscreen_action = QAction("Full Screen", self, checkable=True)
        self.view_fullscreen_action.setShortcut(QKeySequence("F11"))
        self.view_fullscreen_action.hovered.connect(lambda: self.update_status_bar("Enter or exit full screen"))
        self.view_fullscreen_action.triggered.connect(self.toggle_fullscreen)
        self.view_fullscreen_action.setChecked(False)


    def create_menu(self):
        self.menuBar().setStyle(QStyleFactory.create("Fusion"))

        self.file_menu = self.menuBar().addMenu("File")

        self.open_files_menu = QMenu("Open Audio Files", self)
        self.open_files_menu.addAction(self.open_files_replace_action)
        self.open_files_menu.addAction(self.open_files_add_action)

        self.open_folder_menu = QMenu("Open Music Folder", self)
        self.open_folder_menu.addAction(self.open_folder_replace_action)
        self.open_folder_menu.addAction(self.open_folder_add_action)

        self.create_simple_menu()

        self.file_menu.setMinimumWidth(self.file_menu.sizeHint().width() + 10)
        self.file_menu.installEventFilter(self)
        self.file_menu.aboutToShow.connect(self.sync_file_menu)

        view_menu = self.menuBar().addMenu("View")
        view_menu.addAction(self.view_playlist_action)
        view_menu.addAction(self.view_player_image_action)
        view_menu.addAction(self.view_fullscreen_action)
        view_menu.installEventFilter(self)


    def create_simple_menu(self):
        self.file_menu.addAction(self.open_files_action)
        self.file_menu.addAction(self.open_folder_action)


    def change_to_simple_menu(self):
        self.file_menu.removeAction(self.open_files_menu.menuAction())
        self.file_menu.removeAction(self.open_folder_menu.menuAction())
        self.create_simple_menu()


    def change_to_extended_menu(self):
        self.file_menu.removeAction(self.open_files_action)
        self.file_menu.removeAction(self.open_folder_action)

        self.file_menu.addMenu(self.open_files_menu)
        self.file_menu.addMenu(self.open_folder_menu)


    def sync_file_menu(self):
        desired_mode = "advanced" if self.track_paths_list else "simple"

        if self.menu_mode == desired_mode:
            return

        if desired_mode == "simple":
            self.change_to_simple_menu()
        else:
            self.change_to_extended_menu()

        self.menu_mode = desired_mode


# --------------------------------- DOCK / LISTS ---------------------------------

    def create_dock(self):
        self.library_list = QListWidget()
        self.queue_list = QListWidget()
        self.library_list.itemDoubleClicked.connect(self.handle_track_double_click)
        self.queue_list.itemDoubleClicked.connect(self.handle_track_double_click)

        self.library_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.library_list.customContextMenuRequested.connect(self.show_list_menu)

        self.queue_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.queue_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.queue_list.setDragEnabled(True)
        self.queue_list.setAcceptDrops(True)
        self.queue_list.setDropIndicatorShown(True)
        self.queue_list.model().rowsMoved.connect(self.on_queue_reordered)
        self.queue_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.queue_list.customContextMenuRequested.connect(self.show_list_menu)

        tab_widget = CustomTabWidget([["Library", self.library_list, "Source list (order preserved)"], ["Queue", self.queue_list, "Playback order (editable)"]])
        tab_widget.setObjectName("custom_tab_widget")
        tab_widget.tab_context_menu_requested.connect(self.on_tab_context_menu)

        self.dock = QDockWidget()
        self.dock_title_bar = DockTitleBar(self.dock, "Playlist")
        self.dock.setTitleBarWidget(self.dock_title_bar)
        self.dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)

        self.dock.setWidget(tab_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock)
        self.dock.visibilityChanged.connect(self.sync_view_playlist_action)
        self.dock.topLevelChanged.connect(self.sync_float_button)


    def populate_dock_list(self, list_widget, paths_list):
        list_widget.clear()

        for track_path in paths_list:
            audio = File(track_path)
            if audio is None or audio.info is None:
                continue

            duration_seconds = int(audio.info.length)
            duration_str = f"{duration_seconds // 60}:{duration_seconds % 60:02d}"

            item = QListWidgetItem()
            widget = TrackItemWidget(os.path.basename(track_path), duration_str, track_path)
            item.setSizeHint(widget.sizeHint())

            list_widget.addItem(item)
            list_widget.setItemWidget(item, widget)


    def update_queue_list(self, new_list):
        self.populate_dock_list(self.queue_list, new_list)
        self.update_playback_state_style()


    def on_queue_reordered(self):
        current_track = self.player.get_current_track_path()

        new_order = []

        for i in range(self.queue_list.count()):
            item = self.queue_list.item(i)
            widget = self.queue_list.itemWidget(item)

            new_order.append(widget.track_path)

        self.player.track_list = new_order

        if current_track in self.player.track_list:
            self.player.current_track_index = self.player.track_list.index(current_track)
        else:
            self.player.current_track_index = 0
            self.player.pause()
            self.player.load_current_track()


    def on_tab_context_menu(self, tab_name):
        list = self.queue_list if tab_name == "Queue" else self.library_list
        self._add_list_actions(list)


    def show_list_menu(self, pos):
        list = self.sender()
        item = list.itemAt(pos)

        if not item:
            self._add_list_actions(list)
            return

        menu = QMenu(self)
        if list == self.library_list:
            widget = self.library_list.itemWidget(item)
            track_path = widget.track_path

            if track_path not in self.player.track_list:
                add_to_queue_action = QAction("Add to queue", self)
                add_to_queue_action.hovered.connect(lambda: self.update_status_bar("Add the track to the queue"))
                add_to_queue_action.triggered.connect(lambda: self.add_to_queue(track_path))

                menu.addAction(add_to_queue_action)

        remove_action = QAction("Remove", self)
        if list == self.library_list:
            remove_action.hovered.connect(lambda: self.update_status_bar("Remove the track from the library (also removes it from the queue)"))
        else:
            remove_action.hovered.connect(lambda: self.update_status_bar("Remove the track from the queue"))
        remove_action.triggered.connect(lambda: self.remove_track_from_list(list, item))

        menu.addAction(remove_action)
        menu.exec(list.mapToGlobal(pos))


    def _add_list_actions(self, list):
        menu = QMenu(self)

        if list == self.queue_list:
            if self.player.track_list != self.track_paths_list:
                reset_action = QAction("Reset to library", self)
                reset_action.hovered.connect(lambda: self.update_status_bar("Reset the queue to match library"))
                if self.player.track_list:
                    reset_action.triggered.connect(self.player.reset_queue_to_library)

                else:
                    reset_action.triggered.connect(lambda: self.player.load_queue(self.track_paths_list))

                menu.addAction(reset_action)

            if self.player.track_list:
                clear_action = QAction("Clear queue", self)
                clear_action.hovered.connect(lambda: self.update_status_bar("Clear the queue"))
                clear_action.triggered.connect(self.clear_list)
                menu.addAction(clear_action)

        elif list == self.library_list and self.track_paths_list:
            if not self.player.track_list:
                add_list_to_queue_action = QAction("Add list to queue", self)
                add_list_to_queue_action.hovered.connect(lambda: self.update_status_bar("Add all library tracks to the queue"))
                add_list_to_queue_action.triggered.connect(self.add_to_queue)
                menu.addAction(add_list_to_queue_action)

            if self.player.track_list and len(self.track_paths_list) != len(self.player.track_list):
                add_missing_to_queue_action = QAction("Add missing to queue", self)
                add_missing_to_queue_action.hovered.connect(lambda: self.update_status_bar("Add all library tracks not already in the queue"))
                add_missing_to_queue_action.triggered.connect(self.add_to_queue)
                menu.addAction(add_missing_to_queue_action)

            clear_action = QAction("Clear library", self)
            clear_action.hovered.connect(lambda: self.update_status_bar("Clear the library (also clears the queue)"))
            clear_action.triggered.connect(lambda: self.clear_list(True))
            menu.addAction(clear_action)

        if not menu.isEmpty():
            menu.exec(QCursor.pos())


    def remove_track_from_list(self, list, item):
        widget = list.itemWidget(item)
        track_path = widget.track_path

        self.player.remove_track(track_path)

        if list == self.library_list:
            self.player.remove_from_original_list(track_path)
            self.track_paths_list.remove(track_path)
            self.populate_dock_list(self.library_list, self.track_paths_list)
            self.highlight_current_track(self.player.get_current_track_path())


    def clear_list(self, clear_all: bool = False):
        self.player.clear_track_list(clear_all)

        if clear_all:
            self.track_paths_list.clear()
            self.library_list.clear()
            self.populate_dock_list(self.library_list, self.track_paths_list)

        self.highlight_current_track(self.player.get_current_track_path())
        self.update_buttons_style()


    def add_to_queue(self, track):
        if track:
            self.player.add_to_queue(track)

        else:
            if self.player.track_list:
                tracks = []
                for track_path in self.track_paths_list:
                    if track_path not in self.player.track_list:
                        tracks.append(track_path)
                self.player.add_to_queue(*tracks)

            else:
                self.player.load_queue(self.track_paths_list)

        self.update_queue_list(self.player.track_list)


    def sync_float_button(self):
        self.dock_title_bar.float_btn.setChecked(self.dock.isFloating())


# --------------------------------- VISIBILITY ---------------------------------

    def view_playlist(self):
        if self.view_playlist_action.isChecked():
            self.dock.show()
        else:
            self.dock.hide()
        self.update_status_bar()


    def sync_view_playlist_action(self, visible):
        self.view_playlist_action.setChecked(visible)


    def view_player_image(self):
        if self.view_player_image_action.isChecked():
            self.player_image.show()
        else:
            self.player_image.hide()
        self.update_status_bar()


    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.view_fullscreen_action.setChecked(False)
        else:
            self.showFullScreen()
            self.view_fullscreen_action.setChecked(True)


# --------------------------------- TRACK MANAGEMENT ---------------------------------

    def open_files(self, replace=True):
        initial_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.MusicLocation
        )

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select music files",
            initial_dir,
            "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a)"
        )

        if not files:
            self.update_status_bar()
            return

        self._add_tracks(files, replace)


    def open_folder(self, replace=True):
        """Open a folder and add all music files, including those in subfolders."""
        initial_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.MusicLocation)
        folder = QFileDialog.getExistingDirectory(None, "Select a folder", initial_dir)
        if not folder:
            self.update_status_bar()
            return

        track_paths_list = []

        # Walk through folder and subfolders
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.lower().endswith(AUDIO_EXTENSIONS):
                    track_paths_list.append(os.path.join(root, file))

        self._add_tracks(track_paths_list, replace)


    def _add_tracks(self, paths, replace=True):
        paths = list(dict.fromkeys(paths))  # remove duplicates within the new paths

        if not replace:
            paths = [p for p in paths if p not in self.track_paths_list]  # exclude paths already in the playlist

        if replace:
            self.library_list.clear()
            self.track_paths_list.clear()

        self.track_paths_list.extend(paths)

        self.populate_dock_list(self.library_list, self.track_paths_list)

        if self.track_paths_list:
            self.player.set_tracks(paths, replace)
            self.update_buttons_style()

        self.populate_dock_list(self.queue_list, self.player.track_list)
        self.update_playback_state_style()


# --------------------------------- PLAYBACK CONTROLS ---------------------------------

    def handle_play_pause_click(self):
        self.player.play_pause()


    def handle_shuffle_click(self):
        self.player.toggle_shuffle()


    def handle_repeat_click(self):
        self.player.toggle_repeat()
        path = resource_path(f"assets/repeat_{self.player.repeat}.png").replace("\\", "/")
        self.repeat_button.setStyleSheet(f'image: url("{path}");')
        self.update_status_bar()


    def handle_track_double_click(self, item):
        list = self.sender()
        widget = list.itemWidget(item)

        if widget:
            if list == self.library_list and widget.track_path not in self.player.track_list:
                self.player.insert_next_and_play(widget.track_path)
            else:
                self.player.set_track_by_path(widget.track_path)


    def slider_pressed(self):
        if self.player.reproduction_mode == "playing":
            self.player.pause()
            self.wasPlaying = True
        else:
            self.wasPlaying = False


    def slider_released(self):
        self.player.set_position(self.slider.value())

        if self.wasPlaying:
            self.player.play()


# --------------------------------- UI STATE ---------------------------------

    def update_playback_state_style(self):
        self.update_play_pause_button_style()
        self.update_buttons_style()
        self.highlight_current_track(self.player.get_current_track_path())
        self.update_status_bar()


    def update_play_pause_button_style(self):
        if self.player.reproduction_mode == "playing":
            self.play_pause_button.setToolTip("Pause")
            path = resource_path("assets/pause.png").replace("\\", "/")
            self.play_pause_button.setStyleSheet(
                f"image: url({path});"
                "padding: 10px 10px 10px 11px;"
            )
        else:
            self.play_pause_button.setToolTip("Play")
            path = resource_path("assets/play_enabled.png").replace("\\", "/")
            self.play_pause_button.setStyleSheet(
                f"image: url({path});"
                "padding: 8px 8px 8px 12px;"
            )

        if self.player.track_list:
            self.play_pause_button.setEnabled(True)
        else:
            self.play_pause_button.setEnabled(False)
            path = resource_path("assets/play_disabled.png").replace("\\", "/")
            self.play_pause_button.setStyleSheet(
                f"image: url({path});"
                "padding: 8px 8px 8px 12px;"
            )
            self.play_pause_button.setToolTip("")


    def update_buttons_style(self):
        has_tracks = bool(self.player.track_list)
        is_playing = self.player.reproduction_mode != "stopped"

        self.next_button.setEnabled(has_tracks)
        next_state = "enabled" if has_tracks else "disabled"
        next_path = resource_path(f"assets/next_{next_state}.png").replace("\\", "/")
        self.next_button.setStyleSheet(
            f"image: url({next_path})")
        self.next_button.setToolTip("Next Track" if has_tracks else "")

        self.previous_button.setEnabled(has_tracks)
        previous_state = "enabled" if has_tracks else "disabled"
        previous_path = resource_path(f"assets/previous_{previous_state}.png").replace("\\", "/")
        self.previous_button.setStyleSheet(
            f"image: url({previous_path})")
        self.previous_button.setToolTip("Previous Track" if has_tracks else "")

        enable_seek = has_tracks and is_playing

        self.ten_forward_button.setEnabled(enable_seek)
        ten_forward_state = "enabled" if enable_seek else "disabled"
        ten_forward_path = resource_path(f"assets/ten_forward_{ten_forward_state}.png").replace("\\", "/")
        self.ten_forward_button.setStyleSheet(
            f"image: url({ten_forward_path})")
        self.ten_forward_button.setToolTip("Forward 10 seconds" if enable_seek else "")

        self.ten_backward_button.setEnabled(enable_seek)
        ten_backward_state = "enabled" if enable_seek else "disabled"
        ten_backward_path = resource_path(f"assets/ten_backward_{ten_backward_state}.png").replace("\\", "/")
        self.ten_backward_button.setStyleSheet(
            f"image: url({ten_backward_path})")
        self.ten_backward_button.setToolTip("Backward 10 seconds" if enable_seek else "")


    def update_shuffle_button(self, is_shuffle_on):
        if is_shuffle_on:
            path = resource_path("assets/shuffle_on.png").replace("\\", "/")
        else:
            path = resource_path("assets/shuffle_off.png").replace("\\", "/")

        self.shuffle_button.setStyleSheet(f"image: url({path})")

        self.update_status_bar()


    def update_current_track(self, current_track):
        if current_track and self.player.reproduction_mode != "stopped":
            self.track_name.setText(Path(current_track).stem)
            self.track_name.setStyleSheet("background-color: rgba(5, 1, 20, 0.3);")
        else:
            self.track_name.setText("")
            self.track_name.setStyleSheet("background-color: transparent;")

        self.highlight_current_track(self.player.get_current_track_path())


    def highlight_current_track(self, current_track):
        for widgets_list in [self.library_list, self.queue_list]:
            if widgets_list:
                for i in range(widgets_list.count()):
                    item = widgets_list.item(i)
                    widget = widgets_list.itemWidget(item)

                    if current_track and widget.track_path == current_track:
                        widget.title_label.setGlowEnabled(enabled=True)
                        widget.duration_label.setGlowEnabled(enabled=True)
                    else:
                        widget.title_label.setGlowEnabled(enabled=False)
                        widget.duration_label.setGlowEnabled(enabled=False)


    def update_status_bar(self, status_tip=None):
        permanent_parts = []

        if self.player.current_track_index is not None:
            if self.player.reproduction_mode == "playing":
                permanent_parts.append("Playing")
            elif self.player.reproduction_mode == "paused":
                permanent_parts.append("Paused")

        permanent_parts.append(f"Volume: {self.volume}%")
        permanent_parts.append(f"Muted: {'on' if self.player.is_muted else 'off'}")
        permanent_parts.append(f"Shuffle: {'on' if self.player.is_shuffle_on else 'off'}")
        permanent_parts.append(f"Repeat: {self.player.repeat}")

        permanent_text = "   |   ".join(permanent_parts)

        if status_tip:
            full_text = f"{status_tip}   •   {permanent_text}"
        else:
            full_text = permanent_text

        self.status_bar.showMessage(full_text)


# --------------------------------- VOLUME ---------------------------------

    def handle_volume_button_click(self):
        self.player.toggle_mute(self.volume_slider.value())


    def update_volume_button(self, is_muted):
        icon = "volume_off.png" if is_muted else "volume_on.png"
        path = resource_path(f"assets/{icon}").replace("\\", "/")
        tooltip = "Unmute" if is_muted else "Mute"

        if self.current_main_size == "expanded":
            radius_left = "15px"
            radius_right = "15px"
            padding = "7px"
        else:
            radius_left = "10px"
            radius_right = "3px"
            padding = "7px 3px"

        self.volume_button.setToolTip(tooltip)
        self.volume_button.setStyleSheet(
            f"border-radius: {radius_right};"
            f"border-top-left-radius: {radius_left};"
            f"border-bottom-left-radius: {radius_left};"
            f"padding: {padding};"
            f"image: url({path})"
        )

        self.update_status_bar()


    def change_volume(self, value):
        self.player.audio_output.setVolume(value / 100)
        self.sync_volume_sliders(value)
        self.volume = value
        self.volume_slider.setToolTip(f"Volume: {self.volume}%")
        self.floating_volume_slider.setToolTip(f"Volume: {self.volume}%")
        self.update_status_bar()


    def sync_volume_sliders(self, value):
        self.volume_slider.blockSignals(True)
        self.floating_volume_slider.blockSignals(True)

        self.volume_slider.setValue(value)
        self.floating_volume_slider.setValue(value)

        self.volume_slider.blockSignals(False)
        self.floating_volume_slider.blockSignals(False)


    def toggle_floating_volume_slider(self):
        if self.floating_volume_panel.isVisible():
            self.floating_volume_panel.hide()
            self.on_volume_panel_closed()
            return

        self.floating_volume_panel.is_open = True

        button_pos = self.volume_button.mapToGlobal(QPoint(0, 0))

        self.floating_volume_panel.adjustSize()

        x = button_pos.x() + (self.volume_button.width() - self.floating_volume_panel.width()) // 2
        y = button_pos.y() - self.floating_volume_panel.height() - 5

        self.floating_volume_panel.move(x, y)
        self.floating_volume_panel.show()
        self.floating_volume_panel.raise_()

        path = resource_path("assets/arrow-down.png").replace("\\", "/")
        self.volume_toggle_button.setStyleSheet(f"image: url({path})")
        self.volume_toggle_button.setToolTip("Close volume slider")


    def on_volume_panel_closed(self):
        path = resource_path("assets/arrow-up.png").replace("\\", "/")
        self.volume_toggle_button.setStyleSheet(f"image: url({path})")
        self.volume_toggle_button.setToolTip("Open volume slider")


# --------------------------------- RESPONSIVE LAYOUT ---------------------------------

    def update_responsive_ui(self):
        container_size = self.main_widget.size()
        w, h = container_size.width(), container_size.height()

        self.update_pixmap(container_size)
        if self.floating_volume_panel.isVisible():
            self.floating_volume_panel.hide()

        mode = "compact" if w < 653 else "expanded"

        if mode != self.current_main_size:
            self.current_main_size = mode
            getattr(self, f"apply_{mode}_layout")()


    def apply_compact_layout(self):
        self.volume_slider.setVisible(False)
        self.volume_toggle_button.setVisible(True)
        self.volume_layout.setSpacing(1)
        self.update_volume_button(self.player.is_muted)

        self.track_outer_layout.removeWidget(self.track_inner_container)
        self.main_layout.insertWidget(1, self.track_inner_container)

        self.track_inner_layout.setContentsMargins(9,0,9,5)
        self.track_outer_container.setMinimumWidth(0)

        self.ten_forward_button.setVisible(False)
        self.ten_backward_button.setVisible(False)


    def apply_expanded_layout(self):
        self.volume_slider.setVisible(True)
        self.volume_toggle_button.setVisible(False)
        self.volume_layout.setSpacing(5)
        self.update_volume_button(self.player.is_muted)

        self.main_layout.removeWidget(self.track_inner_container)
        self.track_outer_layout.insertWidget(0, self.track_inner_container)

        self.track_inner_layout.setContentsMargins(0, 0, 0, 0)
        self.track_outer_container.setMinimumWidth(136)

        self.ten_forward_button.setVisible(True)
        self.ten_backward_button.setVisible(True)


    def update_pixmap(self, container_size):
        ratio = self.image_container.width() / self.image_container.height()

        if self.original_pixmap.isNull():
            return

        ratio = self.image_container.width() / self.image_container.height()

        if ratio > 4 or self.image_container.height() < 100:
            self.player_image.hide()
            return

        if self.view_player_image_action.isChecked():
            self.player_image.show()

        if 1.2 <= ratio <= 1.8:
            # Scale the image while keeping aspect ratio
            mode = Qt.AspectRatioMode.KeepAspectRatio
        else:
            # Scale the image while keeping aspect ratio, filling the container
            mode = Qt.AspectRatioMode.KeepAspectRatioByExpanding

        scaled = self.original_pixmap.scaled(container_size, mode, Qt.TransformationMode.SmoothTransformation)

        # Create a pixmap with the size of the container
        final_pixmap = QPixmap(container_size)
        final_pixmap.fill(Qt.GlobalColor.transparent)  # transparent background

        # Coordinates to center the scaled image
        x = (container_size.width() - scaled.width()) // 2
        y = (container_size.height() - scaled.height()) // 2

        # Draw the scaled image centered
        painter = QPainter(final_pixmap)
        painter.drawPixmap(x, y, scaled)
        painter.end()

        self.player_image.setPixmap(final_pixmap)


# --------------------------------- EVENTS ---------------------------------

    def event(self, event):
        if event.type() == QEvent.Type.StatusTip:
            return True

        return super().event(event)


    def eventFilter(self, obj, event):
        if obj == self.main_widget and event.type() == QEvent.Type.Resize:
            self.update_responsive_ui()

        if event.type() == QEvent.Type.Leave:
            if isinstance(obj, QMenu):
                self.update_status_bar("")

        if event.type() == QEvent.Type.MouseButtonPress:
            if self.floating_volume_panel.isVisible():

                global_pos = event.globalPosition().toPoint()

                # If click is inside the floating panel → do nothing
                if self.floating_volume_panel.frameGeometry().contains(global_pos):
                    return False

                # If click is on the toggle button → do nothing (avoid conflict)
                if self.volume_toggle_button.rect().contains(
                        self.volume_toggle_button.mapFromGlobal(global_pos)
                ):
                    return False

                # Any other click → close the panel
                self.floating_volume_panel.hide()

        return super().eventFilter(obj, event)


    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self._apply_resize_rules)


    def paintEvent(self, event):
        painter = QPainter(self)

        if self._bg_size != self.size():
            self._bg_size = self.size()
            self._bg_scaled = self._bg_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )

        x = (self.width() - self._bg_scaled.width()) // 2
        y = (self.height() - self._bg_scaled.height()) // 2

        painter.drawPixmap(x, y, self._bg_scaled)

        super().paintEvent(event)


    def _apply_resize_rules(self):
        h = self.height()

        self.main_layout.setStretch(1, 1 if h < 220 else 0)
        self.image_container.setVisible(h >= 216)
        self.status_bar.setVisible(h >= 200)
        self.menuBar().setVisible(h >= 140)


    def closeEvent(self, event):
        self.player.cleanup()
        event.accept()


# --------------------------- LOAD STYLES -----------------------------------

def load_stylesheet(relative_css_path):
    css_path = resource_path(relative_css_path)
    assets_dir = resource_path("assets").replace("\\", "/")

    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()

    # Replace any url("assets/...") with the actual absolute path
    css = css.replace('url("assets/', f'url("{assets_dir}/')

    return css


if __name__ == '__main__':
    app  = QApplication(sys.argv)
    app.setStyleSheet(load_stylesheet("styles/styles.css"))
    # app.setFont(QFont("Arial", 12))
    window = MainWindow()
    sys.exit(app.exec())
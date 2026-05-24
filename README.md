# Trek Music 🎵

![Trek Music demo](assets/demo.gif)

A desktop music player built with Python and PyQt6. Clean interface, responsive layout, and a focus on getting out of the way while you listen.

---

## Features

### Playback
- **Play/pause**, **previous/next** track, and **±10 second** seek buttons
- **Shuffle** (preserves original order, restores on unshuffle) and **repeat** modes: none / all / one
- Double-click any track to play it immediately
- Click a Library track not in the current queue to insert it next and play

### Library & Queue
- **Library tab** — your original file list, order preserved
- **Queue tab** — the active playback order, drag-and-drop reorderable and affected by shuffle
- Load audio files individually or scan an entire folder (including subfolders)
- **Add** to current playlist or **replace** playlist without losing your current track
- New tracks are shuffled into the queue if shuffle is active
- Right-click context menus: remove a track, add from Library to Queue, reset Queue back to Library order
- Supported formats: MP3, WAV, FLAC, OGG, M4A

### UI & Layout
- **Responsive layout**: at narrow widths, ±10s buttons collapse and the track name moves inline; the volume slider becomes a floating popup
- **Floating playlist dock**: detach the panel and move it anywhere, or close it to reclaim space
- **Marquee track name**: long titles scroll smoothly when they don't fit
- **Glow highlight**: the currently playing track glows in both Library and Queue lists
- **Progressive image scaling**: the decorative player image adapts its aspect ratio based on the available space; hides automatically at very small window heights
- Layered backgrounds with a fixed wallpaper behind all panels

### Volume
- Mute button with inline volume slider (expanded mode)
- Floating vertical volume popup (compact mode), closes on outside click
- Both sliders stay in sync at all times

### Status bar
- Live playback state, volume %, mute, shuffle, and repeat — always visible
- Contextual tips when hovering menu items

### Other
- **Wake lock** via `wakepy`: prevents the system from sleeping while music is playing
- Menu adapts between simple (empty queue) and advanced (add vs replace) modes automatically
- Keyboard shortcuts: `Ctrl+O` open files, `Ctrl+Shift+O` open folder, `Ctrl+L` toggle playlist, `Ctrl+I` toggle player image

---

## Architecture

The project is split into a logic layer and a UI layer with no circular dependencies:

- main.py — MainWindow, layout, event handling
- player.py — Player (QObject), all playback logic, pyqtSignal bus
- clickable_slider.py — QSlider subclass with seek-on-click and floating position/duration tooltip
- marquee_label.py — QLabel subclass with timer-driven scroll animation
- glow_label.py — QLabel subclass with custom paintEvent glow effect
- track_item_widget.py — Composite widget for playlist rows (icon + title + duration)
- custom_tab_widget.py — Tab container with checkable QPushButton tabs and context menu support
- dock_title_bar.py — Custom QDockWidget title bar with float/close buttons
- floating_volume_panel.py  — Frameless popup with rounded painted background

`Player` communicates upward exclusively through signals (`playback_state_changed`, `track_changed`, `playlist_changed`, `shuffle_state_changed`, `volume_state_changed`, `duration_changed`, 
`position_changed`). `MainWindow` owns the UI and connects to those signals — no circular imports.

---

## Requirements

PyQt6
mutagen
wakepy

Install:

```bash
pip install PyQt6 mutagen wakepy
```

---

## Running

```bash
python main.py
```

The app expects an `images/` folder and a `styles.css` in the working directory. See `resources.qrc` for the full asset list.

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+O` | Open audio files |
| `Ctrl+Shift+O` | Open folder |
| `Ctrl+L` | Toggle playlist panel |
| `Ctrl+I` | Toggle player image |

---

## License

MIT
import re
import datetime
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QScrollArea, QFrame, 
                             QSizePolicy, QFileDialog, QDialog)
from PySide6.QtCore import Qt, Signal, Slot
from engine.queue_item import QueueItem, Status, Mode
from gui.widgets.queue_row import QueueRow
from gui.widgets.progress_bar import LabelledProgressBar
from gui.icons import get_svg_icon, get_svg_pixmap
from config import load_config, save_config
from constants import VALID_URL_PREFIXES
from deps import checker

class DownloaderTab(QWidget):
    show_toast_requested = Signal(str)
    start_queue_requested = Signal()
    pause_queue_requested = Signal()
    cancel_queue_requested = Signal()
    clear_queue_requested = Signal()
    item_removed = Signal(str)  # item_id
    item_retry_requested = Signal(str) # item_id
    config_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = load_config()
        self.queue_items = []
        self.row_widgets = {}
        self.is_downloading = False
        self.is_paused = False
        self.init_ui()
        self.update_ui_state()

    def init_ui(self):
        # Base layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(14, 14, 14, 14)
        self.layout.setSpacing(10)

        # 1. Mode Row
        self.mode_layout = QHBoxLayout()
        self.mode_layout.setSpacing(10)
        
        self.mode_label = QLabel("Mode:", self)
        self.mode_label.setFixedWidth(120)
        self.mode_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.mode_label.setStyleSheet("color: #333333; font-size: 12px; font-family: 'Segoe UI';")
        self.mode_layout.addWidget(self.mode_label)

        # Mode Buttons
        self.mode_new_btn = QPushButton("New download", self)
        self.mode_new_btn.setIcon(get_svg_icon("ti-download", color="#1A5A9C", size=13))
        self.mode_new_btn.setFixedHeight(28)
        self.mode_new_btn.setCursor(Qt.PointingHandCursor)
        self.mode_new_btn.clicked.connect(lambda: self.set_mode(Mode.NEW_DOWNLOAD))
        self.mode_layout.addWidget(self.mode_new_btn, 1)

        self.mode_update_btn = QPushButton("Update playlist", self)
        self.mode_update_btn.setIcon(get_svg_icon("ti-refresh", color="#333333", size=13))
        self.mode_update_btn.setFixedHeight(28)
        self.mode_update_btn.setCursor(Qt.PointingHandCursor)
        self.mode_update_btn.clicked.connect(lambda: self.set_mode(Mode.UPDATE_PLAYLIST))
        self.mode_layout.addWidget(self.mode_update_btn, 1)

        self.layout.addLayout(self.mode_layout)

        # 2. URL Input Row
        self.url_layout = QHBoxLayout()
        self.url_layout.setSpacing(10)

        self.url_label = QLabel("URL:", self)
        self.url_label.setFixedWidth(120)
        self.url_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.url_label.setStyleSheet("color: #333333; font-size: 12px; font-family: 'Segoe UI';")
        self.url_layout.addWidget(self.url_label)

        # URL text field
        self.url_input = QLineEdit(self)
        self.url_input.setFixedHeight(24)
        self.url_input.setPlaceholderText("Paste YouTube or YouTube Music link here...")
        self.url_input.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #888888;
                border-radius: 2px;
                color: #111111;
                font-size: 12px;
                font-family: 'Segoe UI';
                padding: 0px 6px;
            }
        """)
        self.url_input.returnPressed.connect(self.add_url_to_queue)
        self.url_layout.addWidget(self.url_input, 1)

        # Add (+) button
        self.add_btn = QPushButton(self)
        self.add_btn.setFixedSize(28, 24)
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setIcon(get_svg_icon("ti-plus", color="#333333", size=15))
        self.add_btn.setToolTip("Add to queue (Enter)")
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #E8E8E8;
                border: 1px solid #888888;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #D8D8D8;
            }
        """)
        self.add_btn.clicked.connect(self.add_url_to_queue)
        self.url_layout.addWidget(self.add_btn)

        self.layout.addLayout(self.url_layout)

        # Inline Validation Error Label (under input, aligned with URL field)
        self.error_label_layout = QHBoxLayout()
        self.error_label_layout.setSpacing(0)
        self.error_label_spacer = QWidget(self)
        self.error_label_spacer.setFixedWidth(130) # 120 (label) + 10 (gap)
        self.error_label_layout.addWidget(self.error_label_spacer)
        
        self.validation_error_label = QLabel(self)
        self.validation_error_label.setStyleSheet("color: #C0392B; font-size: 11px; font-family: 'Segoe UI';")
        self.validation_error_label.setVisible(False)
        self.error_label_layout.addWidget(self.validation_error_label, 1)
        self.layout.addLayout(self.error_label_layout)

        # 3. Save To Row
        self.save_layout = QHBoxLayout()
        self.save_layout.setSpacing(10)

        self.save_label = QLabel("Save to:", self)
        self.save_label.setFixedWidth(120)
        self.save_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.save_label.setStyleSheet("color: #333333; font-size: 12px; font-family: 'Segoe UI';")
        self.save_layout.addWidget(self.save_label)

        self.save_folder_label = QLabel(self)
        self.save_folder_label.setFixedHeight(24)
        self.save_folder_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.save_folder_label.setStyleSheet("""
            QLabel {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 2px;
                color: #555555;
                font-size: 12px;
                font-family: 'Segoe UI';
                padding: 2px 6px;
            }
        """)
        self.save_layout.addWidget(self.save_folder_label, 1)

        self.folder_browse_btn = QPushButton(self)
        self.folder_browse_btn.setFixedSize(28, 24)
        self.folder_browse_btn.setCursor(Qt.PointingHandCursor)
        self.folder_browse_btn.setIcon(get_svg_icon("ti-folder", color="#333333", size=14))
        self.folder_browse_btn.setToolTip("Change download folder")
        self.folder_browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #E8E8E8;
                border: 1px solid #888888;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #D8D8D8;
            }
        """)
        self.folder_browse_btn.clicked.connect(self.browse_folder)
        self.save_layout.addWidget(self.folder_browse_btn)

        self.layout.addLayout(self.save_layout)

        # 4. Queue Row
        self.queue_layout = QHBoxLayout()
        self.queue_layout.setSpacing(10)

        self.queue_label = QLabel("Queue — 0:", self)
        self.queue_label.setFixedWidth(120)
        self.queue_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.queue_label.setStyleSheet("color: #333333; font-size: 12px; font-family: 'Segoe UI'; margin-top: 4px;")
        self.queue_layout.addWidget(self.queue_label)

        # Scroll Area for Queue items
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #AAAAAA;
                background-color: #FFFFFF;
                border-radius: 2px;
            }
        """)
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: #FFFFFF;")
        self.scroll_list_layout = QVBoxLayout(self.scroll_content)
        self.scroll_list_layout.setContentsMargins(4, 4, 4, 4)
        self.scroll_list_layout.setSpacing(4)
        self.scroll_list_layout.setAlignment(Qt.AlignTop)
        
        self.scroll_area.setWidget(self.scroll_content)
        self.queue_layout.addWidget(self.scroll_area, 1)
        self.layout.addLayout(self.queue_layout)

        # Empty State Overlay inside Queue area
        self.empty_state = QFrame(self.scroll_area)
        self.empty_state.setStyleSheet("""
            QFrame {
                border: 1px dashed #CCCCCC;
                background-color: #FAFAFA;
                border-radius: 2px;
            }
        """)
        self.empty_layout = QVBoxLayout(self.empty_state)
        self.empty_layout.setAlignment(Qt.AlignCenter)
        self.empty_layout.setSpacing(4)

        self.empty_icon = QLabel(self)
        self.empty_icon.setPixmap(get_svg_pixmap("ti-playlist", color="#CCCCCC", size=28))
        self.empty_icon.setAlignment(Qt.AlignCenter)
        self.empty_layout.addWidget(self.empty_icon)

        self.empty_title = QLabel("No items in queue", self)
        self.empty_title.setStyleSheet("color: #AAAAAA; font-size: 12px; font-family: 'Segoe UI'; font-weight: 500;")
        self.empty_title.setAlignment(Qt.AlignCenter)
        self.empty_layout.addWidget(self.empty_title)

        self.empty_subtitle = QLabel("Paste a link above and press + to add", self)
        self.empty_subtitle.setStyleSheet("color: #AAAAAA; font-size: 11px; font-family: 'Segoe UI';")
        self.empty_subtitle.setAlignment(Qt.AlignCenter)
        self.empty_layout.addWidget(self.empty_subtitle)

        # We will position the empty state by resizing it inside the scroll area
        # This is handled in resizeEvent
        self.empty_state.setVisible(True)

        # 5. Collapsible Error Panel (hidden by default)
        self.error_panel = QWidget(self)
        self.error_panel.setVisible(False)
        self.error_panel_layout = QVBoxLayout(self.error_panel)
        self.error_panel_layout.setContentsMargins(130, 0, 0, 0) # align with queue list
        self.error_panel_layout.setSpacing(0)

        # Error Panel Header
        self.err_header = QFrame(self.error_panel)
        self.err_header.setFixedHeight(28)
        self.err_header.setStyleSheet("""
            QFrame {
                background-color: #FDE8E8;
                border: 1px solid #C0392B;
                border-bottom: none;
                border-top-left-radius: 2px;
                border-top-right-radius: 2px;
            }
        """)
        self.err_header_layout = QHBoxLayout(self.err_header)
        self.err_header_layout.setContentsMargins(8, 0, 8, 0)
        
        self.err_header_icon = QLabel(self.err_header)
        self.err_header_icon.setPixmap(get_svg_pixmap("ti-alert-triangle", color="#C0392B", size=14))
        self.err_header_layout.addWidget(self.err_header_icon)

        self.err_header_title = QLabel("Errors & Skips", self.err_header)
        self.err_header_title.setStyleSheet("color: #922B21; font-size: 12px; font-weight: bold; font-family: 'Segoe UI';")
        self.err_header_layout.addWidget(self.err_header_title)
        self.err_header_layout.addStretch(1)

        self.err_collapse_btn = QPushButton(self.err_header)
        self.err_collapse_btn.setFixedSize(20, 20)
        self.err_collapse_btn.setCursor(Qt.PointingHandCursor)
        self.err_collapse_btn.setIcon(get_svg_icon("ti-chevron-up", color="#C0392B", size=12))
        self.err_collapse_btn.setStyleSheet("background: transparent; border: none;")
        self.err_collapse_btn.clicked.connect(self.toggle_error_panel)
        self.err_header_layout.addWidget(self.err_collapse_btn)
        
        self.error_panel_layout.addWidget(self.err_header)

        # Error Panel Body
        self.err_body = QFrame(self.error_panel)
        self.err_body.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #C0392B;
                border-bottom-left-radius: 2px;
                border-bottom-right-radius: 2px;
            }
        """)
        self.err_body_layout = QVBoxLayout(self.err_body)
        self.err_body_layout.setContentsMargins(8, 8, 8, 8)
        self.err_body_layout.setSpacing(6)

        # Scroll area inside error panel
        self.err_scroll = QScrollArea(self.err_body)
        self.err_scroll.setWidgetResizable(True)
        self.err_scroll.setFixedHeight(90)
        self.err_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.err_scroll_content = QWidget()
        self.err_scroll_list = QVBoxLayout(self.err_scroll_content)
        self.err_scroll_list.setContentsMargins(0, 0, 0, 0)
        self.err_scroll_list.setSpacing(8)
        self.err_scroll_list.setAlignment(Qt.AlignTop)
        
        self.err_scroll.setWidget(self.err_scroll_content)
        self.err_body_layout.addWidget(self.err_scroll)

        # Copy error button
        self.err_footer_layout = QHBoxLayout()
        self.err_footer_layout.addStretch(1)
        self.err_copy_btn = QPushButton("Copy error log", self.err_body)
        self.err_copy_btn.setIcon(get_svg_icon("ti-copy", color="#333333", size=12))
        self.err_copy_btn.setFixedHeight(20)
        self.err_copy_btn.setCursor(Qt.PointingHandCursor)
        self.err_copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #E8E8E8;
                border: 1px solid #888888;
                border-radius: 2px;
                font-size: 11px;
                color: #333333;
                font-family: 'Segoe UI';
                padding: 0 10px;
            }
            QPushButton:hover {
                background-color: #D8D8D8;
            }
        """)
        self.err_copy_btn.clicked.connect(self.copy_error_log)
        self.err_footer_layout.addWidget(self.err_copy_btn)
        self.err_body_layout.addLayout(self.err_footer_layout)

        self.error_panel_layout.addWidget(self.err_body)
        self.layout.addWidget(self.error_panel)

        # 6. Dependency Status Footer
        self.footer_line = QFrame(self)
        self.footer_line.setFixedHeight(1)
        self.footer_line.setStyleSheet("background-color: #CCCCCC;")
        self.layout.addWidget(self.footer_line)

        self.dep_status_layout = QHBoxLayout()
        self.dep_status_layout.setContentsMargins(130, 0, 0, 0) # Align with form
        
        self.dep_status_icon = QLabel(self)
        self.dep_status_icon.setFixedSize(14, 14)
        self.dep_status_layout.addWidget(self.dep_status_icon)

        self.dep_status_text = QLabel(self)
        self.dep_status_text.setStyleSheet("color: #666666; font-size: 11px; font-family: 'Segoe UI';")
        self.dep_status_layout.addWidget(self.dep_status_text)
        self.dep_status_layout.addStretch(1)
        self.layout.addLayout(self.dep_status_layout)

        # 7. Main Button Bar
        self.btn_bar_layout = QHBoxLayout()
        self.btn_bar_layout.setContentsMargins(130, 4, 0, 4)
        self.btn_bar_layout.setSpacing(8)

        self.start_btn = QPushButton("Start queue", self)
        self.start_btn.setFixedHeight(30)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self.on_start_btn_clicked)
        self.btn_bar_layout.addWidget(self.start_btn, 1)

        self.clear_btn = QPushButton("Clear all", self)
        self.clear_btn.setFixedHeight(30)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self.on_clear_btn_clicked)
        self.btn_bar_layout.addWidget(self.clear_btn, 1)

        self.layout.addLayout(self.btn_bar_layout)

        # 8. Bottom Labelled Progress Bars (hidden by default)
        self.item_progress = LabelledProgressBar("Item progress", fill_color="#4A90D9", parent=self)
        self.layout.addWidget(self.item_progress)
        self.item_progress.setVisible(False)

        self.overall_progress = LabelledProgressBar("Overall progress", fill_color="#27AE60", parent=self)
        self.layout.addWidget(self.overall_progress)
        self.overall_progress.setVisible(False)

        # Internal states
        self.selected_mode = Mode.NEW_DOWNLOAD
        self.is_downloading = False
        self.is_error_expanded = True
        self.error_records = []

        # Load initial config values
        self.save_folder_label.setText(self.config.download_folder)
        self.set_mode(Mode.NEW_DOWNLOAD)
        self.update_dep_footer()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.url_input.text():
                self.url_input.clear()
                self.clear_validation_error()
                event.accept()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def set_mode(self, mode: Mode):
        self.selected_mode = mode
        if mode == Mode.NEW_DOWNLOAD:
            self.mode_new_btn.setStyleSheet("""
                QPushButton {
                    background-color: #DAE8F8;
                    border: 1px solid #4A90D9;
                    color: #1A5A9C;
                    font-size: 11px;
                    font-weight: 500;
                    border-radius: 2px;
                    font-family: 'Segoe UI';
                }
            """)
            self.mode_update_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E8E8E8;
                    border: 1px solid #888888;
                    color: #333333;
                    font-size: 11px;
                    border-radius: 2px;
                    font-family: 'Segoe UI';
                }
                QPushButton:hover {
                    background-color: #D8D8D8;
                }
            """)
        else:
            self.mode_update_btn.setStyleSheet("""
                QPushButton {
                    background-color: #DAE8F8;
                    border: 1px solid #4A90D9;
                    color: #1A5A9C;
                    font-size: 11px;
                    font-weight: 500;
                    border-radius: 2px;
                    font-family: 'Segoe UI';
                }
            """)
            self.mode_new_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E8E8E8;
                    border: 1px solid #888888;
                    color: #333333;
                    font-size: 11px;
                    border-radius: 2px;
                    font-family: 'Segoe UI';
                }
                QPushButton:hover {
                    background-color: #D8D8D8;
                }
            """)

    def browse_folder(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Download Folder", self.save_folder_label.text()
        )
        if dir_path:
            self.save_folder_label.setText(dir_path)
            self.config.download_folder = dir_path
            save_config(self.config)
            self.config_changed.emit()

    def refresh_config(self):
        self.config = load_config()
        self.save_folder_label.setText(self.config.download_folder)

    def update_dep_footer(self):
        ytdlp_ver = checker.get_ytdlp_version()
        ffmpeg_ver = checker.get_ffmpeg_version()
        if ytdlp_ver and ffmpeg_ver:
            # Shorten ffmpeg version
            ffmpeg_short = ffmpeg_ver.split()[2] if len(ffmpeg_ver.split()) > 2 else ffmpeg_ver
            self.dep_status_icon.setPixmap(get_svg_pixmap("ti-circle-check", color="#27AE60", size=14))
            self.dep_status_text.setText(f"yt-dlp {ytdlp_ver} · ffmpeg {ffmpeg_short[:12]} — ready")
        else:
            self.dep_status_icon.setPixmap(get_svg_pixmap("ti-alert-circle", color="#E67E22", size=14))
            self.dep_status_text.setText("Dependencies missing or corrupted. Check settings.")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Position empty state to fill scroll area body
        rect = self.scroll_area.viewport().rect()
        self.empty_state.setGeometry(rect)

    def show_validation_error(self, text: str):
        self.validation_error_label.setText(text)
        self.validation_error_label.setVisible(True)
        self.url_input.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #C0392B;
                border-radius: 2px;
                color: #111111;
                font-size: 12px;
                font-family: 'Segoe UI';
                padding: 0px 6px;
            }
        """)

    def clear_validation_error(self):
        self.validation_error_label.setVisible(False)
        self.url_input.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #888888;
                border-radius: 2px;
                color: #111111;
                font-size: 12px;
                font-family: 'Segoe UI';
                padding: 0px 6px;
            }
        """)

    def add_url_to_queue(self):
        url = self.url_input.text().strip()
        if not url:
            return

        self.clear_validation_error()

        # Validate URL prefix
        valid_prefix = False
        for prefix in VALID_URL_PREFIXES:
            if url.startswith(prefix):
                valid_prefix = True
                break

        if not valid_prefix:
            self.show_validation_error("Not a recognised YouTube or YouTube Music link")
            return

        # Check playlist requirements for Update playlist mode
        is_playlist = "playlist" in url or "list=" in url
        if self.selected_mode == Mode.UPDATE_PLAYLIST and not is_playlist:
            self.show_validation_error("Update playlist mode requires a playlist link")
            return

        # Check if URL already in queue
        for existing in self.queue_items:
            if existing.url == url and existing.status not in (Status.DONE, Status.CANCELLED, Status.SKIPPED_DUPLICATE):
                self.show_validation_error("This URL is already in the queue")
                return

        # Create QueueItem
        item = QueueItem(url=url, mode=self.selected_mode)
        item.is_playlist = is_playlist
        if is_playlist:
            item.title = "Playlist: " + url[:30] + "..."
            item.subtitle = "Pending playlist metadata resolution..."
        else:
            item.title = "Video: " + url[:30] + "..."
            item.subtitle = "Pending metadata resolution..."
            
        # Resolve archive file path if it's Update mode
        if item.mode == Mode.UPDATE_PLAYLIST:
            # We will extract the playlist ID from the URL as the file name
            playlist_id_match = re.search(r"[&?]list=([^&]+)", url)
            playlist_id = playlist_id_match.group(1) if playlist_id_match else "playlist"
            from utils.paths import ARCH_DIR
            item.archive_path = ARCH_DIR / f"{playlist_id}.txt"

        self.queue_items.append(item)
        self.url_input.clear()

        # Add Row to UI
        row = QueueRow(item, self.scroll_content)
        row.remove_clicked.connect(self.remove_item)
        row.retry_clicked.connect(self.item_retry_requested.emit)
        self.scroll_list_layout.addWidget(row)
        self.row_widgets[item.id] = row

        self.update_ui_state()
        self.show_toast_requested.emit("Added to queue")

    def remove_item(self, item_id: str):
        # Notify engine if active item is deleted
        self.item_removed.emit(item_id)
        
        # Remove from list
        target_item = None
        for item in self.queue_items:
            if item.id == item_id:
                target_item = item
                break
                
        if target_item:
            self.queue_items.remove(target_item)
            
        # Remove widget
        if item_id in self.row_widgets:
            widget = self.row_widgets[item_id]
            self.scroll_list_layout.removeWidget(widget)
            widget.deleteLater()
            del self.row_widgets[item_id]

        # Update empty error panel items too if relevant
        self.error_records = [r for r in self.error_records if r["id"] != item_id]
        self.refresh_error_panel()

        self.update_ui_state()

    def update_ui_state(self):
        count = len(self.queue_items)
        self.queue_label.setText(f"Queue — {count}:")
        self.empty_state.setVisible(count == 0)

        # Update button bar depending on state (downloading vs idle)
        if self.is_downloading:
            self.start_btn.setText("Pause")
            self.start_btn.setIcon(get_svg_icon("ti-player-pause", color="#333333", size=13))
            self.start_btn.setEnabled(True)
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E8E8E8;
                    border: 1px solid #888888;
                    color: #333333;
                    font-size: 12px;
                    font-family: 'Segoe UI';
                    padding: 0 16px;
                    border-radius: 2px;
                }
                QPushButton:hover {
                    background-color: #D8D8D8;
                }
            """)

            self.clear_btn.setText("Cancel all")
            self.clear_btn.setIcon(get_svg_icon("ti-x", color="#C0392B", size=13))
            self.clear_btn.setEnabled(True)
            self.clear_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFF8F8;
                    border: 1px solid #C0392B;
                    color: #C0392B;
                    font-size: 12px;
                    font-family: 'Segoe UI';
                    font-weight: 500;
                    padding: 0 16px;
                    border-radius: 2px;
                }
                QPushButton:hover {
                    background-color: #FDE8E8;
                }
            """)
        else:
            self.start_btn.setText("Start queue")
            self.start_btn.setIcon(get_svg_icon("ti-player-play", color="#1A5A9C", size=13))
            # Enable if there are any non-done items in queue
            has_pending = any(item.status in (Status.QUEUED, Status.PAUSED_NETWORK) for item in self.queue_items)
            self.start_btn.setEnabled(has_pending)
            
            if has_pending:
                self.start_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #DAE8F8;
                        border: 1px solid #4A90D9;
                        color: #1A5A9C;
                        font-size: 12px;
                        font-family: 'Segoe UI';
                        font-weight: 500;
                        padding: 0 16px;
                        border-radius: 2px;
                    }
                    QPushButton:hover {
                        background-color: #C0DBF5;
                    }
                """)
            else:
                self.start_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #F0F0F0;
                        border: 1px solid #CCCCCC;
                        color: #AAAAAA;
                        font-size: 12px;
                        font-family: 'Segoe UI';
                        padding: 0 16px;
                        border-radius: 2px;
                    }
                """)

            self.clear_btn.setText("Clear all")
            self.clear_btn.setIcon(get_svg_icon("ti-rotate-clockwise", color="#333333", size=13))
            self.clear_btn.setEnabled(count > 0)
            self.clear_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E8E8E8;
                    border: 1px solid #888888;
                    color: #333333;
                    font-size: 12px;
                    font-family: 'Segoe UI';
                    padding: 0 16px;
                    border-radius: 2px;
                }
                QPushButton:hover {
                    background-color: #D8D8D8;
                }
                QPushButton:disabled {
                    background-color: #F0F0F0;
                    color: #AAAAAA;
                    border-color: #CCCCCC;
                }
            """)

        # Hide progress bars if not downloading and not paused
        show_progress = self.is_downloading or self.is_paused
        self.item_progress.setVisible(show_progress)
        self.overall_progress.setVisible(show_progress)

    def on_start_btn_clicked(self):
        if self.is_downloading:
            self.pause_queue_requested.emit()
        else:
            self.start_queue_requested.emit()

    def on_clear_btn_clicked(self):
        if self.is_downloading:
            self.cancel_queue_requested.emit()
        else:
            self.clear_queue_requested.emit()

    def set_downloading(self, downloading: bool):
        self.is_downloading = downloading
        if downloading:
            self.is_paused = False
        self.update_ui_state()

    def set_paused(self, paused: bool):
        self.is_paused = paused
        self.update_ui_state()

    def update_item_row(self, item: QueueItem):
        if item.id in self.row_widgets:
            self.row_widgets[item.id].update_state()

    def add_error_record(self, item_id: str, title: str, reason: str):
        record = {
            "id": item_id,
            "title": title,
            "reason": reason,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        }
        self.error_records.append(record)
        self.refresh_error_panel()
        self.error_panel.setVisible(True)

    def refresh_error_panel(self):
        # Clear current error widgets
        while self.err_scroll_list.count() > 0:
            item = self.err_scroll_list.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not self.error_records:
            self.error_panel.setVisible(False)
            return

        for rec in self.error_records:
            entry = QFrame(self.err_scroll_content)
            entry.setStyleSheet("QFrame { background: transparent; }")
            entry_layout = QVBoxLayout(entry)
            entry_layout.setContentsMargins(0, 0, 0, 0)
            entry_layout.setSpacing(1)

            t_layout = QHBoxLayout()
            t_layout.setContentsMargins(0, 0, 0, 0)
            
            title = QLabel(rec["title"], entry)
            title.setStyleSheet("color: #111111; font-size: 11px; font-weight: bold; font-family: 'Segoe UI';")
            t_layout.addWidget(title)
            
            t_layout.addStretch(1)
            
            ts = QLabel(rec["time"], entry)
            ts.setStyleSheet("color: #999999; font-size: 10px; font-family: 'Segoe UI';")
            t_layout.addWidget(ts)
            entry_layout.addLayout(t_layout)

            reason = QLabel(rec["reason"], entry)
            reason.setWordWrap(True)
            reason.setStyleSheet("color: #C0392B; font-size: 11px; font-family: 'Segoe UI';")
            entry_layout.addWidget(reason)

            # Divider line
            divider = QFrame(entry)
            divider.setFixedHeight(1)
            divider.setStyleSheet("background-color: #EEEEEE;")
            entry_layout.addWidget(divider)

            self.err_scroll_list.addWidget(entry)

    def toggle_error_panel(self):
        self.is_error_expanded = not self.is_error_expanded
        self.err_body.setVisible(self.is_error_expanded)
        icon_name = "ti-chevron-down" if not self.is_error_expanded else "ti-chevron-up"
        self.err_collapse_btn.setIcon(get_svg_icon(icon_name, color="#C0392B", size=12))

    def copy_error_log(self):
        text = ""
        for rec in self.error_records:
            text += f"[{rec['time']}] {rec['title']}\nError: {rec['reason']}\n" + "-"*40 + "\n"
            
        if text:
            from PySide6.QtGui import QGuiApplication
            QGuiApplication.clipboard().setText(text)
            self.show_toast_requested.emit("Copied to clipboard")

    def update_item_progress(self, item_title: str, percent: float, speed_str: str):
        self.item_progress.setLeftText(f"Item progress — {item_title}")
        self.item_progress.setRightText(f"{int(percent)}% · {speed_str}")
        self.item_progress.setValue(int(percent))

    def update_overall_progress(self):
        total_tracks = 0
        downloaded_tracks = 0
        
        for item in self.queue_items:
            t_count = item.track_count if item.track_count > 0 else 1
            total_tracks += t_count
            
            if item.status in (Status.DONE, Status.SKIPPED_DUPLICATE):
                downloaded_tracks += t_count
            elif item.status == Status.DOWNLOADING:
                downloaded_tracks += item.tracks_downloaded
            elif item.status in (Status.ERROR, Status.CANCELLED, Status.SKIPPED):
                downloaded_tracks += item.tracks_downloaded
                
        percent = int(downloaded_tracks * 100 / total_tracks) if total_tracks else 0
        
        self.overall_progress.setLeftText("Overall progress")
        self.overall_progress.setRightText(f"Track {downloaded_tracks} of {total_tracks}")
        self.overall_progress.setValue(percent)

    def clear_all_error_records(self):
        self.error_records.clear()
        self.refresh_error_panel()
        self.error_panel.setVisible(False)

class DownloadSummaryDialog(QDialog):
    def __init__(self, successes, errors, failed_names, parent=None):
        super().__init__(parent)
        self.retry_requested = False
        self.setWindowTitle("Download Summary")
        self.setFixedSize(400, 320 if errors else 180)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet("background-color: #F8F9FA;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Header Row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        icon_label = QLabel(self)
        icon_name = "ti-circle-check" if not errors else "ti-alert-circle"
        icon_color = "#27AE60" if not errors else "#E74C3C"
        icon_label.setPixmap(get_svg_pixmap(icon_name, color=icon_color, size=24))
        header_layout.addWidget(icon_label)
        
        title_label = QLabel("Queue completed" if not errors else "Completed with errors", self)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #222222; font-family: 'Segoe UI';")
        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        layout.addLayout(header_layout)
        
        # Summary details
        details_label = QLabel(f"Successfully downloaded: {successes} track{'s' if successes != 1 else ''}\nFailed: {errors} track{'s' if errors != 1 else ''}", self)
        details_label.setStyleSheet("font-size: 12px; color: #555555; font-family: 'Segoe UI'; line-height: 1.4;")
        layout.addWidget(details_label)
        
        # If there are errors, show the list of failed song names
        if errors:
            layout.addWidget(QLabel("Failed songs:", self, styleSheet="font-weight: bold; font-size: 11px; color: #333333; font-family: 'Segoe UI';"))
            
            scroll = QScrollArea(self)
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("QScrollArea { border: 1px solid #DDDDDD; background-color: #FFFFFF; border-radius: 2px; }")
            
            scroll_content = QWidget()
            scroll_content.setStyleSheet("background-color: #FFFFFF;")
            scroll_layout = QVBoxLayout(scroll_content)
            scroll_layout.setContentsMargins(8, 8, 8, 8)
            scroll_layout.setSpacing(4)
            scroll_layout.setAlignment(Qt.AlignTop)
            
            for name in failed_names:
                lbl = QLabel(name, scroll_content)
                lbl.setWordWrap(True)
                lbl.setStyleSheet("font-size: 11px; color: #C0392B; font-family: 'Segoe UI';")
                scroll_layout.addWidget(lbl)
                
            scroll.setWidget(scroll_content)
            layout.addWidget(scroll, 1)
            
        # Button bar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        if errors:
            self.retry_btn = QPushButton("Retry failed items", self)
            self.retry_btn.setFixedHeight(28)
            self.retry_btn.setCursor(Qt.PointingHandCursor)
            self.retry_btn.setStyleSheet("""
                QPushButton {
                    background-color: #DAE8F8;
                    border: 1px solid #4A90D9;
                    color: #1A5A9C;
                    font-size: 11px;
                    font-weight: 500;
                    border-radius: 2px;
                    font-family: 'Segoe UI';
                    padding: 0 12px;
                }
                QPushButton:hover {
                    background-color: #C0DBF5;
                }
            """)
            self.retry_btn.clicked.connect(self.on_retry_clicked)
            btn_layout.addWidget(self.retry_btn)
            
        close_btn = QPushButton("Close", self)
        close_btn.setFixedHeight(28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #E8E8E8;
                border: 1px solid #888888;
                border-radius: 2px;
                font-size: 11px;
                color: #333333;
                font-family: 'Segoe UI';
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #D8D8D8;
            }
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addStretch(1)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
    def on_retry_clicked(self):
        self.retry_requested = True
        self.accept()

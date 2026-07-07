from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QGroupBox, QCheckBox, 
                             QFileDialog, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QThread
from gui.widgets.dep_card import DepCard
from gui.icons import get_svg_icon
from config import Config, load_config, save_config
from deps import checker
from deps.fetcher import FetchWorker
from utils.paths import YTDLP_EXE, FFMPEG_EXE
from utils.net import get_request
import logging

logger = logging.getLogger("YTMusicDownloader")

class YtdlpVersionCheckWorker(QThread):
    done = Signal(str, str) # current, latest
    failed = Signal(str)

    def run(self):
        try:
            current = checker.get_ytdlp_version() or "unknown"
            # Get latest tag from GitHub releases API
            from constants import YTDLP_RELEASES_API
            r = get_request(YTDLP_RELEASES_API, timeout=10)
            r.raise_for_status()
            latest = r.json().get("tag_name", "unknown")
            self.done.emit(current, latest)
        except Exception as e:
            self.failed.emit(str(e))

class YtdlpUpdateWorker(QThread):
    progress = Signal(int)
    done = Signal(str)
    failed = Signal(str)

    def run(self):
        try:
            import subprocess
            # Replaces itself in place
            args = [str(YTDLP_EXE), "-U"]
            p = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            pct = 10
            for line in p.stdout:
                logger.info(f"[yt-dlp-update] {line.strip()}")
                pct = min(pct + 15, 95)
                self.progress.emit(pct)
            p.wait()
            if p.returncode == 0:
                new_ver = checker.get_ytdlp_version() or "updated"
                self.done.emit(new_ver)
            else:
                self.failed.emit("Update process exited with non-zero status.")
        except Exception as e:
            self.failed.emit(str(e))

class FfmpegVersionCheckWorker(QThread):
    done = Signal(str, str) # current, latest
    failed = Signal(str)

    def run(self):
        try:
            current = checker.get_ffmpeg_version() or "unknown"
            r = get_request("https://www.gyan.dev/ffmpeg/builds/release-version", timeout=10)
            r.raise_for_status()
            latest = r.text.strip()
            self.done.emit(current, latest)
        except Exception as e:
            self.failed.emit(str(e))

class SettingsTab(QWidget):
    show_toast_requested = Signal(str)
    config_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = load_config()
        self.init_ui()
        self.load_settings_into_ui()

    def init_ui(self):
        # Base layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(14, 14, 14, 14)
        self.layout.setSpacing(10)

        # Form container layout
        self.form_layout = QVBoxLayout()
        self.form_layout.setSpacing(8)

        # Helper to create label + widget row
        def create_form_row(label_text, widget):
            row = QHBoxLayout()
            row.setSpacing(10)
            label = QLabel(label_text, self)
            label.setFixedWidth(120)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            label.setStyleSheet("color: #333333; font-size: 12px; font-family: 'Segoe UI';")
            row.addWidget(label)
            from PySide6.QtWidgets import QLayout
            if isinstance(widget, QLayout):
                row.addLayout(widget)
            else:
                row.addWidget(widget)
            return row

        # 1. Download folder row
        self.folder_layout = QHBoxLayout()
        self.folder_layout.setSpacing(4)
        
        self.folder_input = QLabel(self)
        self.folder_input.setFixedHeight(24)
        self.folder_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.folder_input.setStyleSheet("""
            QLabel {
                background-color: #FFFFFF;
                border: 1px solid #888888;
                border-radius: 2px;
                padding: 2px 6px;
                color: #111111;
                font-size: 12px;
                font-family: 'Segoe UI';
            }
        """)
        self.folder_layout.addWidget(self.folder_input, 1)

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
        self.folder_layout.addWidget(self.folder_browse_btn)

        self.form_layout.addLayout(create_form_row("Download folder:", self.folder_layout))

        # 2. Filename pattern row
        self.pattern_combo = QComboBox(self)
        self.pattern_combo.setFixedHeight(24)
        self.pattern_combo.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #888888;
                border-radius: 2px;
                color: #111111;
                font-size: 12px;
                font-family: 'Segoe UI';
                padding-left: 4px;
            }
        """)
        self.pattern_combo.addItem("%(title)s")
        self.pattern_combo.addItem("%(title)s - %(artist)s")
        self.form_layout.addLayout(create_form_row("Filename pattern:", self.pattern_combo))

        # 3. Audio quality row (read-only label since it is fixed to Best Available)
        self.quality_label = QLabel("Best available", self)
        self.quality_label.setFixedHeight(24)
        self.quality_label.setStyleSheet("""
            QLabel {
                background-color: #F0F0F0;
                border: 1px solid #CCCCCC;
                border-radius: 2px;
                color: #555555;
                font-size: 12px;
                font-family: 'Segoe UI';
                padding-left: 6px;
                padding-top: 2px;
            }
        """)
        self.form_layout.addLayout(create_form_row("Audio quality:", self.quality_label))

        self.layout.addLayout(self.form_layout)

        # 4. Post-processing Groupbox
        self.post_group = QGroupBox("Post-processing", self)
        self.post_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                margin-top: 8px;
                padding-top: 10px;
                font-family: 'Segoe UI';
                font-size: 12px;
                font-weight: 500;
                color: #333333;
                background-color: #FAFAFA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 3px;
            }
        """)
        self.post_layout = QVBoxLayout(self.post_group)
        self.post_layout.setContentsMargins(12, 8, 12, 8)
        self.post_layout.setSpacing(6)

        self.thumb_check = QCheckBox("Embed thumbnail (square-crop)", self.post_group)
        self.thumb_check.setStyleSheet("QCheckBox { font-size: 11px; font-family: 'Segoe UI'; color: #333333; }")
        self.post_layout.addWidget(self.thumb_check)

        self.meta_check = QCheckBox("Embed metadata", self.post_group)
        self.meta_check.setStyleSheet("QCheckBox { font-size: 11px; font-family: 'Segoe UI'; color: #333333; }")
        self.post_layout.addWidget(self.meta_check)

        self.layout.addWidget(self.post_group)

        # 5. Dependencies Groupbox
        self.deps_group = QGroupBox("Dependencies", self)
        self.deps_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                margin-top: 8px;
                padding-top: 10px;
                font-family: 'Segoe UI';
                font-size: 12px;
                font-weight: 500;
                color: #333333;
                background-color: #FAFAFA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 3px;
            }
        """)
        self.deps_layout = QHBoxLayout(self.deps_group)
        self.deps_layout.setContentsMargins(12, 10, 12, 10)
        self.deps_layout.setSpacing(8)

        self.ytdlp_card = DepCard("yt-dlp", self.deps_group)
        self.ytdlp_card.check_update_clicked.connect(self.check_ytdlp_update)
        self.ytdlp_card.update_now_clicked.connect(self.update_ytdlp)
        self.deps_layout.addWidget(self.ytdlp_card)

        self.ffmpeg_card = DepCard("ffmpeg", self.deps_group)
        self.ffmpeg_card.check_update_clicked.connect(self.check_ffmpeg_update)
        self.ffmpeg_card.update_now_clicked.connect(self.update_ffmpeg)
        self.deps_layout.addWidget(self.ffmpeg_card)

        self.layout.addWidget(self.deps_group)
        self.layout.addStretch(1)

        # 6. Button Bar
        self.btn_layout = QHBoxLayout()
        self.btn_layout.setSpacing(8)
        
        self.save_btn = QPushButton("Save settings", self)
        self.save_btn.setIcon(get_svg_icon("ti-device-floppy", color="#1A5A9C", size=14))
        self.save_btn.setFixedHeight(30)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet("""
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
        self.save_btn.clicked.connect(self.save_settings)
        self.btn_layout.addWidget(self.save_btn)

        self.reset_btn = QPushButton("Reset to defaults", self)
        self.reset_btn.setIcon(get_svg_icon("ti-rotate-clockwise", color="#333333", size=14))
        self.reset_btn.setFixedHeight(30)
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setStyleSheet("""
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
        self.reset_btn.clicked.connect(self.reset_defaults)
        self.btn_layout.addWidget(self.reset_btn)

        self.layout.addLayout(self.btn_layout)

        # Setup workers
        self.check_worker = None
        self.update_worker = None
        self.ffmpeg_fetcher = None

    def load_settings_into_ui(self):
        self.folder_input.setText(self.config.download_folder)
        # Select defaults (only one option for v1, but set anyway)
        idx_pattern = self.pattern_combo.findText(self.config.filename_pattern)
        if idx_pattern >= 0:
            self.pattern_combo.setCurrentIndex(idx_pattern)
            
        self.thumb_check.setChecked(self.config.embed_thumbnail)
        self.meta_check.setChecked(self.config.embed_metadata)

        # Refresh dependency cards
        self.refresh_dep_cards()

    def refresh_dep_cards(self):
        ytdlp_ver = checker.get_ytdlp_version()
        if ytdlp_ver:
            self.ytdlp_card.set_up_to_date(ytdlp_ver)
        else:
            self.ytdlp_card.set_update_available("missing", "latest")
            
        ffmpeg_ver = checker.get_ffmpeg_version()
        if ffmpeg_ver:
            # ffmpeg version is long, elide/shorten
            short_ver = ffmpeg_ver.split()[2] if len(ffmpeg_ver.split()) > 2 else ffmpeg_ver
            self.ffmpeg_card.set_up_to_date(short_ver[:15])
        else:
            self.ffmpeg_card.set_update_available("missing", "latest")

    def browse_folder(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Download Folder", self.folder_input.text()
        )
        if dir_path:
            self.folder_input.setText(dir_path)

    def save_settings(self):
        self.config.download_folder = self.folder_input.text()
        self.config.filename_pattern = self.pattern_combo.currentText()
        self.config.audio_quality = "0"
        self.config.embed_thumbnail = self.thumb_check.isChecked()
        self.config.embed_metadata = self.meta_check.isChecked()

        save_config(self.config)
        self.config_changed.emit()
        self.show_toast_requested.emit("Settings saved")

    def reset_defaults(self):
        self.config = Config() # Creates standard defaults, doesn't write automatically
        self.load_settings_into_ui()

    # --- Dependency Update Handling ---
    def check_ytdlp_update(self):
        if self.check_worker and self.check_worker.isRunning():
            return
        self.ytdlp_card.set_checking()
        self.check_worker = YtdlpVersionCheckWorker(self)
        self.check_worker.done.connect(self.on_ytdlp_check_done)
        self.check_worker.failed.connect(self.on_ytdlp_check_failed)
        self.check_worker.start()

    def on_ytdlp_check_done(self, current, latest):
        if current != latest and latest != "unknown":
            self.ytdlp_card.set_update_available(current, latest)
        else:
            self.ytdlp_card.set_up_to_date(current)

    def on_ytdlp_check_failed(self, error_msg):
        logger.error(f"Failed to check yt-dlp update: {error_msg}")
        self.refresh_dep_cards()
        self.show_toast_requested.emit("Update check failed")

    def update_ytdlp(self):
        if self.update_worker and self.update_worker.isRunning():
            return
        self.ytdlp_card.set_updating()
        self.update_worker = YtdlpUpdateWorker(self)
        self.update_worker.progress.connect(self.ytdlp_card.set_update_progress)
        self.update_worker.done.connect(self.on_ytdlp_update_done)
        self.update_worker.failed.connect(self.on_ytdlp_update_failed)
        self.update_worker.start()

    def on_ytdlp_update_done(self, new_ver):
        self.ytdlp_card.set_up_to_date(new_ver)
        self.show_toast_requested.emit("yt-dlp updated successfully")

    def on_ytdlp_update_failed(self, error_msg):
        logger.error(f"Failed to update yt-dlp: {error_msg}")
        self.refresh_dep_cards()
        self.show_toast_requested.emit("yt-dlp update failed")

    def update_ffmpeg(self):
        if self.ffmpeg_fetcher and self.ffmpeg_fetcher.isRunning():
            return
        self.ffmpeg_card.set_updating()
        # Fetch ffmpeg only
        self.ffmpeg_fetcher = FetchWorker(fetch_ytdlp=False, fetch_ffmpeg=True, parent=self)
        self.ffmpeg_fetcher.progress.connect(lambda name, pct: self.ffmpeg_card.set_update_progress(pct))
        self.ffmpeg_fetcher.item_done.connect(self.on_ffmpeg_update_done)
        self.ffmpeg_fetcher.item_failed.connect(self.on_ffmpeg_update_failed)
        self.ffmpeg_fetcher.start()

    def on_ffmpeg_update_done(self, name):
        if name == "ffmpeg.exe":
            ver = checker.get_ffmpeg_version()
            short_ver = ver.split()[2] if ver and len(ver.split()) > 2 else "latest"
            self.ffmpeg_card.set_up_to_date(short_ver[:15])
            self.show_toast_requested.emit("ffmpeg updated successfully")

    def on_ffmpeg_update_failed(self, name, error_msg):
        logger.error(f"Failed to update ffmpeg: {error_msg}")
        self.refresh_dep_cards()
        self.show_toast_requested.emit("ffmpeg update failed")

    def check_ffmpeg_update(self):
        # Using a dedicated attribute to avoid thread collision with ytdlp checks
        if hasattr(self, "ffmpeg_check_worker") and self.ffmpeg_check_worker and self.ffmpeg_check_worker.isRunning():
            return
        self.ffmpeg_card.set_checking()
        self.ffmpeg_check_worker = FfmpegVersionCheckWorker(self)
        self.ffmpeg_check_worker.done.connect(self.on_ffmpeg_check_done)
        self.ffmpeg_check_worker.failed.connect(self.on_ffmpeg_check_failed)
        self.ffmpeg_check_worker.start()

    def on_ffmpeg_check_done(self, current, latest):
        if latest != "unknown" and latest not in current:
            short_cur = current.split()[2] if len(current.split()) > 2 else current
            self.ffmpeg_card.set_update_available(short_cur[:15], latest)
        else:
            short_cur = current.split()[2] if len(current.split()) > 2 else current
            self.ffmpeg_card.set_up_to_date(short_cur[:15])

    def on_ffmpeg_check_failed(self, error_msg):
        logger.error(f"Failed to check ffmpeg update: {error_msg}")
        self.refresh_dep_cards()
        self.show_toast_requested.emit("Update check failed")

    def refresh_config(self):
        self.config = load_config()
        self.load_settings_into_ui()

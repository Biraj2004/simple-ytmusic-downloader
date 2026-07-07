import sys
from pathlib import Path
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QProgressBar, QFrame, QWidget)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QIcon
from gui.icons import get_svg_icon, get_svg_pixmap
from deps.fetcher import FetchWorker
from deps import checker

class SetupWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        self.drag_position = QPoint()
        self.fetch_worker = None
        self.init_ui()
        self.start_dependency_fetch()

    def init_ui(self):
        self.setFixedSize(480, 360)
        self.setStyleSheet("QDialog { background-color: #F0F0F0; border: 1px solid #2D5FA8; }")
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. Custom Title Bar
        self.title_bar = QFrame(self)
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet("background-color: #2D5FA8;")
        self.title_bar_layout = QHBoxLayout(self.title_bar)
        self.title_bar_layout.setContentsMargins(10, 0, 10, 0)
        self.title_bar_layout.setSpacing(6)

        # App Icon
        self.title_icon = QLabel(self.title_bar)
        self.title_icon.setPixmap(get_svg_pixmap("ti-music", color="#FFFFFF", size=14))
        self.title_bar_layout.addWidget(self.title_icon)

        # App Title
        self.title_text = QLabel("YT Music Downloader — Setup", self.title_bar)
        self.title_text.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 500; font-family: 'Segoe UI';")
        self.title_bar_layout.addWidget(self.title_text)
        self.title_bar_layout.addStretch(1)

        # Close Button
        self.close_btn = QPushButton("✕", self.title_bar)
        self.close_btn.setFixedSize(22, 22)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #FFFFFF;
                border: none;
                font-size: 12px;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background-color: #C42B1C;
            }
        """)
        self.close_btn.clicked.connect(self.close_and_exit)
        self.title_bar_layout.addWidget(self.close_btn)

        self.main_layout.addWidget(self.title_bar)

        # 2. Window Body Container
        self.body_widget = QWidget(self)
        self.body_layout = QVBoxLayout(self.body_widget)
        self.body_layout.setContentsMargins(16, 16, 16, 16)
        self.body_layout.setSpacing(12)

        # Intro text
        self.intro_label = QLabel(
            "YT Music Downloader needs two tools to work. Fetching them "
            "from their official sources — this only happens once, or if a "
            "file goes missing on launch.", self.body_widget
        )
        self.intro_label.setWordWrap(True)
        self.intro_label.setStyleSheet("color: #666666; font-size: 12px; font-family: 'Segoe UI'; line-height: 1.7;")
        self.body_layout.addWidget(self.intro_label)

        # 3. Item List (yt-dlp, ffmpeg)
        self.list_frame = QFrame(self.body_widget)
        self.list_frame.setStyleSheet("QFrame { background-color: #FAFAFA; border: 1px solid #CCCCCC; border-radius: 3px; }")
        self.list_layout = QVBoxLayout(self.list_frame)
        self.list_layout.setContentsMargins(10, 8, 10, 8)
        self.list_layout.setSpacing(8)

        # yt-dlp item
        self.ytdlp_layout = QHBoxLayout()
        self.ytdlp_icon = QLabel(self)
        self.ytdlp_icon.setPixmap(get_svg_pixmap("ti-clock", color="#999999", size=18))
        self.ytdlp_layout.addWidget(self.ytdlp_icon)

        self.ytdlp_info = QVBoxLayout()
        self.ytdlp_name_row = QHBoxLayout()
        self.ytdlp_name = QLabel("yt-dlp.exe", self)
        self.ytdlp_name.setStyleSheet("color: #111111; font-size: 12px; font-weight: 500; font-family: 'Segoe UI';")
        self.ytdlp_hint = QLabel("github.com/yt-dlp/yt-dlp", self)
        self.ytdlp_hint.setStyleSheet("color: #888888; font-size: 10px; font-family: 'Segoe UI';")
        self.ytdlp_name_row.addWidget(self.ytdlp_name)
        self.ytdlp_name_row.addWidget(self.ytdlp_hint)
        self.ytdlp_name_row.addStretch(1)
        self.ytdlp_info.addLayout(self.ytdlp_name_row)
        
        self.ytdlp_status = QLabel("Pending...", self)
        self.ytdlp_status.setStyleSheet("color: #666666; font-size: 11px; font-family: 'Segoe UI';")
        self.ytdlp_info.addWidget(self.ytdlp_status)
        self.ytdlp_layout.addLayout(self.ytdlp_info, 1)
        self.list_layout.addLayout(self.ytdlp_layout)

        # Divider
        self.divider = QFrame(self)
        self.divider.setFixedHeight(1)
        self.divider.setStyleSheet("background-color: #DDDDDD;")
        self.list_layout.addWidget(self.divider)

        # ffmpeg item
        self.ffmpeg_layout = QHBoxLayout()
        self.ffmpeg_icon = QLabel(self)
        self.ffmpeg_icon.setPixmap(get_svg_pixmap("ti-clock", color="#999999", size=18))
        self.ffmpeg_layout.addWidget(self.ffmpeg_icon)

        self.ffmpeg_info = QVBoxLayout()
        self.ffmpeg_name_row = QHBoxLayout()
        self.ffmpeg_name = QLabel("ffmpeg.exe", self)
        self.ffmpeg_name.setStyleSheet("color: #111111; font-size: 12px; font-weight: 500; font-family: 'Segoe UI';")
        self.ffmpeg_hint = QLabel("www.gyan.dev", self)
        self.ffmpeg_hint.setStyleSheet("color: #888888; font-size: 10px; font-family: 'Segoe UI';")
        self.ffmpeg_name_row.addWidget(self.ffmpeg_name)
        self.ffmpeg_name_row.addWidget(self.ffmpeg_hint)
        self.ffmpeg_name_row.addStretch(1)
        self.ffmpeg_info.addLayout(self.ffmpeg_name_row)
        
        self.ffmpeg_status = QLabel("Pending...", self)
        self.ffmpeg_status.setStyleSheet("color: #666666; font-size: 11px; font-family: 'Segoe UI';")
        self.ffmpeg_info.addWidget(self.ffmpeg_status)
        self.ffmpeg_layout.addLayout(self.ffmpeg_info, 1)
        self.list_layout.addLayout(self.ffmpeg_layout)

        self.body_layout.addWidget(self.list_frame)

        # 4. Footer Note
        self.footer_note = QLabel(self.body_widget)
        self.footer_note.setTextFormat(Qt.RichText)
        self.footer_note.setText(
            "Files are saved to <span style='background-color:#E0E0E0;'>bin/</span> next to the app. "
            "They are not installed system-wide and do not touch the Windows registry."
        )
        self.footer_note.setWordWrap(True)
        self.footer_note.setStyleSheet("""
            QLabel {
                background-color: #F5F5F5;
                border: 1px solid #DDDDDD;
                border-radius: 2px;
                padding: 7px 10px;
                font-size: 11px;
                color: #666666;
                font-family: 'Segoe UI';
            }
        """)
        self.body_layout.addWidget(self.footer_note)

        # 5. Overall Progress Bar
        self.overall_pbar_layout = QVBoxLayout()
        self.overall_pbar_layout.setSpacing(2)
        
        self.overall_label_row = QHBoxLayout()
        self.overall_title = QLabel("Download progress", self)
        self.overall_title.setStyleSheet("color: #555555; font-size: 11px; font-family: 'Segoe UI';")
        self.overall_val = QLabel("0%", self)
        self.overall_val.setStyleSheet("color: #555555; font-size: 11px; font-family: 'Segoe UI';")
        self.overall_label_row.addWidget(self.overall_title)
        self.overall_label_row.addStretch(1)
        self.overall_label_row.addWidget(self.overall_val)
        self.overall_pbar_layout.addLayout(self.overall_label_row)

        self.overall_pbar = QProgressBar(self)
        self.overall_pbar.setFixedHeight(12)
        self.overall_pbar.setTextVisible(False)
        self.overall_pbar.setRange(0, 100)
        self.overall_pbar.setValue(0)
        self.overall_pbar.setStyleSheet("""
            QProgressBar {
                background-color: #FFFFFF;
                border: 1px solid #BBBBBB;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #2980B9;
                border-radius: 1px;
            }
        """)
        self.overall_pbar_layout.addWidget(self.overall_pbar)
        self.body_layout.addLayout(self.overall_pbar_layout)

        # 6. Failure State Buttons (hidden by default)
        self.fail_btn_bar = QHBoxLayout()
        self.fail_btn_bar.setSpacing(8)

        self.retry_btn = QPushButton("Retry setup", self)
        self.retry_btn.setFixedHeight(30)
        self.retry_btn.setCursor(Qt.PointingHandCursor)
        self.retry_btn.setStyleSheet("""
            QPushButton {
                background-color: #DAE8F8;
                border: 1px solid #4A90D9;
                color: #1A5A9C;
                font-size: 12px;
                font-family: 'Segoe UI';
                font-weight: 500;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #C0DBF5;
            }
        """)
        self.retry_btn.clicked.connect(self.start_dependency_fetch)
        self.fail_btn_bar.addWidget(self.retry_btn, 1)

        self.exit_btn = QPushButton("Close app", self)
        self.exit_btn.setFixedHeight(30)
        self.exit_btn.setCursor(Qt.PointingHandCursor)
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFF8F8;
                border: 1px solid #C0392B;
                color: #C0392B;
                font-size: 12px;
                font-family: 'Segoe UI';
                font-weight: 500;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #FDE8E8;
            }
        """)
        self.exit_btn.clicked.connect(self.close_and_exit)
        self.fail_btn_bar.addWidget(self.exit_btn, 1)

        self.body_layout.addLayout(self.fail_btn_bar)
        self.fail_btn_bar_widget = QWidget(self)
        # We will toggle visibility by storing references or making the buttons layout hidden
        self.retry_btn.setVisible(False)
        self.exit_btn.setVisible(False)

        self.main_layout.addWidget(self.body_widget)

    # --- Mouse Dragging Support ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def close_and_exit(self):
        if self.fetch_worker:
            self.fetch_worker.cancel()
            self.fetch_worker.wait()
        sys.exit(1)

    def start_dependency_fetch(self):
        # Hide retry buttons if visible
        self.retry_btn.setVisible(False)
        self.exit_btn.setVisible(False)
        
        # Reset labels
        self.ytdlp_icon.setPixmap(get_svg_pixmap("ti-clock", color="#999999", size=18))
        self.ytdlp_status.setText("Pending...")
        self.ytdlp_status.setStyleSheet("color: #666666; font-size: 11px; font-family: 'Segoe UI';")
        
        self.ffmpeg_icon.setPixmap(get_svg_pixmap("ti-clock", color="#999999", size=18))
        self.ffmpeg_status.setText("Pending...")
        self.ffmpeg_status.setStyleSheet("color: #666666; font-size: 11px; font-family: 'Segoe UI';")
        
        self.overall_pbar.setValue(0)
        self.overall_val.setText("0%")

        # Check which dependencies are missing
        ytdlp_ok, ffmpeg_ok = checker.deps_functional()
        fetch_ytdlp = not ytdlp_ok
        fetch_ffmpeg = not ffmpeg_ok

        if not fetch_ytdlp and not fetch_ffmpeg:
            # Both OK! Close dialog.
            self.accept()
            return

        self.fetch_worker = FetchWorker(fetch_ytdlp=fetch_ytdlp, fetch_ffmpeg=fetch_ffmpeg, parent=self)
        self.fetch_worker.progress.connect(self.on_fetch_progress)
        self.fetch_worker.item_done.connect(self.on_fetch_done)
        self.fetch_worker.item_failed.connect(self.on_fetch_failed)
        self.fetch_worker.all_done.connect(self.on_fetch_all_done)
        self.fetch_worker.start()

    def on_fetch_progress(self, item_name, percent):
        self.overall_val.setText(f"{percent}%")
        self.overall_pbar.setValue(percent)
        
        if item_name == "yt-dlp.exe":
            self.ytdlp_icon.setPixmap(get_svg_pixmap("ti-loader-2", color="#2980B9", size=18))
            self.ytdlp_status.setText(f"Downloading — {percent}%")
            self.ytdlp_status.setStyleSheet("color: #2980B9; font-size: 11px; font-family: 'Segoe UI';")
        else:
            self.ffmpeg_icon.setPixmap(get_svg_pixmap("ti-loader-2", color="#2980B9", size=18))
            self.ffmpeg_status.setText(f"Downloading — {percent}%")
            self.ffmpeg_status.setStyleSheet("color: #2980B9; font-size: 11px; font-family: 'Segoe UI';")

    def on_fetch_done(self, item_name):
        if item_name == "yt-dlp.exe":
            self.ytdlp_icon.setPixmap(get_svg_pixmap("ti-circle-check", color="#27AE60", size=18))
            self.ytdlp_status.setText("Installed and verified")
            self.ytdlp_status.setStyleSheet("color: #27AE60; font-size: 11px; font-family: 'Segoe UI';")
        else:
            self.ffmpeg_icon.setPixmap(get_svg_pixmap("ti-circle-check", color="#27AE60", size=18))
            self.ffmpeg_status.setText("Installed and verified")
            self.ffmpeg_status.setStyleSheet("color: #27AE60; font-size: 11px; font-family: 'Segoe UI';")

    def on_fetch_failed(self, item_name, error_msg):
        if item_name == "yt-dlp.exe":
            self.ytdlp_icon.setPixmap(get_svg_pixmap("ti-alert-circle", color="#C0392B", size=18))
            self.ytdlp_status.setText(f"Download failed: {error_msg}")
            self.ytdlp_status.setStyleSheet("color: #C0392B; font-size: 11px; font-family: 'Segoe UI';")
        else:
            self.ffmpeg_icon.setPixmap(get_svg_pixmap("ti-alert-circle", color="#C0392B", size=18))
            self.ffmpeg_status.setText(f"Download failed: {error_msg}")
            self.ffmpeg_status.setStyleSheet("color: #C0392B; font-size: 11px; font-family: 'Segoe UI';")

    def on_fetch_all_done(self):
        # Re-check functionality
        ytdlp_ok, ffmpeg_ok = checker.deps_functional()
        if ytdlp_ok and ffmpeg_ok:
            self.accept()
        else:
            # Failure state: show buttons
            self.retry_btn.setVisible(True)
            self.exit_btn.setVisible(True)

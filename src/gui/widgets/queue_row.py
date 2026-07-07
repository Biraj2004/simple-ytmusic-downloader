from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QProgressBar
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QFontMetrics
from engine.queue_item import QueueItem, Status, Mode
from gui.icons import get_svg_icon, get_svg_pixmap

class ElidedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.full_text = text

    def setText(self, text):
        self.full_text = text
        self.update_elision()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_elision()

    def update_elision(self):
        fm = self.fontMetrics()
        elided = fm.elidedText(self.full_text, Qt.ElideRight, max(self.width(), 20))
        super().setText(elided)

class QueueRow(QFrame):
    remove_clicked = Signal(str)  # item_id
    retry_clicked = Signal(str)   # item_id

    def __init__(self, item: QueueItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.init_ui()
        self.update_state()

    def init_ui(self):
        self.setFixedHeight(54)
        self.setObjectName("QueueRow")
        
        # Main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(8, 6, 8, 6)
        self.main_layout.setSpacing(8)

        # 1. Status Icon
        self.status_icon_label = QLabel(self)
        self.status_icon_label.setFixedSize(16, 16)
        self.status_icon_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.status_icon_label)

        # 2. Text Stack (Title, Subtitle, Progress Bar / Retry Button)
        self.text_layout = QVBoxLayout()
        self.text_layout.setSpacing(2)
        self.text_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = ElidedLabel(self.item.title, self)
        self.title_label.setStyleSheet("color: #111111; font-size: 12px; font-weight: 500; font-family: 'Segoe UI';")
        self.text_layout.addWidget(self.title_label)

        # Subtitle layout (combines status details and type)
        self.subtitle_layout = QHBoxLayout()
        self.subtitle_layout.setContentsMargins(0, 0, 0, 0)
        self.subtitle_layout.setSpacing(6)
        
        self.subtitle_label = QLabel(self)
        self.subtitle_label.setStyleSheet("color: #666666; font-size: 11px; font-family: 'Segoe UI';")
        self.subtitle_layout.addWidget(self.subtitle_label)

        self.retry_btn = QPushButton("Retry", self)
        self.retry_btn.setFixedSize(40, 16)
        self.retry_btn.setCursor(Qt.PointingHandCursor)
        self.retry_btn.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
                color: #2980B9;
                font-size: 11px;
                font-weight: bold;
                font-family: 'Segoe UI';
                text-align: left;
                padding: 0px;
            }
            QPushButton:hover {
                text-decoration: underline;
                color: #1B5A8F;
            }
        """)
        self.retry_btn.clicked.connect(lambda: self.retry_clicked.emit(self.item.id))
        self.retry_btn.setVisible(False)
        self.subtitle_layout.addWidget(self.retry_btn)
        self.subtitle_layout.addStretch()

        self.text_layout.addLayout(self.subtitle_layout)

        # Inline progress bar (hidden by default)
        self.row_progress = QProgressBar(self)
        self.row_progress.setFixedHeight(4)
        self.row_progress.setTextVisible(False)
        self.row_progress.setRange(0, 100)
        self.row_progress.setValue(0)
        self.row_progress.setStyleSheet("""
            QProgressBar {
                background-color: #E0E0E0;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #2980B9;
                border-radius: 2px;
            }
        """)
        self.row_progress.setVisible(False)
        self.text_layout.addWidget(self.row_progress)

        self.main_layout.addLayout(self.text_layout, stretch=1)

        # 3. Mode Tag
        self.mode_tag = QLabel(self)
        self.mode_tag.setStyleSheet("color: #777777; font-size: 10px; font-family: 'Segoe UI'; font-weight: 500;")
        self.mode_tag.setText("New" if self.item.mode == Mode.NEW_DOWNLOAD else "Update")
        self.main_layout.addWidget(self.mode_tag)

        # 4. Action Button (Remove / Cancel)
        self.action_btn = QPushButton(self)
        self.action_btn.setFixedSize(20, 20)
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.setIcon(get_svg_icon("ti-x", color="#BBBBBB", size=13))
        self.action_btn.setToolTip("Remove from queue")
        self.action_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #FDE8E8;
            }
        """)
        self.action_btn.clicked.connect(lambda: self.remove_clicked.emit(self.item.id))
        self.main_layout.addWidget(self.action_btn)

    def update_state(self):
        # Update title if it changed
        self.title_label.setText(self.item.title)
        
        # Build subtitle
        type_str = "Playlist" if self.item.is_playlist else "Song"
        track_part = f" · {self.item.track_count} tracks" if self.item.is_playlist else ""
        
        # Handle skipped details
        skip_part = ""
        if self.item.is_playlist and self.item.skipped_count > 0:
            skip_part = f" · {self.item.skipped_count} skipped"
            
        status_detail = ""
        if self.item.status == Status.QUEUED:
            status_detail = "queued"
        elif self.item.status == Status.DOWNLOADING:
            if self.item.speed_str:
                status_detail = f"downloading ({self.item.speed_str})"
            else:
                status_detail = "downloading"
        elif self.item.status == Status.DONE:
            status_detail = "done"
        elif self.item.status == Status.SKIPPED_DUPLICATE:
            status_detail = "already downloaded"
        elif self.item.status == Status.SKIPPED:
            status_detail = "skipped"
        elif self.item.status == Status.PAUSED_NETWORK:
            status_detail = "paused — network issue"
        elif self.item.status == Status.ERROR:
            status_detail = "failed"
        elif self.item.status == Status.CANCELLED:
            status_detail = "cancelled"
            
        self.subtitle_label.setText(f"{type_str}{track_part}{skip_part} · {status_detail}")

        # Update Progress Bar
        if self.item.status == Status.DOWNLOADING:
            self.row_progress.setVisible(True)
            self.row_progress.setValue(int(self.item.progress_pct))
            self.setFixedHeight(62) # Expand for progress bar
        else:
            self.row_progress.setVisible(False)
            self.setFixedHeight(54)

        # Update Retry Button
        self.retry_btn.setVisible(self.item.status == Status.PAUSED_NETWORK)

        # Style frame border and background depending on status
        border_css = "border: 1px solid #D0D0D0;"
        bg_css = "background-color: #FFFFFF;"
        opacity = "1.0"

        if self.item.status == Status.DOWNLOADING:
            border_css = "border: 1px solid #D0D0D0; border-left: 3px solid #4A90D9;"
            bg_css = "background-color: #F4F9FF;"
            self.status_icon_label.setPixmap(get_svg_pixmap("ti-loader-2", color="#2980B9", size=14))
            self.action_btn.setToolTip("Cancel download")
            self.action_btn.setIcon(get_svg_icon("ti-x", color="#C0392B", size=13))
        elif self.item.status == Status.DONE or self.item.status == Status.SKIPPED_DUPLICATE:
            bg_css = "background-color: rgba(255, 255, 255, 165);" # 65% opacity
            self.status_icon_label.setPixmap(get_svg_pixmap("ti-circle-check", color="#27AE60", size=14))
            self.action_btn.setToolTip("Remove from list")
            self.action_btn.setIcon(get_svg_icon("ti-x", color="#BBBBBB", size=13))
        elif self.item.status == Status.QUEUED:
            self.status_icon_label.setPixmap(get_svg_pixmap("ti-clock", color="#999999", size=14))
            self.action_btn.setToolTip("Remove from queue")
            self.action_btn.setIcon(get_svg_icon("ti-x", color="#BBBBBB", size=13))
        elif self.item.status == Status.PAUSED_NETWORK:
            border_css = "border: 1px solid #D0D0D0; border-left: 3px solid #E67E22;"
            bg_css = "background-color: #FFFBF5;"
            self.status_icon_label.setPixmap(get_svg_pixmap("ti-wifi-off", color="#E67E22", size=14))
            self.action_btn.setToolTip("Remove from queue")
            self.action_btn.setIcon(get_svg_icon("ti-x", color="#BBBBBB", size=13))
        elif self.item.status in (Status.ERROR, Status.SKIPPED):
            border_css = "border: 1px solid #D0D0D0; border-left: 3px solid #C0392B;"
            bg_css = "background-color: #FFF8F8;"
            self.status_icon_label.setPixmap(get_svg_pixmap("ti-alert-circle", color="#C0392B", size=14))
            self.action_btn.setToolTip("Remove from list")
            self.action_btn.setIcon(get_svg_icon("ti-x", color="#BBBBBB", size=13))
        elif self.item.status == Status.CANCELLED:
            bg_css = "background-color: rgba(255, 255, 255, 165);"
            self.status_icon_label.setPixmap(get_svg_pixmap("ti-x", color="#AAAAAA", size=14))
            self.action_btn.setToolTip("Remove from list")
            self.action_btn.setIcon(get_svg_icon("ti-x", color="#BBBBBB", size=13))

        self.setStyleSheet(f"""
            QFrame#QueueRow {{
                {bg_css}
                {border_css}
                border-radius: 2px;
            }}
        """)

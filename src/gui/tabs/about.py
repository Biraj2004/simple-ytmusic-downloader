from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from gui.icons import get_svg_icon, get_svg_pixmap
from constants import TODO_GITHUB_URL, TODO_REPO_URL, APP_NAME, APP_VERSION

class AboutTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # Center-aligned vertical layout
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.setContentsMargins(40, 20, 40, 20)
        self.layout.setSpacing(0)

        # 1. App Icon Container
        self.icon_container = QLabel(self)
        self.icon_container.setFixedSize(52, 52)
        self.icon_container.setPixmap(get_svg_pixmap("ti-music", color="#555555", size=26))
        self.icon_container.setAlignment(Qt.AlignCenter)
        self.icon_container.setStyleSheet("""
            QLabel {
                background-color: #E8E8E8;
                border: 1px solid #CCCCCC;
                border-radius: 6px;
            }
        """)
        self.layout.addWidget(self.icon_container, 0, Qt.AlignCenter)
        self.layout.addSpacing(10)

        # 2. App Name
        self.name_label = QLabel(APP_NAME, self)
        self.name_label.setStyleSheet("color: #111111; font-size: 15px; font-weight: 500; font-family: 'Segoe UI';")
        self.layout.addWidget(self.name_label, 0, Qt.AlignCenter)
        self.layout.addSpacing(2)

        # 3. Version Info
        self.version_label = QLabel(f"v{APP_VERSION} · Windows x64", self)
        self.version_label.setStyleSheet("color: #888888; font-size: 11px; font-family: 'Segoe UI';")
        self.layout.addWidget(self.version_label, 0, Qt.AlignCenter)
        self.layout.addSpacing(12)

        # 4. Author
        self.author_label = QLabel(self)
        self.author_label.setTextFormat(Qt.RichText)
        self.author_label.setText('Built by <span style="font-weight: 500; color: #222222;">Biraj Sarkar</span>')
        self.author_label.setStyleSheet("color: #555555; font-size: 12px; font-family: 'Segoe UI';")
        self.layout.addWidget(self.author_label, 0, Qt.AlignCenter)
        self.layout.addSpacing(14)

        # 5. Link Buttons Row
        self.btn_layout = QHBoxLayout()
        self.btn_layout.setSpacing(8)
        self.btn_layout.setAlignment(Qt.AlignCenter)

        self.github_btn = QPushButton("GitHub — Biraj2004", self)
        self.github_btn.setIcon(get_svg_icon("ti-brand-github", color="#333333", size=14))
        self.github_btn.setFixedHeight(26)
        self.github_btn.setCursor(Qt.PointingHandCursor)
        self.github_btn.setStyleSheet("""
            QPushButton {
                background-color: #E8E8E8;
                border: 1px solid #888888;
                color: #333333;
                font-size: 11px;
                font-family: 'Segoe UI';
                padding: 0px 12px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #D8D8D8;
            }
        """)
        self.github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(TODO_GITHUB_URL)))
        self.btn_layout.addWidget(self.github_btn)

        self.repo_btn = QPushButton("Repository", self)
        self.repo_btn.setIcon(get_svg_icon("ti-external-link", color="#333333", size=14))
        self.repo_btn.setFixedHeight(26)
        self.repo_btn.setCursor(Qt.PointingHandCursor)
        self.repo_btn.setStyleSheet("""
            QPushButton {
                background-color: #E8E8E8;
                border: 1px solid #888888;
                color: #333333;
                font-size: 11px;
                font-family: 'Segoe UI';
                padding: 0px 12px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #D8D8D8;
            }
        """)
        self.repo_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(TODO_REPO_URL)))
        self.btn_layout.addWidget(self.repo_btn)

        self.layout.addLayout(self.btn_layout)
        self.layout.addSpacing(14)

        # 6. Full width divider
        self.divider = QWidget(self)
        self.divider.setFixedHeight(1)
        self.divider.setStyleSheet("background-color: #DDDDDD;")
        self.layout.addWidget(self.divider)
        self.layout.addSpacing(10)

        # 7. Note text
        self.note_label = QLabel(self)
        self.note_label.setTextFormat(Qt.RichText)
        self.note_label.setText(
            "Built on <b>yt-dlp</b> (github.com/yt-dlp/yt-dlp) and <b>ffmpeg</b> (gyan.dev).<br>"
            "For personal use only. Not affiliated with YouTube or Google."
        )
        self.note_label.setAlignment(Qt.AlignCenter)
        self.note_label.setStyleSheet("color: #888888; font-size: 11px; font-family: 'Segoe UI'; line-height: 1.7;")
        self.layout.addWidget(self.note_label, 0, Qt.AlignCenter)

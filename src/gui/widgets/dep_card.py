from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar
from PySide6.QtCore import Qt, Signal
from gui.icons import get_svg_icon

class DepCard(QFrame):
    check_update_clicked = Signal()
    update_now_clicked = Signal()

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.name = name
        self.init_ui()
        self.set_up_to_date("v1.0.0") # default state

    def init_ui(self):
        self.setObjectName("DepCard")
        self.setStyleSheet("""
            QFrame#DepCard {
                background-color: #FAFAFA;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
            }
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 10, 12, 10)
        self.main_layout.setSpacing(6)

        # Header: Name + Status Pill
        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(0, 0, 0, 0)

        self.name_label = QLabel(self.name, self)
        self.name_label.setStyleSheet("color: #111111; font-size: 12px; font-weight: 500; font-family: 'Segoe UI';")
        self.header_layout.addWidget(self.name_label)

        self.pill_label = QLabel(self)
        self.pill_label.setStyleSheet("""
            font-size: 10px;
            font-weight: 500;
            padding: 2px 8px;
            border-radius: 9px;
            font-family: 'Segoe UI';
        """)
        self.pill_label.setAlignment(Qt.AlignCenter)
        self.header_layout.addWidget(self.pill_label, 0, Qt.AlignRight)
        
        self.main_layout.addLayout(self.header_layout)

        # Version text
        self.version_label = QLabel(self)
        self.version_label.setStyleSheet("color: #666666; font-size: 11px; font-family: 'Segoe UI';")
        self.main_layout.addWidget(self.version_label)

        # Container for action button / progress bar
        self.action_layout = QVBoxLayout()
        self.action_layout.setContentsMargins(0, 0, 0, 0)
        self.action_layout.setSpacing(4)
        
        self.action_btn = QPushButton(self)
        self.action_btn.setFixedHeight(24)
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #F0F0F0;
                color: #AAAAAA;
                border-color: #CCCCCC;
            }
        """)
        self.action_layout.addWidget(self.action_btn)

        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setStyleSheet("""
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
        self.progress_bar.setVisible(False)
        self.action_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel(self)
        self.progress_label.setStyleSheet("color: #2980B9; font-size: 10px; font-family: 'Segoe UI';")
        self.progress_label.setVisible(False)
        self.action_layout.addWidget(self.progress_label)

        self.main_layout.addLayout(self.action_layout)

    def set_up_to_date(self, version: str):
        self.pill_label.setText("up to date")
        self.pill_label.setStyleSheet("""
            background-color: #D4EDDA;
            color: #155724;
            border: 1px solid #C3E6CB;
            font-size: 10px;
            font-weight: 500;
            padding: 2px 8px;
            border-radius: 9px;
            font-family: 'Segoe UI';
        """)
        self.version_label.setText(version)
        self.action_btn.setText("Check for update")
        self.action_btn.setIcon(get_svg_icon("ti-refresh", color="#333333", size=12))
        self.action_btn.setEnabled(True)
        self.action_btn.setVisible(True)
        self.action_btn.setStyleSheet("""
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
        # Disconnect and reconnect clicked signal
        try:
            self.action_btn.clicked.disconnect()
        except Exception:
            pass
        self.action_btn.clicked.connect(self.check_update_clicked.emit)

        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)

    def set_update_available(self, current_version: str, new_version: str):
        self.pill_label.setText("update available")
        self.pill_label.setStyleSheet("""
            background-color: #FFF3CD;
            color: #856404;
            border: 1px solid #FFEAA7;
            font-size: 10px;
            font-weight: 500;
            padding: 2px 8px;
            border-radius: 9px;
            font-family: 'Segoe UI';
        """)
        self.version_label.setText(f"{current_version} → {new_version}")
        self.action_btn.setText("Update now")
        self.action_btn.setIcon(get_svg_icon("ti-download", color="#1A5A9C", size=12))
        self.action_btn.setEnabled(True)
        self.action_btn.setVisible(True)
        # Apply primary style to Update now button
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #DAE8F8;
                border: 1px solid #4A90D9;
                color: #1A5A9C;
                font-size: 11px;
                border-radius: 2px;
                font-family: 'Segoe UI';
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #C0DBF5;
            }
        """)
        try:
            self.action_btn.clicked.disconnect()
        except Exception:
            pass
        self.action_btn.clicked.connect(self.update_now_clicked.emit)

        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)

    def set_checking(self):
        self.pill_label.setText("checking...")
        self.pill_label.setStyleSheet("""
            background-color: #E8E8E8;
            color: #666666;
            border: 1px solid #CCCCCC;
            font-size: 10px;
            font-weight: 500;
            padding: 2px 8px;
            border-radius: 9px;
            font-family: 'Segoe UI';
        """)
        self.action_btn.setText("Checking...")
        self.action_btn.setEnabled(False)
        
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)

    def set_updating(self):
        self.pill_label.setText("updating")
        self.pill_label.setStyleSheet("""
            background-color: #CCE5FF;
            color: #004085;
            border: 1px solid #B8DAFF;
            font-size: 10px;
            font-weight: 500;
            padding: 2px 8px;
            border-radius: 9px;
            font-family: 'Segoe UI';
        """)
        self.action_btn.setVisible(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Downloading — 0%")
        self.progress_label.setVisible(True)

    def set_update_progress(self, percent: int):
        self.progress_bar.setValue(percent)
        self.progress_label.setText(f"Downloading — {percent}%")

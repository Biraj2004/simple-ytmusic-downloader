from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt

class LabelledProgressBar(QWidget):
    def __init__(self, label_text: str, fill_color: str = "#4A90D9", parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)

        # Labels row
        self.labels_layout = QHBoxLayout()
        self.labels_layout.setContentsMargins(0, 0, 0, 0)
        
        self.left_label = QLabel(label_text, self)
        self.left_label.setStyleSheet("color: #555555; font-size: 11px; font-family: 'Segoe UI';")
        
        self.right_label = QLabel("", self)
        self.right_label.setStyleSheet("color: #555555; font-size: 11px; font-family: 'Segoe UI';")
        self.right_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.labels_layout.addWidget(self.left_label)
        self.labels_layout.addWidget(self.right_label)
        self.layout.addLayout(self.labels_layout)

        # Progress bar
        self.pbar = QProgressBar(self)
        self.pbar.setFixedHeight(18)
        self.pbar.setTextVisible(False)
        self.pbar.setRange(0, 100)
        self.pbar.setValue(0)
        
        # Stylesheet for custom Windows styling
        self.pbar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #FFFFFF;
                border: 1px solid #BBBBBB;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {fill_color};
                border-radius: 1px;
            }}
        """)
        self.layout.addWidget(self.pbar)

    def setValue(self, val: int):
        # Bound it between 0 and range max
        max_val = self.pbar.maximum()
        min_val = self.pbar.minimum()
        bounded_val = max(min_val, min(int(val), max_val))
        self.pbar.setValue(bounded_val)

    def setRange(self, min_val: int, max_val: int):
        self.pbar.setRange(min_val, max_val)

    def setLeftText(self, text: str):
        self.left_label.setText(text)

    def setRightText(self, text: str):
        self.right_label.setText(text)
        
    def value(self) -> int:
        return self.pbar.value()

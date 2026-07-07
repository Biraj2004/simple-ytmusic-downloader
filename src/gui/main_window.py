import sys
from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QTabWidget, QFrame, 
                             QGraphicsOpacityEffect, QStyleFactory, QApplication)
from PySide6.QtCore import Qt, QPoint, QPropertyAnimation, QTimer, Slot, QSize
from PySide6.QtGui import QIcon, QGuiApplication

from gui.tabs.downloader import DownloaderTab
from gui.tabs.settings import SettingsTab
from gui.tabs.about import AboutTab
from gui.icons import get_svg_icon, get_svg_pixmap
from config import Config, load_config, save_config
from engine.queue_item import QueueItem, Status, Mode
from engine.worker import DownloadWorker
import logging

logger = logging.getLogger("YTMusicDownloader")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.is_maximized = False
        self.drag_position = QPoint()
        
        # Download Queue states
        self.current_worker = None
        self.active_item = None
        self.queue_paused = False
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint)
        self.init_ui()
        self.restore_window_state()

    def init_ui(self):
        # Central widget and layout
        self.central_widget = QWidget(self)
        self.central_widget.setStyleSheet("background-color: #F0F0F0;")
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. Custom Title Bar
        self.title_bar = QFrame(self.central_widget)
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet("background-color: #2D5FA8;")
        self.title_bar_layout = QHBoxLayout(self.title_bar)
        self.title_bar_layout.setContentsMargins(10, 0, 0, 0)
        self.title_bar_layout.setSpacing(4)

        # App Icon
        self.title_icon = QLabel(self.title_bar)
        self.title_icon.setPixmap(get_svg_pixmap("ti-music", color="#FFFFFF", size=14))
        self.title_bar_layout.addWidget(self.title_icon)

        # App Title
        self.title_text = QLabel("YT Music Downloader", self.title_bar)
        self.title_text.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 500; font-family: 'Segoe UI';")
        self.title_bar_layout.addWidget(self.title_text)
        self.title_bar_layout.addStretch(1)

        # Title Bar Buttons Container
        self.btn_container = QWidget(self.title_bar)
        self.btn_layout = QHBoxLayout(self.btn_container)
        self.btn_layout.setContentsMargins(0, 0, 0, 0)
        self.btn_layout.setSpacing(0)

        # Minimise Button
        self.min_btn = QPushButton(self.btn_container)
        self.min_btn.setIcon(get_svg_icon("win-min", color="#FFFFFF", size=10))
        self.min_btn.setFixedSize(36, 30)
        self.min_btn.setCursor(Qt.PointingHandCursor)
        self.min_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        self.min_btn.clicked.connect(self.showMinimized)
        self.btn_layout.addWidget(self.min_btn)

        # Maximise/Restore Button
        self.max_btn = QPushButton(self.btn_container)
        self.max_btn.setIcon(get_svg_icon("win-max", color="#FFFFFF", size=10))
        self.max_btn.setFixedSize(36, 30)
        self.max_btn.setCursor(Qt.PointingHandCursor)
        self.max_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        self.max_btn.clicked.connect(self.toggle_maximize)
        self.btn_layout.addWidget(self.max_btn)

        # Close Button
        self.close_btn = QPushButton(self.btn_container)
        self.close_btn.setIcon(get_svg_icon("win-close", color="#FFFFFF", size=10))
        self.close_btn.setFixedSize(36, 30)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: #C42B1C;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        self.btn_layout.addWidget(self.close_btn)

        self.title_bar_layout.addWidget(self.btn_container)
        self.main_layout.addWidget(self.title_bar)

        # 2. Tabs Container
        self.tab_widget = QTabWidget(self.central_widget)
        self.tab_widget.setStyleSheet("""
            QTabWidget::panel {
                border-top: 1px solid #AAAAAA;
                background-color: #F0F0F0;
            }
            QTabBar::tab {
                background-color: #C8C8C8;
                color: #444444;
                border: 1px solid #AAAAAA;
                border-bottom: none;
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
                padding: 5px 16px;
                font-family: 'Segoe UI';
                font-size: 12px;
            }
            QTabBar::tab:hover {
                background-color: #D8D8D8;
            }
            QTabBar::tab:selected {
                background-color: #F0F0F0;
                color: #000000;
                font-weight: 500;
                border-bottom-color: #F0F0F0;
            }
        """)

        # Add Tab views
        self.downloader_tab = DownloaderTab(self)
        self.downloader_tab.start_queue_requested.connect(self.start_queue)
        self.downloader_tab.pause_queue_requested.connect(self.pause_queue)
        self.downloader_tab.cancel_queue_requested.connect(self.cancel_queue)
        self.downloader_tab.clear_queue_requested.connect(self.clear_queue)
        self.downloader_tab.item_removed.connect(self.on_item_removed)
        self.downloader_tab.item_retry_requested.connect(self.on_item_retry_requested)
        self.downloader_tab.show_toast_requested.connect(self.show_toast)
        self.tab_widget.addTab(self.downloader_tab, "Downloader")

        self.settings_tab = SettingsTab(self)
        self.settings_tab.show_toast_requested.connect(self.show_toast)
        self.settings_tab.config_changed.connect(self.downloader_tab.refresh_config)
        self.downloader_tab.config_changed.connect(self.settings_tab.refresh_config)
        self.settings_tab.config_changed.connect(self.reload_config)
        self.downloader_tab.config_changed.connect(self.reload_config)
        self.tab_widget.addTab(self.settings_tab, "Settings")

        self.about_tab = AboutTab(self)
        self.tab_widget.addTab(self.about_tab, "About")

        self.main_layout.addWidget(self.tab_widget)

        # 3. Floating Toast Overlay (hidden by default)
        self.toast_label = QLabel(self.central_widget)
        self.toast_label.setAlignment(Qt.AlignCenter)
        self.toast_label.setStyleSheet("""
            QLabel {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                padding: 6px 12px;
                font-size: 12px;
                color: #222222;
                font-family: 'Segoe UI';
            }
        """)
        self.toast_label.setVisible(False)
        self.toast_opacity = QGraphicsOpacityEffect(self.toast_label)
        self.toast_label.setGraphicsEffect(self.toast_opacity)

        self.toast_timer = QTimer(self)
        self.toast_timer.setSingleShot(True)
        self.toast_timer.timeout.connect(self.hide_toast)

    # --- Mouse Dragging and Maximize Support ---
    def mousePressEvent(self, event):
        # Click on custom title bar to drag window
        if event.button() == Qt.LeftButton and event.position().y() < 30:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and event.position().y() < 30 and not self.is_maximized:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def toggle_maximize(self):
        if self.is_maximized:
            self.showNormal()
            self.max_btn.setIcon(get_svg_icon("win-max", color="#FFFFFF", size=10))
            self.is_maximized = False
        else:
            self.showMaximized()
            self.max_btn.setIcon(get_svg_icon("win-restore", color="#FFFFFF", size=10))
            self.is_maximized = True

    # --- Sizing and Position Persistence ---
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Position toast overlay in bottom-center
        self.position_toast()

    def position_toast(self):
        if self.toast_label.isVisible():
            toast_w = self.toast_label.sizeHint().width()
            toast_h = self.toast_label.sizeHint().height()
            win_w = self.width()
            win_h = self.height()
            self.toast_label.setGeometry((win_w - toast_w) // 2, win_h - toast_h - 45, toast_w, toast_h)

    def restore_window_state(self):
        # Set default minimum size
        self.setMinimumSize(600, 460)
        
        cfg = self.config
        primary_screen = QGuiApplication.primaryScreen()
        if not primary_screen:
            # Fallback if no screen detected
            self.setGeometry(100, 100, 800, 600)
            return

        screen_rect = primary_screen.geometry()
        
        # Check if saved geometry exists and is valid (not -1 default)
        has_saved_pos = (cfg.window_x != -1 and cfg.window_y != -1 and cfg.window_w != -1 and cfg.window_h != -1)
        
        if has_saved_pos:
            # Check if offscreen
            offscreen = True
            for screen in QGuiApplication.screens():
                if screen.geometry().contains(cfg.window_x, cfg.window_y):
                    offscreen = False
                    break
            
            if not offscreen:
                self.setGeometry(cfg.window_x, cfg.window_y, cfg.window_w, cfg.window_h)
                return
                
        # If no saved position, calculate 60% of screen width and height dynamically
        w = int(screen_rect.width() * 0.6)
        h = int(screen_rect.height() * 0.6)
        
        # Respect minimum constraints
        w = max(w, 600)
        h = max(h, 460)
        
        # Center on monitor
        x = screen_rect.x() + (screen_rect.width() - w) // 2
        y = screen_rect.y() + (screen_rect.height() - h) // 2
        self.setGeometry(x, y, w, h)

    def closeEvent(self, event):
        # Stop download worker if active
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.request_cancel()
            self.current_worker.wait()

        # Save window size and position
        if not self.isMaximized():
            self.config.window_x = self.x()
            self.config.window_y = self.y()
            self.config.window_w = self.width()
            self.config.window_h = self.height()
            save_config(self.config)
        event.accept()

    @Slot()
    def reload_config(self):
        self.config = load_config()

    # --- Floating Toast System ---
    @Slot(str)
    def show_toast(self, text: str):
        self.toast_label.setText(text)
        self.toast_label.adjustSize()
        self.toast_label.setVisible(True)
        self.position_toast()
        
        # Animate Fade In
        self.toast_opacity.setOpacity(0.0)
        self.anim = QPropertyAnimation(self.toast_opacity, b"opacity")
        self.anim.setDuration(150)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()

        self.toast_timer.start(2000) # hold 2 seconds

    def hide_toast(self):
        self.anim = QPropertyAnimation(self.toast_opacity, b"opacity")
        self.anim.setDuration(250)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(lambda: self.toast_label.setVisible(False))
        self.anim.start()

    # --- Download Queue Engine Integration ---
    @Slot()
    def start_queue(self):
        self.queue_paused = False
        self.downloader_tab.set_downloading(True)
        self.process_next_queue_item()

    @Slot()
    def pause_queue(self):
        self.queue_paused = True
        self.downloader_tab.set_paused(True)  # Keep progress panel visible
        self.downloader_tab.set_downloading(False)
        self.show_toast("Queue paused")
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.request_cancel()

    @Slot()
    def cancel_queue(self):
        self.queue_paused = True
        self.downloader_tab.set_paused(False)  # Hide progress panel
        self.downloader_tab.set_downloading(False)
        
        # Cancel current active worker
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.request_cancel()
        
        self._clear_queue_force()
        self.show_toast("Queue cancelled")

    def _clear_queue_force(self):
        # Clear downloader list
        self.downloader_tab.queue_items.clear()
        
        # Clear UI row widgets
        for wid in list(self.downloader_tab.row_widgets.values()):
            self.downloader_tab.scroll_list_layout.removeWidget(wid)
            wid.deleteLater()
        self.downloader_tab.row_widgets.clear()
        
        self.downloader_tab.clear_all_error_records()
        self.downloader_tab.update_ui_state()
        self.setWindowTitle("YT Music Downloader")

    @Slot()
    def clear_queue(self):
        if self.current_worker and self.current_worker.isRunning():
            return
        self._clear_queue_force()

    @Slot(str)
    def on_item_removed(self, item_id: str):
        # If the item being removed is currently downloading, cancel it
        if self.active_item and self.active_item.id == item_id:
            if self.current_worker and self.current_worker.isRunning():
                self.current_worker.request_cancel()

    @Slot(str)
    def on_item_retry_requested(self, item_id: str):
        # Reset specific item status to QUEUED and start queue if idle
        for item in self.downloader_tab.queue_items:
            if item.id == item_id:
                item.status = Status.QUEUED
                item.progress_pct = 0.0
                item.speed_str = ""
                self.downloader_tab.update_item_row(item)
                break
        self.start_queue()

    def get_active_index(self) -> int:
        idx = 1
        for item in self.downloader_tab.queue_items:
            if item == self.active_item:
                return idx
            if item.status in (Status.DONE, Status.SKIPPED, Status.SKIPPED_DUPLICATE, Status.ERROR, Status.CANCELLED):
                idx += 1
        return idx

    def process_next_queue_item(self):
        if self.queue_paused:
            self.downloader_tab.set_downloading(False)
            return

        # Find first QUEUED item
        next_item = None
        for item in self.downloader_tab.queue_items:
            if item.status == Status.QUEUED:
                next_item = item
                break

        if not next_item:
            # Queue complete!
            self.downloader_tab.set_downloading(False)
            self.active_item = None
            self.setWindowTitle("YT Music Downloader")
            
            # Reconcile all track stats from all items in the queue
            successes = 0
            errors = 0
            failed_names = []
            
            for item in self.downloader_tab.queue_items:
                successes += item.tracks_downloaded
                errors += item.tracks_error
                failed_names.extend(item.failed_tracks)
                
            # If successes or errors: show summary
            if successes > 0 or errors > 0:
                from gui.tabs.downloader import DownloadSummaryDialog
                dlg = DownloadSummaryDialog(successes, errors, failed_names, self)
                dlg.exec()
                if dlg.retry_requested:
                    # Retry failed items
                    # Reset all queue items that had errors
                    for item in self.downloader_tab.queue_items:
                        if item.tracks_error > 0 or item.status in (Status.ERROR, Status.SKIPPED):
                            item.status = Status.QUEUED
                            item.tracks_downloaded = 0
                            item.tracks_error = 0
                            item.failed_tracks = []
                            item.progress_pct = 0.0
                            item.speed_str = ""
                            self.downloader_tab.update_item_row(item)
                    self.start_queue()
            else:
                self.show_toast("All downloads finished")
            return

        # Launch DownloadWorker
        self.active_item = next_item
        self.downloader_tab.update_overall_progress()
        self.downloader_tab.update_item_progress(next_item.title, 0.0, "")

        self.current_worker = DownloadWorker(next_item, self.config)
        self.current_worker.progress_updated.connect(self.on_worker_progress)
        self.current_worker.playlist_item_changed.connect(self.on_worker_playlist_item)
        self.current_worker.status_changed.connect(self.on_worker_status_changed)
        self.current_worker.log_line.connect(self.on_worker_log_line)
        self.current_worker.error_occurred.connect(self.on_worker_error)
        self.current_worker.finished_item.connect(self.on_worker_finished_item)
        self.current_worker.start()

    # --- Worker Thread Slots ---
    @Slot(str, float, str)
    def on_worker_progress(self, item_id, percent, speed_str):
        if self.active_item and self.active_item.id == item_id:
            self.active_item.progress_pct = percent
            self.active_item.speed_str = speed_str
            self.downloader_tab.update_item_row(self.active_item)
            self.downloader_tab.update_item_progress(self.active_item.title, percent, speed_str)
            self.setWindowTitle(f"YT Music Downloader — Downloading... {int(percent)}%")

    @Slot(str, int, int)
    def on_worker_playlist_item(self, item_id, index, total):
        if self.active_item and self.active_item.id == item_id:
            self.active_item.track_count = total
            self.active_item.tracks_downloaded = index - 1
            self.active_item.subtitle = f"Playlist · track {index} of {total}"
            self.downloader_tab.update_item_row(self.active_item)
            self.downloader_tab.update_overall_progress()

    @Slot(str, object)
    def on_worker_status_changed(self, item_id, status):
        # Update in list
        for item in self.downloader_tab.queue_items:
            if item.id == item_id:
                item.status = status
                self.downloader_tab.update_item_row(item)
                # If this is the active item and we are downloading, refresh bottom bar name
                if self.active_item and self.active_item.id == item_id:
                    self.downloader_tab.update_item_progress(
                        self.active_item.title,
                        self.active_item.progress_pct,
                        self.active_item.speed_str
                    )
                break
        self.downloader_tab.update_overall_progress()
        self.downloader_tab.update_ui_state()

    @Slot(str, str)
    def on_worker_log_line(self, item_id, line):
        # Log is automatically appended to item.log_buffer inside the worker thread.
        # But we could print or debug log if needed:
        logger.debug(f"[WorkerLog:{item_id}] {line}")

    @Slot(str, str, str)
    def on_worker_error(self, item_id, error_type, message):
        # Add to error panel
        title = "Unknown Track"
        for item in self.downloader_tab.queue_items:
            if item.id == item_id:
                title = item.title
                if error_type == "content":
                    item.skipped_count += 1
                break
        self.downloader_tab.add_error_record(item_id, title, message)

    @Slot(str)
    def on_worker_finished_item(self, item_id):
        # Clean up active worker
        self.current_worker = None
        self.downloader_tab.update_overall_progress()
        self.process_next_queue_item()

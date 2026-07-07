import sys
from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtGui import QFont, QIcon
from gui.setup_window import SetupWindow
from gui.main_window import MainWindow
import logging
from utils.paths import LOGS_DIR, resource_path

# Set up logging at startup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("YTMusicDownloader")

def main():
    # Set AppUserModelID on Windows so taskbar groups the window with custom icon
    import ctypes
    try:
        myappid = "biraj.ytmusicdownloader.app.v1"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    
    # Set application icon
    icon_path = resource_path("public/app_icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # 1. Apply Fusion Style
    QApplication.setStyle(QStyleFactory.create("Fusion"))
    
    # 2. Set default font (Segoe UI, 9 pt ≈ 12 px)
    app.setFont(QFont("Segoe UI", 9))
    
    # 3. Check if dependencies are already present and functional
    from deps import checker
    ytdlp_ok, ffmpeg_ok = checker.deps_functional()
    
    if not (ytdlp_ok and ffmpeg_ok):
        logger.info("Dependencies missing or broken. Launching SetupWindow...")
        setup_dialog = SetupWindow()
        if setup_dialog.exec() != SetupWindow.Accepted:
            # User closed setup window or failed
            logger.warning("Setup window rejected. Exiting app.")
            sys.exit(0)
    else:
        logger.info("Dependencies verified in bin folder. Skipping SetupWindow.")
        
    logger.info("Dependencies verified. Launching MainWindow...")
    # 4. Show Main Window
    main_window = MainWindow()
    main_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

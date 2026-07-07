from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QByteArray, QSize, Qt, QRectF

SVG_ICONS = {
    "ti-download": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2 -2v-2" />
        <path d="M7 11l5 5l5 -5" />
        <path d="M12 4l0 12" />
    </svg>
    """,
    "ti-refresh": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20 11a8.1 8.1 0 0 0 -15.5 -2m-.5 -4v4h4" />
        <path d="M4 13a8.1 8.1 0 0 0 15.5 2m.5 4v-4h-4" />
    </svg>
    """,
    "ti-plus": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 5l0 14" />
        <path d="M5 12l14 0" />
    </svg>
    """,
    "ti-folder": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M5 19h14a2 2 0 0 0 2 -2v-5a2 2 0 0 0 -2 -2h-5l-2 -3h-7a2 2 0 0 0 -2 2v10a2 2 0 0 0 2 2z" />
    </svg>
    """,
    "ti-x": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M18 6l-12 12" />
        <path d="M6 6l12 12" />
    </svg>
    """,
    "ti-player-play": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M7 4v16l13 -8z" />
    </svg>
    """,
    "ti-player-pause": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M6 5m0 1a1 1 0 0 1 1 -1h2a1 1 0 0 1 1 1v12a1 1 0 0 1 -1 1h-2a1 1 0 0 1 -1 -1z" />
        <path d="M14 5m0 1a1 1 0 0 1 1 -1h2a1 1 0 0 1 1 1v12a1 1 0 0 1 -1 1h-2a1 1 0 0 1 -1 -1z" />
    </svg>
    """,
    "ti-clock": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 12a9 9 0 1 0 18 0a9 9 0 0 0 -18 0" />
        <path d="M12 7v5l3 3" />
    </svg>
    """,
    "ti-loader-2": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 3a9 9 0 1 0 9 9" />
    </svg>
    """,
    "ti-circle-check": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="9" />
        <path d="M9 12l2 2l4 -4" />
    </svg>
    """,
    "ti-alert-circle": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="9" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
    """,
    "ti-alert-triangle": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 9v4" />
        <path d="M12 17h.01" />
        <path d="M5 19h14a2 2 0 0 0 1.84 -2.75l-7.1 -12.25a2 2 0 0 0 -3.5 0l-7.1 12.25a2 2 0 0 0 1.75 2.75" />
    </svg>
    """,
    "ti-wifi-off": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 3l18 18" />
        <path d="M18.537 9.462a9 9 0 0 0 -13.074 0" />
        <path d="M15.713 12.288a5 5 0 0 0 -7.428 0" />
        <path d="M12 18l.01 0" />
    </svg>
    """,
    "ti-chevron-down": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="6 9 12 15 18 9" />
    </svg>
    """,
    "ti-chevron-up": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="18 15 12 9 6 15" />
    </svg>
    """,
    "ti-brand-github": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M9 19c-4.3 1.4 -4.3 -2.5 -6 -3m12 5v-3.5c0 -1 .1 -1.4 -.5 -2c2.8 -.3 5.5 -1.4 5.5 -6a4.6 4.6 0 0 0 -1.3 -3.2a4.2 4.2 0 0 0 -.1 -3.2s-1.1 -.3 -3.5 1.3a12.3 12.3 0 0 0 -6.2 0c-2.4 -1.6 -3.5 -1.3 -3.5 -1.3a4.2 4.2 0 0 0 -.1 3.2a4.6 4.6 0 0 0 -1.3 3.2c0 4.6 2.7 5.7 5.5 6c-.6 .6 -.6 1.2 -.5 2v3.5" />
    </svg>
    """,
    "ti-external-link": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 6h-6a2 2 0 0 0 -2 2v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-6" />
        <path d="M11 13l9 -9" />
        <path d="M15 4h5v5" />
    </svg>
    """,
    "ti-device-floppy": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M6 4h10l4 4v10a2 2 0 0 1 -2 2h-12a2 2 0 0 1 -2 -2v-12a2 2 0 0 1 2 -2" />
        <circle cx="12" cy="14" r="2" />
        <polyline points="14 4 14 8 8 8 8 4" />
    </svg>
    """,
    "ti-rotate-clockwise": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4.05 11a8 8 0 1 1 .5 4m-.5 5v-5h5" />
    </svg>
    """,
    "ti-playlist": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="9" y1="6" x2="20" y2="6" />
        <line x1="9" y1="12" x2="20" y2="12" />
        <line x1="9" y1="18" x2="20" y2="18" />
        <circle cx="5" cy="6" r="1" />
        <circle cx="5" cy="12" r="1" />
        <circle cx="5" cy="18" r="1" />
    </svg>
    """,
    "ti-music": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="6" cy="17" r="3" />
        <circle cx="16" cy="17" r="3" />
        <path d="M9 17v-13h10v13" />
        <path d="M9 8h10" />
    </svg>
    """,
    "ti-copy": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
    """,
    "win-min": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <line x1="4" y1="12" x2="20" y2="12" />
    </svg>
    """,
    "win-max": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <rect x="5" y="5" width="14" height="14" />
    </svg>
    """,
    "win-restore": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="8" width="12" height="12" />
        <path d="M8 8v-4h12v12h-4" />
    </svg>
    """,
    "win-close": """
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <line x1="6" y1="6" x2="18" y2="18" />
        <line x1="6" y1="18" x2="18" y2="6" />
    </svg>
    """
}

def get_svg_pixmap(name: str, color: str = "#333333", size: int = 16) -> QPixmap:
    """Renders a Tabler SVG icon as a QPixmap with High DPI support."""
    if name not in SVG_ICONS:
        return QPixmap()
    
    # Get Device Pixel Ratio (DPR) for high DPI screens
    from PySide6.QtWidgets import QApplication
    dpr = 1.0
    app = QApplication.instance()
    if app:
        screen = app.primaryScreen()
        if screen:
            dpr = screen.devicePixelRatio()
            
    svg_str = SVG_ICONS[name]
    svg_str_colored = svg_str.replace("currentColor", color)
    
    renderer = QSvgRenderer(QByteArray(svg_str_colored.encode("utf-8")))
    
    import math
    scaled_size = math.ceil(size * dpr)
    pixmap = QPixmap(scaled_size, scaled_size)
    pixmap.fill(Qt.transparent)
    pixmap.setDevicePixelRatio(dpr)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    
    # Render explicitly into the logical bounding box to prevent clipping/shifting
    target_rect = QRectF(0, 0, size, size)
    renderer.render(painter, target_rect)
    painter.end()
    
    return pixmap

def get_svg_icon(name: str, color: str = "#333333", size: int = 16) -> QIcon:
    """Renders a Tabler SVG icon with a specified color and size, with High DPI support."""
    pixmap = get_svg_pixmap(name, color, size)
    return QIcon(pixmap)

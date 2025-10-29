from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import Qt, QSize
import os

class IconManager:
    _instance = None
    _icons_cache = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IconManager, cls).__new__(cls)
            cls._instance._init_icons()
        return cls._instance
    
    def _init_icons(self):
        self.icons_dir = os.path.join(os.path.dirname(__file__), "Icons")
        
    def get_icon(self, name, color="#FFFFFF", size=24):
        cache_key = f"{name}_{color}_{size}"
        
        if cache_key in self._icons_cache:
            return self._icons_cache[cache_key]
        
        icon_path = os.path.join(self.icons_dir, f"{name}.svg")
        
        if not os.path.exists(icon_path):
            return QIcon()
        
        renderer = QSvgRenderer(icon_path)
        
        if not renderer.isValid():
            return QIcon()
        
        pixmap = QPixmap(QSize(size, size))
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        icon = QIcon(pixmap)
        self._icons_cache[cache_key] = icon
        
        return icon
    
    def get_pixmap(self, name, size=24):
        icon_path = os.path.join(self.icons_dir, f"{name}.svg")
        
        if not os.path.exists(icon_path):
            return QPixmap()
        
        renderer = QSvgRenderer(icon_path)
        
        if not renderer.isValid():
            return QPixmap()
        
        pixmap = QPixmap(QSize(size, size))
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        return pixmap

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import Qt, QSize, QByteArray
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
        
    def get_icon(self, name, color=None, size=24):
        cache_key = f"{name}_{color}_{size}"
        
        if cache_key in self._icons_cache:
            return self._icons_cache[cache_key]
        
        icon_path = os.path.join(self.icons_dir, f"{name}.svg")
        
        if not os.path.exists(icon_path):
            return QIcon()
        
        if color:
            pixmap = self._get_colored_pixmap(icon_path, color, size)
        else:
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
    
    def _get_colored_pixmap(self, icon_path, color, size):
        """Create a pixmap with custom stroke color"""
        with open(icon_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        # Replace stroke color in SVG
        import re
        svg_content = re.sub(r'stroke="[^"]*"', f'stroke="{color}"', svg_content)
        
        renderer = QSvgRenderer(QByteArray(svg_content.encode('utf-8')))
        
        if not renderer.isValid():
            return QPixmap()
        
        pixmap = QPixmap(QSize(size, size))
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        return pixmap
    
    def get_pixmap(self, name, size=24, color=None):
        icon_path = os.path.join(self.icons_dir, f"{name}.svg")
        
        if not os.path.exists(icon_path):
            return QPixmap()
        
        if color:
            return self._get_colored_pixmap(icon_path, color, size)
        
        renderer = QSvgRenderer(icon_path)
        
        if not renderer.isValid():
            return QPixmap()
        
        pixmap = QPixmap(QSize(size, size))
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        return pixmap

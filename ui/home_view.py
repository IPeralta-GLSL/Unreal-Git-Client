from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class HomeView(QWidget):
    open_repo_requested = pyqtSignal()
    clone_repo_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        layout.setContentsMargins(20, 20, 20, 20)
        
        spacer_top = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(spacer_top)
        
        logo_label = QLabel("🎮")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("font-size: 80px;")
        layout.addWidget(logo_label)
        
        title = QLabel("Unreal Git Client")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        title.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: white;
            margin: 10px;
        """)
        layout.addWidget(title)
        
        subtitle = QLabel("Cliente Git intuitivo para proyectos de Unreal Engine")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("""
            font-size: 16px;
            color: #888888;
            margin-bottom: 30px;
        """)
        layout.addWidget(subtitle)
        
        buttons_container = QWidget()
        buttons_container.setMinimumWidth(400)
        buttons_container.setMaximumWidth(700)
        buttons_layout = QVBoxLayout(buttons_container)
        buttons_layout.setSpacing(15)
        
        open_btn = self.create_action_button(
            "📁 Abrir Repositorio",
            "Abre un repositorio Git existente en tu computadora",
            "#0e639c"
        )
        open_btn.clicked.connect(self.open_repo_requested.emit)
        buttons_layout.addWidget(open_btn)
        
        clone_btn = self.create_action_button(
            "↓ Clonar Repositorio",
            "Descarga una copia de un repositorio remoto",
            "#0e639c"
        )
        clone_btn.clicked.connect(self.clone_repo_requested.emit)
        buttons_layout.addWidget(clone_btn)
        
        layout.addWidget(buttons_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        tips_container = QWidget()
        tips_container.setMinimumWidth(400)
        tips_container.setMaximumWidth(800)
        tips_layout = QVBoxLayout(tips_container)
        tips_layout.setSpacing(10)
        
        tips_title = QLabel("💡 Consejos Rápidos")
        tips_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #4ec9b0; margin-top: 20px;")
        tips_layout.addWidget(tips_title)
        
        tips = [
            "• Usa 'Nueva Pestaña' para trabajar con múltiples repositorios",
            "• Git LFS es esencial para proyectos de Unreal Engine",
            "• Escribe mensajes de commit descriptivos y claros",
            "• Usa Pull antes de Push para evitar conflictos"
        ]
        
        for tip in tips:
            tip_label = QLabel(tip)
            tip_label.setWordWrap(True)
            tip_label.setStyleSheet("font-size: 12px; color: #cccccc; padding: 3px;")
            tips_layout.addWidget(tip_label)
        
        layout.addWidget(tips_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        spacer_bottom = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(spacer_bottom)
        
        version_label = QLabel("v1.0.0 • Soporte para Git LFS y Unreal Engine")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setWordWrap(True)
        version_label.setStyleSheet("font-size: 10px; color: #555555; margin: 10px;")
        layout.addWidget(version_label)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
            }
        """)
        
    def create_action_button(self, text, description, color):
        button = QPushButton()
        button.setMinimumHeight(90)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: none;
                border-radius: 8px;
                padding: 20px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {self.lighten_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color)};
            }}
        """)
        
        layout = QVBoxLayout(button)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        btn_text = QLabel(text)
        btn_text.setWordWrap(True)
        btn_text.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: white;
            background: transparent;
        """)
        layout.addWidget(btn_text)
        
        btn_desc = QLabel(description)
        btn_desc.setWordWrap(True)
        btn_desc.setStyleSheet("""
            font-size: 13px;
            color: rgba(255, 255, 255, 0.9);
            background: transparent;
            line-height: 1.4;
        """)
        layout.addWidget(btn_desc)
        
        return button
    
    def lighten_color(self, color):
        color_map = {
            "#0e639c": "#1177bb",
            "#16825d": "#1a9d6f"
        }
        return color_map.get(color, color)
    
    def darken_color(self, color):
        color_map = {
            "#0e639c": "#0d5a8f",
            "#16825d": "#136d4d"
        }
        return color_map.get(color, color)

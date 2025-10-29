from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QSizePolicy, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import os

class HomeView(QWidget):
    open_repo_requested = pyqtSignal()
    clone_repo_requested = pyqtSignal()
    open_recent_repo = pyqtSignal(str)
    
    def __init__(self, settings_manager=None, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1e1e1e;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #3d3d3d;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4d4d4d;
            }
        """)
        
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        header_container = QWidget()
        header_container.setMaximumWidth(900)
        header_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        header_layout = QVBoxLayout(header_container)
        header_layout.setSpacing(15)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("Git Client")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        title.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: white;
            margin: 5px;
        """)
        header_layout.addWidget(title)
        
        layout.addWidget(header_container)
        
        buttons_container = QWidget()
        buttons_container.setMaximumWidth(900)
        buttons_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setSpacing(15)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        open_btn = self.create_action_button(
            "📁 Abrir Repositorio",
            "Abre un repositorio Git existente",
            "#0e639c"
        )
        open_btn.clicked.connect(self.open_repo_requested.emit)
        buttons_layout.addWidget(open_btn)
        
        clone_btn = self.create_action_button(
            "↓ Clonar Repositorio",
            "Descarga un repositorio remoto",
            "#0e639c"
        )
        clone_btn.clicked.connect(self.clone_repo_requested.emit)
        buttons_layout.addWidget(clone_btn)
        
        layout.addWidget(buttons_container)
        
        content_splitter = QWidget()
        content_splitter.setMaximumWidth(1200)
        content_splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout = QHBoxLayout(content_splitter)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        left_panel = QWidget()
        left_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        recent_section = self.create_recent_repos_section()
        if recent_section:
            left_layout.addWidget(recent_section)
        else:
            placeholder = QLabel("No hay repositorios recientes")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: #666666; font-size: 14px; padding: 40px;")
            left_layout.addWidget(placeholder)
        
        left_layout.addStretch()
        
        right_panel = QWidget()
        right_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        tips_container = QFrame()
        tips_container.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        tips_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tips_layout = QVBoxLayout(tips_container)
        tips_layout.setSpacing(12)
        
        tips_title = QLabel("💡 Consejos Rápidos")
        tips_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #4ec9b0;")
        tips_layout.addWidget(tips_title)
        
        tips = [
            ("⌨️", "Ctrl+T para nueva pestaña, Ctrl+W para cerrar"),
            ("🎮", "Git LFS es esencial para proyectos de Unreal Engine"),
            ("💬", "Escribe mensajes de commit descriptivos y claros"),
            ("🔄", "Usa Pull antes de Push para evitar conflictos"),
            ("🌿", "Crea ramas para nuevas características"),
        ]
        
        for icon, tip in tips:
            tip_container = QWidget()
            tip_layout = QHBoxLayout(tip_container)
            tip_layout.setContentsMargins(0, 0, 0, 0)
            tip_layout.setSpacing(10)
            
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 16px;")
            icon_label.setFixedWidth(30)
            tip_layout.addWidget(icon_label)
            
            tip_label = QLabel(tip)
            tip_label.setWordWrap(True)
            tip_label.setStyleSheet("font-size: 12px; color: #cccccc;")
            tip_layout.addWidget(tip_label, stretch=1)
            
            tips_layout.addWidget(tip_container)
        
        right_layout.addWidget(tips_container)
        right_layout.addStretch()
        
        content_layout.addWidget(left_panel, stretch=1)
        content_layout.addWidget(right_panel, stretch=1)
        
        layout.addWidget(content_splitter)
        
        layout.addStretch()
        
        footer = QWidget()
        footer.setMaximumWidth(900)
        footer_layout = QVBoxLayout(footer)
        footer_layout.setSpacing(5)
        footer_layout.setContentsMargins(0, 20, 0, 0)
        
        shortcuts_label = QLabel("💡 Atajos: Ctrl+T nueva pestaña • Ctrl+W cerrar • Ctrl+Tab cambiar")
        shortcuts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shortcuts_label.setWordWrap(True)
        shortcuts_label.setStyleSheet("color: #666666; font-size: 11px;")
        footer_layout.addWidget(shortcuts_label)
        
        version_label = QLabel("v1.0.0 • Soporte para Git LFS y Unreal Engine")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setWordWrap(True)
        version_label.setStyleSheet("font-size: 10px; color: #555555;")
        footer_layout.addWidget(version_label)
        
        layout.addWidget(footer)
        
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
            }
        """)
    
    def create_recent_repos_section(self):
        if not self.settings_manager:
            return None
        
        recent_repos = self.settings_manager.get_recent_repos()
        if not recent_repos:
            return None
        
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        section.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(10)
        
        header = QLabel("📚 Repositorios Recientes")
        header.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: bold;")
        layout.addWidget(header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(200)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #3d3d3d;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4d4d4d;
            }
        """)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(8)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        for repo in recent_repos[:8]:
            repo_btn = self.create_recent_repo_item(repo)
            scroll_layout.addWidget(repo_btn)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        return section
    
    def create_recent_repo_item(self, repo):
        btn = QPushButton()
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setMinimumHeight(60)
        
        repo_name = repo.get('name', os.path.basename(repo['path']))
        repo_path = repo['path']
        
        is_unreal = os.path.exists(os.path.join(repo_path, 'Content')) or \
                    any(f.endswith('.uproject') for f in os.listdir(repo_path) if os.path.isfile(os.path.join(repo_path, f)))
        
        icon = "🎮" if is_unreal else "📁"
        
        btn.setStyleSheet("""
            QPushButton {
                background-color: #1e1e1e;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                padding: 12px 15px;
                text-align: left;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2d2d2d;
                border-color: #007acc;
            }
            QPushButton:pressed {
                background-color: #094771;
            }
        """)
        
        btn.setText(f"{icon}  {repo_name}\n    📍 {repo_path}")
        btn.clicked.connect(lambda: self.open_recent_repo.emit(repo_path))
        
        return btn
    
    def refresh_recent_repos(self):
        self.init_ui()
        
    def create_action_button(self, text, description, color):
        button = QPushButton()
        button.setMinimumHeight(80)
        button.setMaximumHeight(100)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
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
            font-size: 16px;
            font-weight: bold;
            color: white;
            background: transparent;
        """)
        layout.addWidget(btn_text)
        
        btn_desc = QLabel(description)
        btn_desc.setWordWrap(True)
        btn_desc.setStyleSheet("""
            font-size: 12px;
            color: rgba(255, 255, 255, 0.85);
            background: transparent;
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

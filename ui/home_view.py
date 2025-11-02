from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QSizePolicy, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont
from ui.icon_manager import IconManager
from ui.theme import get_current_theme
from core.translations import tr
import os

class HomeView(QWidget):
    open_repo_requested = pyqtSignal()
    clone_repo_requested = pyqtSignal()
    open_recent_repo = pyqtSignal(str)
    
    def __init__(self, settings_manager=None, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.icon_manager = IconManager()
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        theme = get_current_theme()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: palette(window);
            }}
            QScrollBar:vertical {{
                background-color: palette(window);
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: palette(text);
                border-radius: 6px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme.colors['surface_hover']};
            }}
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
        
        self.title = QLabel(tr('git_client'))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setWordWrap(True)
        self.title.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: palette(bright-text);
            margin: 5px;
        """)
        header_layout.addWidget(self.title)
        
        layout.addWidget(header_container)
        
        buttons_container = QWidget()
        buttons_container.setMaximumWidth(900)
        buttons_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setSpacing(15)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        theme = get_current_theme()
        
        self.open_btn = self.create_action_button(
            f" {tr('open_repository_btn')}",
            tr('open_repository_desc'),
            theme.colors['primary'],
            "folder-open"
        )
        self.open_btn.clicked.connect(self.open_repo_requested.emit)
        buttons_layout.addWidget(self.open_btn)
        
        self.clone_btn = self.create_action_button(
            f"↓ {tr('clone_repository_btn')}",
            tr('clone_repository_desc'),
            theme.colors['primary']
        )
        self.clone_btn.clicked.connect(self.clone_repo_requested.emit)
        buttons_layout.addWidget(self.clone_btn)
        
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
            self.no_recent_placeholder = None
        else:
            self.no_recent_placeholder = QLabel(tr('no_recent_repos'))
            self.no_recent_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.no_recent_placeholder.setStyleSheet("color: palette(text); font-size: 14px; padding: 40px;")
            left_layout.addWidget(self.no_recent_placeholder)
        
        left_layout.addStretch()
        
        right_panel = QWidget()
        right_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(10)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        tips_container = QFrame()
        tips_container.setStyleSheet("""
            QFrame {
                background-color: palette(base);
                border-radius: 10px;
                padding: 20px;
            }
        """)
        tips_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tips_layout = QVBoxLayout(tips_container)
        tips_layout.setSpacing(12)
        
        tips_title_layout = QHBoxLayout()
        tips_icon = QLabel()
        tips_icon.setPixmap(self.icon_manager.get_pixmap("lightbulb", size=20))
        tips_title_layout.addWidget(tips_icon)
        
        self.tips_title = QLabel(f" {tr('quick_tips')}")
        self.tips_title.setStyleSheet("font-size: 15px; font-weight: bold; color: palette(link);")
        tips_title_layout.addWidget(self.tips_title)
        tips_title_layout.addStretch()
        tips_layout.addLayout(tips_title_layout)
        
        tips_data = [
            ("plus-circle", 'tip_new_tab'),
            ("file-code", 'tip_git_lfs'),
            ("git-commit", 'tip_commit_messages'),
            ("git-diff", 'tip_pull_before_push'),
            ("git-branch", 'tip_create_branches'),
        ]
        
        self.tip_labels = []
        for icon_name, tip_key in tips_data:
            tip_container = QWidget()
            tip_layout = QHBoxLayout(tip_container)
            tip_layout.setContentsMargins(0, 0, 0, 0)
            tip_layout.setSpacing(10)
            
            icon_label = QLabel()
            icon_label.setPixmap(self.icon_manager.get_pixmap(icon_name, size=16))
            icon_label.setStyleSheet("font-size: 16px;")
            icon_label.setFixedWidth(30)
            tip_layout.addWidget(icon_label)
            
            tip_label = QLabel(tr(tip_key))
            tip_label.setWordWrap(True)
            tip_label.setStyleSheet("font-size: 12px; color: palette(window-text);")
            tip_layout.addWidget(tip_label, stretch=1)
            
            self.tip_labels.append((tip_label, tip_key))
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
        
        self.shortcuts_label = QLabel(tr('shortcuts_text'))
        self.shortcuts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.shortcuts_label.setWordWrap(True)
        self.shortcuts_label.setStyleSheet("color: palette(text); font-size: 11px;")
        footer_layout.addWidget(self.shortcuts_label)
        
        self.version_label = QLabel(tr('version_text'))
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setWordWrap(True)
        self.version_label.setStyleSheet("font-size: 10px; color: palette(text);")
        footer_layout.addWidget(self.version_label)
        
        layout.addWidget(footer)
        
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
        
        self.setStyleSheet("""
            QWidget {
                background-color: palette(window);
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
                background-color: palette(base);
                border-radius: 10px;
                padding: 20px;
            }
        """)
        section.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(10)
        
        header_layout = QHBoxLayout()
        header_icon = QLabel()
        header_icon.setPixmap(self.icon_manager.get_pixmap("folders", size=20))
        header_layout.addWidget(header_icon)
        
        self.recent_repos_header = QLabel(f" {tr('recent_repositories')}")
        self.recent_repos_header.setStyleSheet("color: palette(bright-text); font-size: 15px; font-weight: bold;")
        header_layout.addWidget(self.recent_repos_header)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        theme = get_current_theme()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(200)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: palette(window);
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: palette(text);
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme.colors['surface_hover']};
            }}
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
        
        icon_name = "file-code" if is_unreal else "folder"
        btn.setIcon(self.icon_manager.get_icon(icon_name, size=24))
        
        btn.setStyleSheet("""
            QPushButton {
                background-color: palette(window);
                border: 2px solid palette(mid);
                border-radius: 8px;
                padding: 12px 15px;
                text-align: left;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: palette(button);
                border-color: palette(link);
            }
            QPushButton:pressed {
                background-color: palette(highlight);
                color: palette(bright-text);
            }
        """)
        
        btn.setText(f"{repo_name}\n    {repo_path}")
        btn.clicked.connect(lambda: self.open_recent_repo.emit(repo_path))
        
        return btn
    
    def refresh_recent_repos(self):
        self.init_ui()
        
    def create_action_button(self, text, description, color, icon_name=None):
        button = QPushButton()
        button.setMinimumHeight(80)
        button.setMaximumHeight(100)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        theme = get_current_theme()
        
        if icon_name:
            button.setIcon(self.icon_manager.get_icon(icon_name, size=32))
            button.setIconSize(QSize(32, 32))
        
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: none;
                border-radius: 8px;
                padding: 20px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {theme.colors['primary_pressed']};
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
            color: palette(bright-text);
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
        
        button.text_label = btn_text
        button.desc_label = btn_desc
        
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
    
    def update_translations(self):
        if hasattr(self, 'title'):
            self.title.setText(tr('git_client'))
        
        if hasattr(self, 'open_btn'):
            self.open_btn.text_label.setText(f" {tr('open_repository_btn')}")
            self.open_btn.desc_label.setText(tr('open_repository_desc'))
        
        if hasattr(self, 'clone_btn'):
            self.clone_btn.text_label.setText(f"↓ {tr('clone_repository_btn')}")
            self.clone_btn.desc_label.setText(tr('clone_repository_desc'))
        
        if hasattr(self, 'recent_repos_header'):
            self.recent_repos_header.setText(f" {tr('recent_repositories')}")
        
        if hasattr(self, 'no_recent_placeholder') and self.no_recent_placeholder:
            self.no_recent_placeholder.setText(tr('no_recent_repos'))
        
        if hasattr(self, 'tips_title'):
            self.tips_title.setText(f" {tr('quick_tips')}")
        
        if hasattr(self, 'tip_labels'):
            for tip_label, tip_key in self.tip_labels:
                tip_label.setText(tr(tip_key))
        
        if hasattr(self, 'shortcuts_label'):
            self.shortcuts_label.setText(tr('shortcuts_text'))
        
        if hasattr(self, 'version_label'):
            self.version_label.setText(tr('version_text'))

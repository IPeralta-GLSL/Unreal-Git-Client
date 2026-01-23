from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QSizePolicy, QScrollArea, QGraphicsDropShadowEffect,
                             QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty, QPointF, QUrl
from PyQt6.QtGui import QFont, QColor, QAction, QDesktopServices
from ui.icon_manager import IconManager
from ui.theme import get_current_theme
from core.translations import tr
import os
import subprocess
import platform

class HomeView(QWidget):
    open_repo_requested = pyqtSignal()
    clone_repo_requested = pyqtSignal()
    open_recent_repo = pyqtSignal(str)
    remove_recent_repo = pyqtSignal(str)
    folder_dropped = pyqtSignal(str)
    
    def __init__(self, settings_manager=None, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.icon_manager = IconManager()
        self.setAcceptDrops(True)
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
                background-color: transparent;
                width: 14px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background-color: palette(mid);
                border-radius: 7px;
                min-height: 40px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme.colors['surface_hover']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        layout.setSpacing(35)
        layout.setContentsMargins(50, 60, 50, 50)
        
        header_container = QWidget()
        header_container.setMaximumWidth(1000)
        header_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        header_layout = QVBoxLayout(header_container)
        header_layout.setSpacing(12)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.title = QLabel(tr('git_client'))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setWordWrap(True)
        
        layout.addWidget(header_container)
        
        buttons_container = QWidget()
        buttons_container.setMaximumWidth(1000)
        buttons_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setSpacing(20)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        theme = get_current_theme()
        
        self.open_btn = self.create_action_button(
            tr('open_repository_btn'),
            tr('open_repository_desc'),
            theme.colors['primary'],
            "folder-open"
        )
        self.open_btn.clicked.connect(self.open_repo_requested.emit)
        buttons_layout.addWidget(self.open_btn)
        
        self.clone_btn = self.create_action_button(
            tr('clone_repository_btn'),
            tr('clone_repository_desc'),
            "#16825d",
            "download"
        )
        self.clone_btn.clicked.connect(self.clone_repo_requested.emit)
        buttons_layout.addWidget(self.clone_btn)
        
        layout.addWidget(buttons_container)
        
        content_splitter = QWidget()
        content_splitter.setMaximumWidth(1300)
        content_splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout = QHBoxLayout(content_splitter)
        content_layout.setSpacing(25)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        left_panel = QWidget()
        left_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(12)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        recent_section = self.create_recent_repos_section()
        if recent_section:
            left_layout.addWidget(recent_section)
            self.no_recent_placeholder = None
        else:
            placeholder_frame = QFrame()
            placeholder_frame.setStyleSheet("""
                QFrame {
                    background-color: palette(base);
                    border-radius: 12px;
                    border: none;
                }
            """)
            placeholder_layout = QVBoxLayout(placeholder_frame)
            placeholder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder_layout.setSpacing(15)
            placeholder_layout.setContentsMargins(40, 60, 40, 60)
            
            empty_icon = QLabel()
            empty_icon.setPixmap(self.icon_manager.get_pixmap("folders", size=64))
            empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder_layout.addWidget(empty_icon)
            
            self.no_recent_placeholder = QLabel(tr('no_recent_repos'))
            self.no_recent_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.no_recent_placeholder.setWordWrap(True)
            self.no_recent_placeholder.setStyleSheet("""
                color: palette(text); 
                font-size: 15px; 
                font-weight: 500;
            """)
            placeholder_layout.addWidget(self.no_recent_placeholder)
            
            self.hint_label = QLabel(tr('home_hint'))
            self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.hint_label.setWordWrap(True)
            self.hint_label.setStyleSheet("""
                color: palette(mid); 
                font-size: 12px;
            """)
            placeholder_layout.addWidget(self.hint_label)
            
            left_layout.addWidget(placeholder_frame)
        
        left_layout.addStretch()
        
        right_panel = QWidget()
        right_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(12)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        tips_container = QFrame()
        tips_container.setStyleSheet(f"""
            QFrame {{
                background-color: palette(base);
                border-radius: 12px;
                border: none;
            }}
        """)
        tips_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tips_layout = QVBoxLayout(tips_container)
        tips_layout.setSpacing(15)
        tips_layout.setContentsMargins(25, 25, 25, 25)
        
        tips_title_layout = QHBoxLayout()
        tips_icon = QLabel()
        tips_icon.setPixmap(self.icon_manager.get_pixmap("lightbulb", size=22))
        tips_title_layout.addWidget(tips_icon)
        
        self.tips_title = QLabel(tr('quick_tips'))
        self.tips_title.setStyleSheet(f"""
            font-size: 16px; 
            font-weight: 600; 
            color: {theme.colors['primary']};
            margin-left: 8px;
        """)
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
            tip_layout.setSpacing(12)
            
            icon_label = QLabel()
            icon_label.setPixmap(self.icon_manager.get_pixmap(icon_name, size=18))
            icon_label.setFixedWidth(32)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tip_layout.addWidget(icon_label)
            
            tip_label = QLabel(tr(tip_key))
            tip_label.setWordWrap(True)
            tip_label.setStyleSheet("""
                font-size: 13px; 
                color: palette(window-text);
                line-height: 1.5;
            """)
            tip_layout.addWidget(tip_label, stretch=1)
            
            self.tip_labels.append((tip_label, tip_key))
            tips_layout.addWidget(tip_container)
        
        right_layout.addWidget(tips_container)
        right_layout.addStretch()
        
        content_layout.addWidget(left_panel, stretch=3)
        content_layout.addWidget(right_panel, stretch=2)
        
        layout.addWidget(content_splitter)
        
        layout.addStretch()
        
        footer = QWidget()
        footer.setMaximumWidth(1000)
        footer_layout = QVBoxLayout(footer)
        footer_layout.setSpacing(8)
        footer_layout.setContentsMargins(0, 30, 0, 0)
        
        shortcuts_container = QFrame()
        shortcuts_container.setStyleSheet("""
            QFrame {
                background-color: rgba(128, 128, 128, 0.05);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        shortcuts_layout = QVBoxLayout(shortcuts_container)
        shortcuts_layout.setSpacing(5)
        
        self.shortcuts_label = QLabel(tr('shortcuts_text'))
        self.shortcuts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.shortcuts_label.setWordWrap(True)
        self.shortcuts_label.setStyleSheet("""
            color: palette(text); 
            font-size: 12px;
            font-weight: 500;
        """)
        shortcuts_layout.addWidget(self.shortcuts_label)
        
        footer_layout.addWidget(shortcuts_container)
        
        self.version_label = QLabel(tr('version_text'))
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setWordWrap(True)
        self.version_label.setStyleSheet("""
            font-size: 11px; 
            color: palette(mid);
            margin-top: 5px;
        """)
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
        
        theme = get_current_theme()
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: palette(base);
                border-radius: 12px;
                border: none;
            }}
        """)
        section.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        header_layout = QHBoxLayout()
        header_icon = QLabel()
        header_icon.setPixmap(self.icon_manager.get_pixmap("folders", size=22))
        header_layout.addWidget(header_icon)
        
        self.recent_repos_header = QLabel(tr('recent_repositories'))
        self.recent_repos_header.setStyleSheet(f"""
            color: {theme.colors['primary']}; 
            font-size: 16px; 
            font-weight: 600; 
            margin-left: 8px;
        """)
        header_layout.addWidget(self.recent_repos_header)
        header_layout.addStretch()
        
        repo_count = QLabel(f"{len(recent_repos[:8])}")
        repo_count.setStyleSheet(f"""
            background-color: {theme.colors['primary']};
            color: white;
            font-size: 11px;
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 10px;
        """)
        header_layout.addWidget(repo_count)
        
        layout.addLayout(header_layout)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(220)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: transparent;
                width: 10px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background-color: palette(mid);
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme.colors['surface_hover']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(10)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        for repo in recent_repos[:8]:
            repo_btn = self.create_recent_repo_item(repo)
            scroll_layout.addWidget(repo_btn)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        return section
    
    def create_recent_repo_item(self, repo):
        theme = get_current_theme()
        btn = QPushButton()
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setMinimumHeight(70)
        
        repo_name = repo.get('name', os.path.basename(repo['path']))
        repo_path = repo['path']
        
        is_unreal = os.path.exists(os.path.join(repo_path, 'Content')) or \
                    any(f.endswith('.uproject') for f in os.listdir(repo_path) if os.path.isfile(os.path.join(repo_path, f)))
        
        icon_name = "file-code" if is_unreal else "folder"
        btn.setIcon(self.icon_manager.get_icon(icon_name, size=28))
        btn.setIconSize(QSize(28, 28))
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 10px;
                padding: 15px 18px;
                text-align: left;
                font-size: 14px;
                font-weight: 500;
                color: palette(bright-text);
            }}
            QPushButton:hover {{
                background-color: {theme.colors['surface_hover']};
            }}
            QPushButton:pressed {{
                background-color: {theme.colors['primary']};
                color: white;
            }}
        """)

        shadow = QGraphicsDropShadowEffect(btn)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setBlurRadius(16)
        shadow.setOffset(QPointF(0, 3))
        btn.setGraphicsEffect(shadow)

        btn._hover_blur_anim = QPropertyAnimation(shadow, b"blurRadius", btn)
        btn._hover_blur_anim.setDuration(180)
        btn._hover_blur_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        btn._hover_offset_anim = QPropertyAnimation(shadow, b"offset", btn)
        btn._hover_offset_anim.setDuration(180)
        btn._hover_offset_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def animate_shadow(blur_end: float, offset_end: QPointF):
            btn._hover_blur_anim.stop()
            btn._hover_blur_anim.setStartValue(shadow.blurRadius())
            btn._hover_blur_anim.setEndValue(blur_end)
            btn._hover_blur_anim.start()

            btn._hover_offset_anim.stop()
            btn._hover_offset_anim.setStartValue(shadow.offset())
            btn._hover_offset_anim.setEndValue(offset_end)
            btn._hover_offset_anim.start()

        def on_enter(event):
            animate_shadow(26.0, QPointF(0, 8))
            super(QPushButton, btn).enterEvent(event)

        def on_leave(event):
            animate_shadow(16.0, QPointF(0, 3))
            super(QPushButton, btn).leaveEvent(event)

        btn.enterEvent = on_enter
        btn.leaveEvent = on_leave
        
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(4)
        btn_layout.setContentsMargins(45, 0, 0, 0)
        
        name_label = QLabel(repo_name)
        name_label.setStyleSheet("""
            background-color: transparent;
            font-size: 15px;
            font-weight: bold;
            color: palette(bright-text);
        """)
        btn_layout.addWidget(name_label)
        
        path_label = QLabel(repo_path)
        path_label.setStyleSheet("""
            background-color: transparent;
            font-size: 12px;
            color: palette(text);
            opacity: 0.8;
        """)
        path_label.setWordWrap(False)
        btn_layout.addWidget(path_label)
        
        btn.setLayout(btn_layout)
        btn.clicked.connect(lambda: self.open_recent_repo.emit(repo_path))
        
        btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        btn.customContextMenuRequested.connect(lambda pos: self.show_repo_context_menu(btn, repo_path, pos))
        
        return btn
    
    def show_repo_context_menu(self, button, repo_path, pos):
        theme = get_current_theme()
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 16px;
                border-radius: 4px;
                color: {theme.colors['text']};
            }}
            QMenu::item:selected {{
                background-color: {theme.colors['primary']};
                color: white;
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {theme.colors['border']};
                margin: 4px 8px;
            }}
        """)
        
        open_action = QAction(self.icon_manager.get_icon("folder-open"), tr('open_repository'), self)
        open_action.triggered.connect(lambda: self.open_recent_repo.emit(repo_path))
        menu.addAction(open_action)
        
        open_folder_action = QAction(self.icon_manager.get_icon("folder"), tr('open_in_explorer'), self)
        open_folder_action.triggered.connect(lambda: self.open_folder_in_explorer(repo_path))
        menu.addAction(open_folder_action)
        
        menu.addSeparator()
        
        remove_action = QAction(self.icon_manager.get_icon("trash"), tr('remove_from_list'), self)
        remove_action.triggered.connect(lambda: self.remove_repo_from_list(repo_path))
        menu.addAction(remove_action)
        
        menu.exec(button.mapToGlobal(pos))
    
    def open_folder_in_explorer(self, path):
        if os.path.exists(path):
            if platform.system() == 'Windows':
                subprocess.run(['explorer', path])
            elif platform.system() == 'Darwin':
                subprocess.run(['open', path])
            else:
                subprocess.run(['xdg-open', path])
    
    def remove_repo_from_list(self, repo_path):
        if self.settings_manager:
            self.settings_manager.remove_recent_repo(repo_path)
            self.refresh_recent_repos()
        self.remove_recent_repo.emit(repo_path)
    
    def refresh_recent_repos(self):
        self.init_ui()
        
    def create_action_button(self, text, description, color, icon_name=None):
        theme = get_current_theme()
        button = QPushButton()
        button.setMinimumHeight(100)
        button.setMaximumHeight(120)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        hover_color = self.lighten_color(color)
        pressed_color = self.darken_color(color)
        
        button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color}, stop:1 {self.darken_color(color)});
                border: none;
                border-radius: 12px;
                padding: 0px;
                text-align: left;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {hover_color}, stop:1 {color});
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {pressed_color}, stop:1 {self.darken_color(pressed_color)});
            }}
        """)
        
        layout = QHBoxLayout(button)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        if icon_name:
            icon_label = QLabel()
            icon_label.setPixmap(self.icon_manager.get_pixmap(icon_name, size=40))
            icon_label.setStyleSheet("background: transparent; border: none;")
            icon_label.setFixedSize(40, 40)
            layout.addWidget(icon_label)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        btn_text = QLabel(text)
        btn_text.setWordWrap(True)
        text_font = QFont()
        text_font.setPointSize(15)
        text_font.setWeight(QFont.Weight.Bold)
        btn_text.setFont(text_font)
        btn_text.setStyleSheet("""
            color: white;
            background: transparent;
            border: none;
        """)
        text_layout.addWidget(btn_text)
        
        btn_desc = QLabel(description)
        btn_desc.setWordWrap(True)
        btn_desc.setStyleSheet("""
            font-size: 13px;
            color: rgba(255, 255, 255, 0.9);
            background: transparent;
            border: none;
        """)
        text_layout.addWidget(btn_desc)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        button.text_label = btn_text
        button.desc_label = btn_desc
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        button.setGraphicsEffect(shadow)
        
        return button
    
    def lighten_color(self, color):
        color_map = {
            "#0e639c": "#1a7ab8",
            "#16825d": "#1e9d73",
            "#2c5f2d": "#3a7a3c"
        }
        return color_map.get(color, color)
    
    def darken_color(self, color):
        color_map = {
            "#0e639c": "#0a5280",
            "#16825d": "#126d4d",
            "#2c5f2d": "#234a24",
            "#1a7ab8": "#0e639c",
            "#1e9d73": "#16825d",
            "#3a7a3c": "#2c5f2d"
        }
        return color_map.get(color, color)
    
    def update_translations(self):
        if hasattr(self, 'title'):
            self.title.setText(tr('git_client'))
        
        if hasattr(self, 'open_btn'):
            self.open_btn.text_label.setText(tr('open_repository_btn'))
            self.open_btn.desc_label.setText(tr('open_repository_desc'))
        
        if hasattr(self, 'clone_btn'):
            self.clone_btn.text_label.setText(tr('clone_repository_btn'))
            self.clone_btn.desc_label.setText(tr('clone_repository_desc'))
        
        if hasattr(self, 'recent_repos_header'):
            self.recent_repos_header.setText(tr('recent_repositories'))
        
        if hasattr(self, 'no_recent_placeholder') and self.no_recent_placeholder:
            self.no_recent_placeholder.setText(tr('no_recent_repos'))
        
        if hasattr(self, 'hint_label'):
            self.hint_label.setText(tr('home_hint'))
        
        if hasattr(self, 'tips_title'):
            self.tips_title.setText(tr('quick_tips'))
        
        if hasattr(self, 'tip_labels'):
            for tip_label, tip_key in self.tip_labels:
                tip_label.setText(tr(tip_key))
        
        if hasattr(self, 'shortcuts_label'):
            self.shortcuts_label.setText(tr('shortcuts_text'))
        
        if hasattr(self, 'version_label'):
            self.version_label.setText(tr('version_text'))
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isdir(path):
                    event.acceptProposedAction()
                    return
        event.ignore()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isdir(path):
                    git_dir = os.path.join(path, '.git')
                    if os.path.exists(git_dir):
                        self.folder_dropped.emit(path)
                        event.acceptProposedAction()
                        return
            event.ignore()

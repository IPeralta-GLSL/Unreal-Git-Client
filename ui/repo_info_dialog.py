from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QApplication, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QCursor, QColor
from ui.theme import get_current_theme
from ui.icon_manager import IconManager
from core.translations import tr
import os


class RepoInfoPopup(QFrame):
    """Popup widget to display repository information."""
    
    def __init__(self, git_manager, repo_path, parent=None):
        super().__init__(parent)
        self.git_manager = git_manager
        self.repo_path = repo_path
        self.icon_manager = IconManager()
        self.theme = get_current_theme()
        
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setup_ui()
        self.load_info()
        
    def setup_ui(self):
        theme = self.theme
        
        # Main container with shadow
        self.setStyleSheet("background: transparent;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Content frame
        content = QFrame()
        content.setObjectName("popupContent")
        content.setStyleSheet(f"""
            QFrame#popupContent {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                border-radius: 10px;
            }}
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 80))
        content.setGraphicsEffect(shadow)
        
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 14, 16, 14)
        content_layout.setSpacing(12)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        header_icon = QLabel()
        header_icon.setPixmap(self.icon_manager.get_icon("folder", size=18).pixmap(18, 18))
        header_layout.addWidget(header_icon)
        
        title = QLabel(tr('info_title'))
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        title.setStyleSheet(f"color: {theme.colors['text']};")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {theme.colors['text_secondary']};
                border: none;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {theme.colors['text']};
                background-color: {theme.colors['surface_hover']};
                border-radius: 10px;
            }}
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        content_layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {theme.colors['border']};")
        content_layout.addWidget(separator)
        
        # Info rows
        self.path_row = self._create_info_row("folder", tr('path'), "")
        content_layout.addLayout(self.path_row['layout'])
        
        self.branch_row = self._create_info_row("git-branch", tr('current_branch_info'), "")
        content_layout.addLayout(self.branch_row['layout'])
        
        self.remote_row = self._create_info_row("globe", tr('remote'), "")
        content_layout.addLayout(self.remote_row['layout'])
        
        self.commit_row = self._create_info_row("git-commit", tr('last_commit'), "")
        content_layout.addLayout(self.commit_row['layout'])
        
        # Footer with copy button
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 4, 0, 0)
        
        copy_btn = QPushButton(tr('copy_path'))
        copy_btn.setIcon(self.icon_manager.get_icon("copy", size=12))
        copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {theme.colors['primary']};
                border: none;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['primary']}20;
                border-radius: 4px;
            }}
        """)
        copy_btn.clicked.connect(self.copy_path)
        footer_layout.addWidget(copy_btn)
        
        footer_layout.addStretch()
        content_layout.addLayout(footer_layout)
        
        main_layout.addWidget(content)
        
        # Set fixed width
        self.setFixedWidth(340)
    
    def _create_info_row(self, icon_name: str, label_text: str, value_text: str) -> dict:
        """Create an info row with icon, label, and value."""
        theme = self.theme
        
        row_layout = QHBoxLayout()
        row_layout.setSpacing(8)
        row_layout.setContentsMargins(0, 0, 0, 0)
        
        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(self.icon_manager.get_icon(icon_name, size=14).pixmap(14, 14))
        icon_label.setFixedWidth(18)
        row_layout.addWidget(icon_label)
        
        # Label
        label = QLabel(f"{label_text}:")
        label.setStyleSheet(f"color: {theme.colors['text_secondary']}; font-size: 11px;")
        label.setFixedWidth(70)
        row_layout.addWidget(label)
        
        # Value
        value = QLabel(value_text)
        value.setStyleSheet(f"color: {theme.colors['text']}; font-size: 11px;")
        value.setWordWrap(True)
        value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        row_layout.addWidget(value, 1)
        
        return {'layout': row_layout, 'value': value}
    
    def load_info(self):
        """Load repository information."""
        if not self.repo_path:
            return
            
        info = self.git_manager.get_repository_info()
        
        # Update path - show only last part
        path_display = os.path.basename(self.repo_path) or self.repo_path
        self.path_row['value'].setText(path_display)
        self.path_row['value'].setToolTip(self.repo_path)
        
        # Update branch
        branch = info.get('branch', 'N/A')
        self.branch_row['value'].setText(branch)
        
        # Update remote
        remote = info.get('remote', 'N/A')
        if remote and remote != 'N/A':
            display_remote = remote if len(remote) < 35 else remote[:32] + "..."
            self.remote_row['value'].setText(display_remote)
            self.remote_row['value'].setToolTip(remote)
        else:
            self.remote_row['value'].setText('N/A')
        
        # Update last commit
        last_commit = info.get('last_commit', 'N/A')
        if last_commit and last_commit != 'N/A':
            display_commit = last_commit if len(last_commit) < 40 else last_commit[:37] + "..."
            self.commit_row['value'].setText(display_commit)
            self.commit_row['value'].setToolTip(last_commit)
        else:
            self.commit_row['value'].setText('N/A')
    
    def copy_path(self):
        """Copy repository path to clipboard."""
        if self.repo_path:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.repo_path)
            # Brief visual feedback
            self.path_row['value'].setText("✓ " + tr('copied') if tr('copied') != 'copied' else "✓ Copied!")
            QTimer.singleShot(1000, lambda: self.path_row['value'].setText(os.path.basename(self.repo_path)))
    
    def show_at(self, global_pos: QPoint):
        """Show popup at specified position, adjusting to stay on screen."""
        self.adjustSize()
        
        # Get screen geometry
        screen = QApplication.screenAt(global_pos)
        if screen:
            screen_rect = screen.availableGeometry()
        else:
            screen_rect = QApplication.primaryScreen().availableGeometry()
        
        # Adjust position to keep popup on screen
        x = global_pos.x() - self.width() // 2
        y = global_pos.y() + 10
        
        # Keep within screen bounds
        if x + self.width() > screen_rect.right():
            x = screen_rect.right() - self.width() - 10
        if x < screen_rect.left():
            x = screen_rect.left() + 10
        if y + self.height() > screen_rect.bottom():
            y = global_pos.y() - self.height() - 10
        
        self.move(x, y)
        self.show()


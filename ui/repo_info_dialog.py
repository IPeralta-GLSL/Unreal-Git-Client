from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QWidget, QGridLayout,
                             QSizePolicy, QApplication)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QCursor
from ui.theme import get_current_theme
from ui.icon_manager import IconManager
from core.translations import tr
import os


class RepoInfoDialog(QDialog):
    """Dialog to display repository information."""
    
    def __init__(self, git_manager, repo_path, parent=None):
        super().__init__(parent)
        self.git_manager = git_manager
        self.repo_path = repo_path
        self.icon_manager = IconManager()
        self.theme = get_current_theme()
        
        self.setWindowTitle(tr('info_title'))
        self.setMinimumSize(450, 280)
        self.setMaximumSize(550, 350)
        self.setup_ui()
        self.load_info()
        
    def setup_ui(self):
        theme = self.theme
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme.colors['background']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ===== HEADER =====
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['surface']};
                border-bottom: 1px solid {theme.colors['border']};
            }}
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(10)
        
        header_icon = QLabel()
        header_icon.setPixmap(self.icon_manager.get_icon("folder", size=20).pixmap(20, 20))
        header_layout.addWidget(header_icon)
        
        title = QLabel(tr('info_title'))
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        title.setStyleSheet(f"color: {theme.colors['text']};")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        layout.addWidget(header_frame)
        
        # ===== CONTENT =====
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)
        
        # Info frame
        info_frame = QFrame()
        info_frame.setObjectName("infoFrame")
        info_frame.setStyleSheet(f"""
            QFrame#infoFrame {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                border-radius: 8px;
            }}
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(16, 14, 16, 14)
        info_layout.setSpacing(14)
        
        # Repository path
        self.path_row = self._create_info_row("folder", tr('path'), "")
        info_layout.addLayout(self.path_row['layout'])
        
        # Current branch
        self.branch_row = self._create_info_row("git-branch", tr('current_branch_info'), "")
        info_layout.addLayout(self.branch_row['layout'])
        
        # Remote URL
        self.remote_row = self._create_info_row("globe", tr('remote'), "")
        info_layout.addLayout(self.remote_row['layout'])
        
        # Last commit
        self.commit_row = self._create_info_row("git-commit", tr('last_commit'), "")
        info_layout.addLayout(self.commit_row['layout'])
        
        content_layout.addWidget(info_frame)
        content_layout.addStretch()
        
        layout.addWidget(content, 1)
        
        # ===== FOOTER =====
        footer_frame = QFrame()
        footer_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['surface']};
                border-top: 1px solid {theme.colors['border']};
            }}
        """)
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(16, 10, 16, 10)
        footer_layout.setSpacing(8)
        
        # Copy path button
        copy_btn = QPushButton(tr('copy_path'))
        copy_btn.setIcon(self.icon_manager.get_icon("copy", size=14))
        copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        copy_btn.setStyleSheet(self._get_secondary_button_style())
        copy_btn.clicked.connect(self.copy_path)
        footer_layout.addWidget(copy_btn)
        
        # Open folder button
        open_btn = QPushButton(tr('open_folder'))
        open_btn.setIcon(self.icon_manager.get_icon("folder-open", size=14))
        open_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        open_btn.setStyleSheet(self._get_secondary_button_style())
        open_btn.clicked.connect(self.open_folder)
        footer_layout.addWidget(open_btn)
        
        footer_layout.addStretch()
        
        # Close button
        close_btn = QPushButton(tr('close'))
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setStyleSheet(self._get_primary_button_style())
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        
        layout.addWidget(footer_frame)
    
    def _create_info_row(self, icon_name: str, label_text: str, value_text: str) -> dict:
        """Create an info row with icon, label, and value."""
        theme = self.theme
        
        row_layout = QHBoxLayout()
        row_layout.setSpacing(8)
        
        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(self.icon_manager.get_icon(icon_name, size=16).pixmap(16, 16))
        icon_label.setFixedWidth(20)
        row_layout.addWidget(icon_label)
        
        # Label
        label = QLabel(f"{label_text}:")
        label.setStyleSheet(f"color: {theme.colors['text_secondary']}; font-size: 12px; font-weight: 500;")
        label.setFixedWidth(100)
        row_layout.addWidget(label)
        
        # Value
        value = QLabel(value_text)
        value.setStyleSheet(f"color: {theme.colors['text']}; font-size: 12px;")
        value.setWordWrap(True)
        value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        row_layout.addWidget(value, 1)
        
        return {'layout': row_layout, 'value': value}
    
    def load_info(self):
        """Load repository information."""
        if not self.repo_path:
            return
            
        info = self.git_manager.get_repository_info()
        
        # Update path
        self.path_row['value'].setText(self.repo_path)
        self.path_row['value'].setToolTip(self.repo_path)
        
        # Update branch
        branch = info.get('branch', 'N/A')
        self.branch_row['value'].setText(branch)
        
        # Update remote
        remote = info.get('remote', 'N/A')
        if remote and remote != 'N/A':
            # Truncate long URLs
            display_remote = remote if len(remote) < 45 else remote[:42] + "..."
            self.remote_row['value'].setText(display_remote)
            self.remote_row['value'].setToolTip(remote)
        else:
            self.remote_row['value'].setText('N/A')
        
        # Update last commit
        last_commit = info.get('last_commit', 'N/A')
        if last_commit and last_commit != 'N/A':
            # Truncate long commit messages
            display_commit = last_commit if len(last_commit) < 50 else last_commit[:47] + "..."
            self.commit_row['value'].setText(display_commit)
            self.commit_row['value'].setToolTip(last_commit)
        else:
            self.commit_row['value'].setText('N/A')
    
    def copy_path(self):
        """Copy repository path to clipboard."""
        if self.repo_path:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.repo_path)
    
    def open_folder(self):
        """Open repository folder in file explorer."""
        if self.repo_path and os.path.exists(self.repo_path):
            import subprocess
            import platform
            if platform.system() == 'Windows':
                subprocess.Popen(['explorer', self.repo_path])
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', self.repo_path])
            else:
                subprocess.Popen(['xdg-open', self.repo_path])
    
    def _get_primary_button_style(self) -> str:
        """Get style for primary buttons."""
        theme = self.theme
        return f"""
            QPushButton {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['text_inverse']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {theme.colors['primary_pressed']};
            }}
        """
    
    def _get_secondary_button_style(self) -> str:
        """Get style for secondary buttons."""
        theme = self.theme
        return f"""
            QPushButton {{
                background-color: {theme.colors['surface']};
                color: {theme.colors['text']};
                border: 1px solid {theme.colors['border']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['surface_hover']};
                border-color: {theme.colors['text_secondary']};
            }}
            QPushButton:pressed {{
                background-color: {theme.colors['background']};
            }}
        """

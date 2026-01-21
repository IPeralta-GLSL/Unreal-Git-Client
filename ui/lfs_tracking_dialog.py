from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QPushButton, QLabel, QLineEdit, QMessageBox, QWidget,
                             QListWidgetItem, QFrame, QGridLayout, QScrollArea)
from PyQt6.QtCore import Qt, QPoint, QSize
from PyQt6.QtGui import QFont, QCursor
from ui.theme import get_current_theme
from ui.icon_manager import IconManager
from core.translations import tr
import os

class LFSTrackingDialog(QDialog):
    def __init__(self, git_manager, plugin_manager, parent=None, suggested_files=None):
        super().__init__(parent)
        self.git_manager = git_manager
        self.plugin_manager = plugin_manager
        self.suggested_files = suggested_files or []
        self.icon_manager = IconManager()
        self.drag_position = QPoint()
        
        # Frameless window setup
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(700, 500)
        
        self.setup_ui()
        self.load_patterns()
        self.load_suggestions()
        
    def setup_ui(self):
        theme = get_current_theme()
        
        # Main container with border and background
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.container = QFrame()
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['background']};
                border: 1px solid {theme.colors['border']};
                border-radius: 10px;
            }}
        """)
        self.main_layout.addWidget(self.container)
        
        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Title Bar
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(40)
        self.title_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['surface']};
                border-bottom: 1px solid {theme.colors['border']};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
        """)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)
        
        title_label = QLabel(tr('lfs_tracking_title'))
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("border: none; background: transparent;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        close_btn = QPushButton()
        close_btn.setIcon(self.icon_manager.get_icon("x-square", size=16))
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 15px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['danger']};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        title_layout.addWidget(close_btn)
        
        self.content_layout.addWidget(self.title_bar)
        
        # Main Content Area
        content_area = QWidget()
        content_area.setStyleSheet("background: transparent; border: none;")
        main_grid = QGridLayout(content_area)
        main_grid.setContentsMargins(20, 20, 20, 20)
        main_grid.setSpacing(20)
        
        # Left Column: Tracked Patterns
        left_col = QVBoxLayout()
        left_col.setSpacing(10)
        
        tracked_label = QLabel(tr('lfs_tracking'))
        tracked_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        left_col.addWidget(tracked_label)
        
        self.patterns_list = QListWidget()
        self.patterns_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                border-radius: 5px;
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 6px;
                border-bottom: 1px solid {theme.colors['border']};
                border-radius: 3px;
            }}
            QListWidget::item:selected {{
                background-color: {theme.colors['surface_selected']};
            }}
        """)
        left_col.addWidget(self.patterns_list)
        
        main_grid.addLayout(left_col, 0, 0)
        
        # Right Column: Add & Suggestions
        right_col = QVBoxLayout()
        right_col.setSpacing(15)
        
        # Add Section
        add_group = QVBoxLayout()
        add_group.setSpacing(8)
        add_label = QLabel(tr('lfs_tracking_info'))
        add_label.setWordWrap(True)
        add_label.setStyleSheet(f"color: {theme.colors['text_secondary']}; font-size: 11px;")
        add_group.addWidget(add_label)
        
        input_row = QHBoxLayout()
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("*.ext")
        self.pattern_input.setFixedHeight(32)
        self.pattern_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                border-radius: 5px;
                padding: 0 10px;
                color: {theme.colors['text']};
            }}
            QLineEdit:focus {{
                border-color: {theme.colors['primary']};
            }}
        """)
        input_row.addWidget(self.pattern_input)
        
        self.add_btn = QPushButton(tr('add'))
        self.add_btn.setFixedHeight(32)
        self.add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['text_inverse']};
                border: none;
                border-radius: 5px;
                padding: 0 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['primary_hover']};
            }}
        """)
        self.add_btn.clicked.connect(self.add_pattern)
        input_row.addWidget(self.add_btn)
        
        add_group.addLayout(input_row)
        right_col.addLayout(add_group)
        
        # Suggestions Section
        suggestions_header = QHBoxLayout()
        suggestions_label = QLabel(tr('suggested_patterns'))
        suggestions_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        suggestions_header.addWidget(suggestions_label)
        
        suggestions_header.addStretch()
        
        self.add_all_btn = QPushButton(tr('add_all_detected'))
        self.add_all_btn.setToolTip(tr('add_all_detected_tooltip'))
        self.add_all_btn.setFixedHeight(24)
        self.add_all_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors['surface_hover']};
                color: {theme.colors['primary']};
                border: 1px solid {theme.colors['primary']};
                border-radius: 4px;
                padding: 0 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['text_inverse']};
            }}
        """)
        self.add_all_btn.clicked.connect(self.add_all_detected_files)
        self.add_all_btn.setVisible(False) # Hidden by default, shown if there are suggestions
        suggestions_header.addWidget(self.add_all_btn)
        
        right_col.addLayout(suggestions_header)
        
        self.suggestions_list = QListWidget()
        self.suggestions_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                border-radius: 5px;
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 6px;
                border-bottom: 1px solid {theme.colors['border']};
                border-radius: 3px;
            }}
            QListWidget::item:hover {{
                background-color: {theme.colors['surface_hover']};
            }}
        """)
        self.suggestions_list.itemDoubleClicked.connect(self.add_suggestion_from_list)
        right_col.addWidget(self.suggestions_list)
        
        main_grid.addLayout(right_col, 0, 1)
        
        # Set column stretch
        main_grid.setColumnStretch(0, 1)
        main_grid.setColumnStretch(1, 1)
        
        self.content_layout.addWidget(content_area)
        
    def load_patterns(self):
        self.patterns_list.clear()
        patterns = self.git_manager.get_lfs_tracked_patterns()
        for pattern in patterns:
            item = QListWidgetItem(pattern)
            item.setIcon(self.icon_manager.get_icon("check-circle", size=14, color=get_current_theme().colors['success']))
            self.patterns_list.addItem(item)
            
    def load_suggestions(self):
        self.suggestions_list.clear()
        
        theme = get_current_theme()
        current_patterns = self.git_manager.get_lfs_tracked_patterns()
        # Normalize patterns for comparison (case insensitive)
        norm_patterns = {p.lower() for p in current_patterns}
        
        has_large_files = False
        
        # Add specific file suggestions first (high priority)
        for file_path in self.suggested_files:
            # Check if extension is already tracked
            ext = "*" + os.path.splitext(file_path)[1]
            
            # Check if file or extension is tracked (case insensitive)
            if (ext.lower() in norm_patterns or 
                file_path.lower() in norm_patterns):
                continue
                
            has_large_files = True
            item = QListWidgetItem(file_path)
            item.setIcon(self.icon_manager.get_icon("warning", size=14, color=theme.colors['warning']))
            item.setToolTip(f"Large file detected. Double click to track.")
            self.suggestions_list.addItem(item)

        self.add_all_btn.setVisible(has_large_files)

        if not self.plugin_manager:
            return
            
        suggestions = self.plugin_manager.get_all_lfs_patterns()
        
        for pattern in suggestions:
            if pattern.lower() in norm_patterns:
                continue
                
            item = QListWidgetItem(pattern)
            item.setIcon(self.icon_manager.get_icon("plus", size=14, color=theme.colors['text_secondary']))
            item.setToolTip(f"Double click to track {pattern}")
            self.suggestions_list.addItem(item)
            
    def add_pattern(self):
        pattern = self.pattern_input.text().strip()
        if not pattern:
            return
        self.track_pattern(pattern)
        self.pattern_input.clear()
        
    def add_suggestion_from_list(self, item):
        self.track_pattern(item.text())
        
    def add_all_detected_files(self):
        current_patterns = self.git_manager.get_lfs_tracked_patterns()
        norm_patterns = {p.lower() for p in current_patterns}
        files_to_add = []
        
        for file_path in self.suggested_files:
            ext = "*" + os.path.splitext(file_path)[1]
            if (ext.lower() not in norm_patterns and 
                file_path.lower() not in norm_patterns):
                files_to_add.append(file_path)
        
        if files_to_add:
            success, message = self.git_manager.lfs_track_files(files_to_add)
            if success:
                self.load_patterns()
                self.load_suggestions()
                QMessageBox.information(self, tr('success'), tr('large_files_tracked'))
            else:
                QMessageBox.warning(self, tr('error'), message)

    def track_pattern(self, pattern):
        success, message = self.git_manager.lfs_track_files([pattern])
        if success:
            self.load_patterns()
            self.load_suggestions()
        else:
            QMessageBox.warning(self, tr('error'), message)

    # Window Dragging Logic
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.title_bar.geometry().contains(event.pos()):
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            if not self.drag_position.isNull():
                self.move(event.globalPosition().toPoint() - self.drag_position)
                event.accept()
                
    def mouseReleaseEvent(self, event):
        self.drag_position = QPoint()


class LFSLocksDialog(QDialog):
    def __init__(self, git_manager, parent=None):
        super().__init__(parent)
        self.git_manager = git_manager
        self.icon_manager = IconManager()
        self.drag_position = QPoint()
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(600, 400)
        
        self.setup_ui()
        self.load_locks()
        
    def setup_ui(self):
        theme = get_current_theme()
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.container = QFrame()
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['background']};
                border: 1px solid {theme.colors['border']};
                border-radius: 10px;
            }}
        """)
        self.main_layout.addWidget(self.container)
        
        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(40)
        self.title_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['surface']};
                border-bottom: 1px solid {theme.colors['border']};
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }}
        """)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)
        
        title_label = QLabel(tr('lfs_locks'))
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_label.setStyleSheet("border: none; background: transparent;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        close_btn = QPushButton()
        close_btn.setIcon(self.icon_manager.get_icon("x-square", size=16))
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 15px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['danger']};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        title_layout.addWidget(close_btn)
        
        self.content_layout.addWidget(self.title_bar)
        
        content_area = QWidget()
        content_area.setStyleSheet("background: transparent; border: none;")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(10)
        
        self.locks_list = QListWidget()
        self.locks_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                border-radius: 5px;
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {theme.colors['border']};
            }}
            QListWidget::item:selected {{
                background-color: {theme.colors['surface_selected']};
            }}
        """)
        content_layout.addWidget(self.locks_list)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.unlock_btn = QPushButton(tr('unlock'))
        self.unlock_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.unlock_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['text_inverse']};
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['primary_hover']};
            }}
        """)
        self.unlock_btn.clicked.connect(self.unlock_selected)
        btn_layout.addWidget(self.unlock_btn)
        
        content_layout.addLayout(btn_layout)
        
        self.content_layout.addWidget(content_area)
        
    def load_locks(self):
        self.locks_list.clear()
        locks = self.git_manager.get_lfs_locks()
        
        if not locks:
            item = QListWidgetItem(tr('no_locks'))
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.locks_list.addItem(item)
            self.unlock_btn.setEnabled(False)
            return
            
        self.unlock_btn.setEnabled(True)
        for lock in locks:
            file_path = lock.get('path', 'Unknown')
            owner = lock.get('owner', {}).get('name', 'Unknown')
            item = QListWidgetItem(f"{file_path} - {tr('locked_by')}: {owner}")
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            item.setIcon(self.icon_manager.get_icon("lock", size=16))
            self.locks_list.addItem(item)
    
    def unlock_selected(self):
        item = self.locks_list.currentItem()
        if not item:
            return
            
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if not file_path:
            return
            
        success, message = self.git_manager.lfs_unlock_file(file_path)
        if success:
            self.load_locks()
        else:
            QMessageBox.warning(self, tr('error'), message)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.title_bar.geometry().contains(event.pos()):
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            if not self.drag_position.isNull():
                self.move(event.globalPosition().toPoint() - self.drag_position)
                event.accept()
                
    def mouseReleaseEvent(self, event):
        self.drag_position = QPoint()

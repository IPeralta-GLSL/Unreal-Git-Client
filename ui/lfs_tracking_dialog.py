from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QPushButton, QLabel, QLineEdit, QMessageBox, QWidget,
                             QListWidgetItem)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ui.theme import get_current_theme
from ui.icon_manager import IconManager
from core.translations import tr

class LFSTrackingDialog(QDialog):
    def __init__(self, git_manager, plugin_manager, parent=None):
        super().__init__(parent)
        self.git_manager = git_manager
        self.plugin_manager = plugin_manager
        self.icon_manager = IconManager()
        self.setWindowTitle(tr('lfs_tracking'))
        self.resize(500, 600)
        self.setup_ui()
        self.load_patterns()
        
    def setup_ui(self):
        theme = get_current_theme()
        self.setStyleSheet(f"background-color: {theme.colors['background']}; color: {theme.colors['text']};")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_label = QLabel(tr('lfs_tracking_title'))
        header_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(header_label)
        
        desc_label = QLabel(tr('lfs_tracking_info'))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {theme.colors['text_secondary']};")
        layout.addWidget(desc_label)
        
        # Current Patterns List
        self.patterns_list = QListWidget()
        self.patterns_list.setStyleSheet(f"""
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
        """)
        layout.addWidget(self.patterns_list)
        
        # Add Pattern Section
        add_layout = QHBoxLayout()
        
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("*.psd")
        self.pattern_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                border-radius: 5px;
                padding: 8px;
                color: {theme.colors['text']};
            }}
            QLineEdit:focus {{
                border-color: {theme.colors['primary']};
            }}
        """)
        add_layout.addWidget(self.pattern_input)
        
        self.add_btn = QPushButton(tr('add'))
        self.add_btn.setIcon(self.icon_manager.get_icon("plus-circle", size=16))
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['text_inverse']};
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['primary_hover']};
            }}
        """)
        self.add_btn.clicked.connect(self.add_pattern)
        add_layout.addWidget(self.add_btn)
        
        layout.addLayout(add_layout)
        
        # Suggestions from plugins
        if self.plugin_manager:
            suggestions_label = QLabel(tr('suggested_patterns'))
            suggestions_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            suggestions_label.setStyleSheet(f"margin-top: 10px;")
            layout.addWidget(suggestions_label)
            
            suggestions_layout = QVBoxLayout()
            suggestions = self.plugin_manager.get_all_lfs_patterns()
            
            # Deduplicate and filter existing
            current_patterns = self.git_manager.get_lfs_tracked_patterns()
            
            added_suggestions = 0
            for pattern in suggestions:
                if pattern in current_patterns:
                    continue
                    
                added_suggestions += 1
                btn = QPushButton(f"Track {pattern}")
                btn.setStyleSheet(f"""
                    QPushButton {{
                        text-align: left;
                        background-color: {theme.colors['surface']};
                        border: 1px solid {theme.colors['border']};
                        border-radius: 5px;
                        padding: 8px;
                    }}
                    QPushButton:hover {{
                        border-color: {theme.colors['primary']};
                    }}
                """)
                btn.clicked.connect(lambda checked, p=pattern: self.add_suggested_pattern(p))
                suggestions_layout.addWidget(btn)
            
            if added_suggestions == 0:
                no_suggestions = QLabel(tr('no_suggestions'))
                no_suggestions.setStyleSheet(f"color: {theme.colors['text_secondary']}; font-style: italic;")
                suggestions_layout.addWidget(no_suggestions)
                
            layout.addLayout(suggestions_layout)
            
        # Close button
        close_btn = QPushButton(tr('close'))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                border-radius: 5px;
                padding: 8px 15px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['surface_hover']};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignRight)
        
    def load_patterns(self):
        self.patterns_list.clear()
        patterns = self.git_manager.get_lfs_tracked_patterns()
        
        for pattern in patterns:
            item = QListWidgetItem(pattern)
            item.setIcon(self.icon_manager.get_icon("file-code", size=16))
            self.patterns_list.addItem(item)
            
    def add_pattern(self):
        pattern = self.pattern_input.text().strip()
        if not pattern:
            return
            
        self.add_suggested_pattern(pattern)
        self.pattern_input.clear()
        
    def add_suggested_pattern(self, pattern):
        success, message = self.git_manager.lfs_track_files([pattern])
        if success:
            self.load_patterns()
            # Refresh suggestions if needed, but simple reload is fine
        else:
            QMessageBox.warning(self, tr('error'), message)

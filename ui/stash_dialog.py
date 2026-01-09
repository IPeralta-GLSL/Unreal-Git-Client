from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QListWidget, QListWidgetItem,
                             QFrame, QCheckBox, QMessageBox, QTextEdit, QSplitter,
                             QWidget, QSizePolicy)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QCursor
from ui.theme import get_current_theme
from ui.icon_manager import IconManager
from core.translations import tr


class StashDialog(QDialog):
    def __init__(self, git_manager, parent=None):
        super().__init__(parent)
        self.git_manager = git_manager
        self.icon_manager = IconManager()
        self.theme = get_current_theme()
        
        self.setWindowTitle(tr('stash'))
        self.setMinimumSize(600, 500)
        self.setup_ui()
        self.load_stashes()
        
    def setup_ui(self):
        theme = self.theme
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme.colors['background']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Title
        title = QLabel(tr('stash_changes'))
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {theme.colors['text']};")
        layout.addWidget(title)
        
        # New stash section
        new_stash_frame = QFrame()
        new_stash_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                border-radius: 8px;
            }}
        """)
        new_stash_layout = QVBoxLayout(new_stash_frame)
        new_stash_layout.setContentsMargins(12, 12, 12, 12)
        new_stash_layout.setSpacing(8)
        
        # Message input
        msg_label = QLabel(tr('stash_message'))
        msg_label.setStyleSheet(f"color: {theme.colors['text_secondary']}; font-size: 12px; border: none;")
        new_stash_layout.addWidget(msg_label)
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText(tr('stash_message_placeholder'))
        self.message_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {theme.colors['input_background']};
                color: {theme.colors['text']};
                border: 1px solid {theme.colors['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {theme.colors['primary']};
            }}
        """)
        new_stash_layout.addWidget(self.message_input)
        
        # Options row
        options_row = QHBoxLayout()
        options_row.setSpacing(12)
        
        self.include_untracked = QCheckBox(tr('include_untracked'))
        self.include_untracked.setChecked(True)
        self.include_untracked.setStyleSheet(f"""
            QCheckBox {{
                color: {theme.colors['text']};
                font-size: 12px;
                border: none;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
        """)
        options_row.addWidget(self.include_untracked)
        options_row.addStretch()
        
        self.save_stash_btn = QPushButton(tr('stash_save'))
        self.save_stash_btn.setIcon(self.icon_manager.get_icon("download", size=16))
        self.save_stash_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_stash_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['text_inverse']};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['primary_hover']};
            }}
        """)
        self.save_stash_btn.clicked.connect(self.save_stash)
        options_row.addWidget(self.save_stash_btn)
        
        new_stash_layout.addLayout(options_row)
        layout.addWidget(new_stash_frame)
        
        # Stash list section
        list_label = QLabel(tr('stash'))
        list_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        list_label.setStyleSheet(f"color: {theme.colors['text']};")
        layout.addWidget(list_label)
        
        # Splitter for list and preview
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Stash list
        self.stash_list = QListWidget()
        self.stash_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                border-radius: 8px;
                padding: 4px;
            }}
            QListWidget::item {{
                background-color: transparent;
                color: {theme.colors['text']};
                padding: 8px;
                border-radius: 4px;
                margin: 2px;
            }}
            QListWidget::item:selected {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['text_inverse']};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {theme.colors['surface_hover']};
            }}
        """)
        self.stash_list.itemSelectionChanged.connect(self.on_stash_selected)
        splitter.addWidget(self.stash_list)
        
        # Preview area
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setFont(QFont("Consolas", 10))
        self.preview.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme.colors['surface']};
                color: {theme.colors['text']};
                border: 1px solid {theme.colors['border']};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        self.preview.setPlaceholderText(tr('stash_show'))
        splitter.addWidget(self.preview)
        
        splitter.setSizes([200, 150])
        layout.addWidget(splitter, 1)
        
        # Action buttons
        actions_row = QHBoxLayout()
        actions_row.setSpacing(8)
        
        self.apply_btn = QPushButton(tr('stash_apply'))
        self.apply_btn.setIcon(self.icon_manager.get_icon("check", size=16))
        self.apply_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.apply_btn.clicked.connect(self.apply_stash)
        self.style_action_btn(self.apply_btn, "normal")
        actions_row.addWidget(self.apply_btn)
        
        self.pop_btn = QPushButton(tr('stash_pop'))
        self.pop_btn.setIcon(self.icon_manager.get_icon("check-circle", size=16))
        self.pop_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.pop_btn.clicked.connect(self.pop_stash)
        self.style_action_btn(self.pop_btn, "success")
        actions_row.addWidget(self.pop_btn)
        
        self.drop_btn = QPushButton(tr('stash_drop'))
        self.drop_btn.setIcon(self.icon_manager.get_icon("trash", size=16))
        self.drop_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.drop_btn.clicked.connect(self.drop_stash)
        self.style_action_btn(self.drop_btn, "danger")
        actions_row.addWidget(self.drop_btn)
        
        actions_row.addStretch()
        
        self.clear_btn = QPushButton(tr('stash_clear'))
        self.clear_btn.setIcon(self.icon_manager.get_icon("x-circle", size=16))
        self.clear_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clear_btn.clicked.connect(self.clear_stashes)
        self.style_action_btn(self.clear_btn, "danger")
        actions_row.addWidget(self.clear_btn)
        
        layout.addLayout(actions_row)
        
        # Close button
        close_row = QHBoxLayout()
        close_row.addStretch()
        close_btn = QPushButton(tr('close'))
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors['surface']};
                color: {theme.colors['text']};
                border: 1px solid {theme.colors['border']};
                border-radius: 4px;
                padding: 8px 24px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['surface_hover']};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        close_row.addWidget(close_btn)
        layout.addLayout(close_row)
        
        self.update_buttons_state()
        
    def style_action_btn(self, btn, style_type):
        theme = self.theme
        if style_type == "success":
            bg = theme.colors['success']
            bg_hover = theme.colors.get('success_hover', '#45a049')
        elif style_type == "danger":
            bg = theme.colors['danger']
            bg_hover = theme.colors.get('danger_hover', '#c0392b')
        else:
            bg = theme.colors['surface']
            bg_hover = theme.colors['surface_hover']
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {theme.colors['text_inverse'] if style_type != "normal" else theme.colors['text']};
                border: 1px solid {theme.colors['border']};
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {bg_hover};
            }}
            QPushButton:disabled {{
                background-color: {theme.colors['surface']};
                color: {theme.colors['text_secondary']};
            }}
        """)
        
    def load_stashes(self):
        self.stash_list.clear()
        stashes = self.git_manager.stash_list()
        
        if not stashes:
            item = QListWidgetItem(tr('stash_empty'))
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.stash_list.addItem(item)
        else:
            for stash in stashes:
                item = QListWidgetItem(f"{stash['index']}: {stash['message']}")
                item.setData(Qt.ItemDataRole.UserRole, stash['index'])
                item.setToolTip(stash.get('date', ''))
                self.stash_list.addItem(item)
        
        self.update_buttons_state()
        self.preview.clear()
        
    def update_buttons_state(self):
        has_selection = len(self.stash_list.selectedItems()) > 0
        has_stashes = self.stash_list.count() > 0 and self.stash_list.item(0).flags() != Qt.ItemFlag.NoItemFlags
        
        self.apply_btn.setEnabled(has_selection)
        self.pop_btn.setEnabled(has_selection)
        self.drop_btn.setEnabled(has_selection)
        self.clear_btn.setEnabled(has_stashes)
        
    def on_stash_selected(self):
        self.update_buttons_state()
        items = self.stash_list.selectedItems()
        if items:
            stash_index = items[0].data(Qt.ItemDataRole.UserRole)
            if stash_index:
                diff = self.git_manager.stash_show(stash_index)
                self.preview.setPlainText(diff)
        else:
            self.preview.clear()
            
    def get_selected_stash(self):
        items = self.stash_list.selectedItems()
        if items:
            return items[0].data(Qt.ItemDataRole.UserRole)
        return None
        
    def save_stash(self):
        message = self.message_input.text().strip() or None
        include_untracked = self.include_untracked.isChecked()
        
        success, msg = self.git_manager.stash_save(message, include_untracked)
        if success:
            QMessageBox.information(self, tr('success'), tr('stash_saved'))
            self.message_input.clear()
            self.load_stashes()
        else:
            QMessageBox.warning(self, tr('error'), msg)
            
    def apply_stash(self):
        stash_index = self.get_selected_stash()
        if stash_index:
            success, msg = self.git_manager.stash_apply(stash_index)
            if success:
                QMessageBox.information(self, tr('success'), tr('stash_applied'))
            else:
                QMessageBox.warning(self, tr('error'), msg)
                
    def pop_stash(self):
        stash_index = self.get_selected_stash()
        if stash_index:
            success, msg = self.git_manager.stash_pop(stash_index)
            if success:
                QMessageBox.information(self, tr('success'), tr('stash_popped'))
                self.load_stashes()
            else:
                QMessageBox.warning(self, tr('error'), msg)
                
    def drop_stash(self):
        stash_index = self.get_selected_stash()
        if stash_index:
            reply = QMessageBox.question(
                self, tr('confirm'), 
                tr('confirm_stash_drop', stash=stash_index),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                success, msg = self.git_manager.stash_drop(stash_index)
                if success:
                    QMessageBox.information(self, tr('success'), tr('stash_dropped'))
                    self.load_stashes()
                else:
                    QMessageBox.warning(self, tr('error'), msg)
                    
    def clear_stashes(self):
        reply = QMessageBox.question(
            self, tr('confirm'), 
            tr('confirm_stash_clear'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.git_manager.stash_clear()
            if success:
                QMessageBox.information(self, tr('success'), tr('stash_cleared'))
                self.load_stashes()
            else:
                QMessageBox.warning(self, tr('error'), msg)

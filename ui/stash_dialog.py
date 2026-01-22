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
        self.setMinimumSize(650, 550)
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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header with icon and description
        header = QHBoxLayout()
        header.setSpacing(12)
        
        header_icon = QLabel()
        header_icon.setPixmap(self.icon_manager.get_icon("archive", size=32).pixmap(32, 32))
        header.addWidget(header_icon)
        
        header_text = QVBoxLayout()
        header_text.setSpacing(2)
        
        title = QLabel(tr('stash_title'))
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {theme.colors['text']};")
        header_text.addWidget(title)
        
        subtitle = QLabel(tr('stash_description'))
        subtitle.setStyleSheet(f"color: {theme.colors['text_secondary']}; font-size: 12px;")
        subtitle.setWordWrap(True)
        header_text.addWidget(subtitle)
        
        header.addLayout(header_text, 1)
        layout.addLayout(header)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {theme.colors['border']};")
        sep.setFixedHeight(1)
        layout.addWidget(sep)
        
        # ===== GUARDAR Section =====
        save_section = QFrame()
        save_section.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                border-radius: 8px;
            }}
        """)
        save_layout = QVBoxLayout(save_section)
        save_layout.setContentsMargins(16, 12, 16, 12)
        save_layout.setSpacing(10)
        
        save_header = QHBoxLayout()
        save_icon = QLabel()
        save_icon.setPixmap(self.icon_manager.get_icon("download", size=18).pixmap(18, 18))
        save_header.addWidget(save_icon)
        save_title = QLabel(tr('stash_save_title'))
        save_title.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        save_title.setStyleSheet(f"color: {theme.colors['text']}; border: none;")
        save_header.addWidget(save_title)
        save_header.addStretch()
        save_layout.addLayout(save_header)
        
        save_desc = QLabel(tr('stash_save_desc'))
        save_desc.setStyleSheet(f"color: {theme.colors['text_secondary']}; font-size: 11px; border: none;")
        save_desc.setWordWrap(True)
        save_layout.addWidget(save_desc)
        
        # Input row
        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText(tr('stash_message_placeholder'))
        self.message_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {theme.colors['background']};
                color: {theme.colors['text']};
                border: 1px solid {theme.colors['border']};
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {theme.colors['primary']};
            }}
        """)
        input_row.addWidget(self.message_input, 1)
        
        self.save_stash_btn = QPushButton(tr('stash_save_btn'))
        self.save_stash_btn.setIcon(self.icon_manager.get_icon("archive", size=16))
        self.save_stash_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.save_stash_btn.setMinimumHeight(40)
        self.save_stash_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['text_inverse']};
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['primary_hover']};
            }}
        """)
        self.save_stash_btn.clicked.connect(self.save_stash)
        input_row.addWidget(self.save_stash_btn)
        
        save_layout.addLayout(input_row)
        
        # Options
        self.include_untracked = QCheckBox(tr('include_untracked'))
        self.include_untracked.setChecked(True)
        self.include_untracked.setStyleSheet(f"""
            QCheckBox {{
                color: {theme.colors['text_secondary']};
                font-size: 11px;
                border: none;
            }}
        """)
        save_layout.addWidget(self.include_untracked)
        
        layout.addWidget(save_section)
        
        # ===== RESTAURAR Section =====
        restore_section = QFrame()
        restore_section.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                border-radius: 8px;
            }}
        """)
        restore_layout = QVBoxLayout(restore_section)
        restore_layout.setContentsMargins(16, 12, 16, 12)
        restore_layout.setSpacing(10)
        
        restore_header = QHBoxLayout()
        restore_icon = QLabel()
        restore_icon.setPixmap(self.icon_manager.get_icon("upload", size=18).pixmap(18, 18))
        restore_header.addWidget(restore_icon)
        restore_title = QLabel(tr('stash_restore_title'))
        restore_title.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        restore_title.setStyleSheet(f"color: {theme.colors['text']}; border: none;")
        restore_header.addWidget(restore_title)
        
        self.stash_count_label = QLabel("(0)")
        self.stash_count_label.setStyleSheet(f"color: {theme.colors['text_secondary']}; font-size: 12px; border: none;")
        restore_header.addWidget(self.stash_count_label)
        
        restore_header.addStretch()
        restore_layout.addLayout(restore_header)
        
        # Stash list
        self.stash_list = QListWidget()
        self.stash_list.setMinimumHeight(120)
        self.stash_list.setMaximumHeight(180)
        self.stash_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme.colors['background']};
                border: 1px solid {theme.colors['border']};
                border-radius: 6px;
                padding: 4px;
            }}
            QListWidget::item {{
                background-color: transparent;
                color: {theme.colors['text']};
                padding: 8px 10px;
                border-radius: 4px;
                margin: 1px 0px;
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
        restore_layout.addWidget(self.stash_list)
        
        # Action buttons row
        actions_row = QHBoxLayout()
        actions_row.setSpacing(8)
        
        self.pop_btn = QPushButton(tr('stash_restore_btn'))
        self.pop_btn.setIcon(self.icon_manager.get_icon("upload", size=16))
        self.pop_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.pop_btn.setToolTip(tr('stash_pop_tooltip'))
        self.pop_btn.clicked.connect(self.pop_stash)
        self.style_action_btn(self.pop_btn, "success")
        actions_row.addWidget(self.pop_btn)
        
        self.apply_btn = QPushButton(tr('stash_apply_btn'))
        self.apply_btn.setIcon(self.icon_manager.get_icon("copy", size=16))
        self.apply_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.apply_btn.setToolTip(tr('stash_apply_tooltip'))
        self.apply_btn.clicked.connect(self.apply_stash)
        self.style_action_btn(self.apply_btn, "normal")
        actions_row.addWidget(self.apply_btn)
        
        actions_row.addStretch()
        
        self.drop_btn = QPushButton(tr('stash_delete_btn'))
        self.drop_btn.setIcon(self.icon_manager.get_icon("trash", size=16))
        self.drop_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.drop_btn.clicked.connect(self.drop_stash)
        self.style_action_btn(self.drop_btn, "danger")
        actions_row.addWidget(self.drop_btn)
        
        self.clear_btn = QPushButton(tr('stash_clear_btn'))
        self.clear_btn.setIcon(self.icon_manager.get_icon("x-circle", size=16))
        self.clear_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.clear_btn.clicked.connect(self.clear_stashes)
        self.style_action_btn(self.clear_btn, "danger")
        actions_row.addWidget(self.clear_btn)
        
        restore_layout.addLayout(actions_row)
        
        layout.addWidget(restore_section)
        
        # Preview area (collapsible feel)
        preview_header = QHBoxLayout()
        preview_icon = QLabel()
        preview_icon.setPixmap(self.icon_manager.get_icon("eye", size=14).pixmap(14, 14))
        preview_header.addWidget(preview_icon)
        preview_label = QLabel(tr('stash_preview'))
        preview_label.setStyleSheet(f"color: {theme.colors['text_secondary']}; font-size: 11px;")
        preview_header.addWidget(preview_label)
        preview_header.addStretch()
        layout.addLayout(preview_header)
        
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setFont(QFont("Cascadia Code", 10))
        self.preview.setMinimumHeight(100)
        self.preview.setMaximumHeight(150)
        self.preview.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme.colors['surface']};
                color: {theme.colors['text']};
                border: 1px solid {theme.colors['border']};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        self.preview.setPlaceholderText(tr('stash_preview_placeholder'))
        layout.addWidget(self.preview)
        
        # Close button
        close_row = QHBoxLayout()
        close_row.addStretch()
        close_btn = QPushButton(tr('close'))
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setMinimumWidth(100)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors['surface']};
                color: {theme.colors['text']};
                border: 1px solid {theme.colors['border']};
                border-radius: 6px;
                padding: 10px 24px;
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
        
        count = len(stashes) if stashes else 0
        self.stash_count_label.setText(f"({count})")
        
        if not stashes:
            item = QListWidgetItem(tr('stash_empty'))
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.stash_list.addItem(item)
        else:
            for stash in stashes:
                item = QListWidgetItem(f"📦 {stash['message']}")
                item.setData(Qt.ItemDataRole.UserRole, stash['index'])
                item.setToolTip(f"{stash['index']} - {stash.get('date', '')}")
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

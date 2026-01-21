from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QListWidget, QPushButton, QLineEdit, QMessageBox,
                             QListWidgetItem, QComboBox, QRadioButton, QButtonGroup,
                             QGroupBox, QTextEdit, QWidget, QFrame)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QColor
from ui.icon_manager import IconManager
from ui.theme import get_current_theme
from ui.style_utils import apply_primary_button, apply_danger_button, apply_default_button, get_theme
from core.translations import tr
import platform

class BranchManagerDialog(QDialog):
    def __init__(self, git_manager, parent=None):
        super().__init__(parent)
        self.git_manager = git_manager
        self.icon_manager = IconManager()
        self.drag_position = QPoint()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.init_ui()
        self.load_branches()
        
    def init_ui(self):
        theme = get_theme()
        self.setWindowTitle(tr('branch_manager'))
        self.setModal(True)
        self.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        title_bar = self.create_title_bar()
        layout.addWidget(title_bar)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(theme.spacing['lg'])
        content_layout.setContentsMargins(theme.spacing['lg'], theme.spacing['lg'], 
                                         theme.spacing['lg'], theme.spacing['lg'])
        
        current_branch_label = QLabel("Rama actual:")
        current_branch_label.setStyleSheet(f"""
            QLabel {{
                color: {theme.colors['text']};
                font-size: {theme.fonts['size_base']}px;
            }}
        """)
        content_layout.addWidget(current_branch_label)
        
        self.current_branch = QLabel()
        self.current_branch.setStyleSheet(f"""
            QLabel {{
                font-size: {theme.fonts['size_xl']}px;
                font-weight: {theme.fonts['weight_bold']};
                color: {theme.colors['primary']};
                background-color: {theme.colors['surface']};
                padding: {theme.spacing['md']}px;
                border-radius: {theme.borders['radius_md']}px;
            }}
        """)
        content_layout.addWidget(self.current_branch)
        
        list_label = QLabel("Todas las Ramas:")
        list_label.setStyleSheet(f"""
            QLabel {{
                color: {theme.colors['text']};
                font-weight: {theme.fonts['weight_bold']};
                margin-top: {theme.spacing['md']}px;
            }}
        """)
        content_layout.addWidget(list_label)
        
        self.branches_list = QListWidget()
        self.branches_list.setStyleSheet(theme.get_list_style())
        self.branches_list.itemDoubleClicked.connect(self.switch_to_branch)
        content_layout.addWidget(self.branches_list)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(theme.spacing['md'])
        
        self.new_branch_btn = QPushButton(tr('new_branch'))
        self.new_branch_btn.setIcon(self.icon_manager.get_icon("plus-circle", size=18))
        self.new_branch_btn.clicked.connect(self.create_new_branch)
        apply_primary_button(self.new_branch_btn)
        buttons_layout.addWidget(self.new_branch_btn)
        
        self.switch_btn = QPushButton(tr('switch'))
        self.switch_btn.setIcon(self.icon_manager.get_icon("arrows-clockwise", size=18))
        self.switch_btn.clicked.connect(self.switch_to_selected_branch)
        apply_default_button(self.switch_btn)
        buttons_layout.addWidget(self.switch_btn)
        
        self.delete_btn = QPushButton(tr('delete'))
        self.delete_btn.setIcon(self.icon_manager.get_icon("trash", size=18))
        self.delete_btn.clicked.connect(self.delete_selected_branch)
        apply_danger_button(self.delete_btn)
        buttons_layout.addWidget(self.delete_btn)
        
        self.merge_btn = QPushButton(tr('merge'))
        self.merge_btn.setIcon(self.icon_manager.get_icon("git-merge", size=18))
        self.merge_btn.clicked.connect(self.merge_selected_branch)
        apply_default_button(self.merge_btn)
        buttons_layout.addWidget(self.merge_btn)
        
        content_layout.addLayout(buttons_layout)
        
        close_btn = QPushButton(tr('close'))
        close_btn.clicked.connect(self.accept)
        apply_default_button(close_btn)
        content_layout.addWidget(close_btn)
        
        layout.addWidget(content_widget)
        self.setStyleSheet(theme.get_dialog_style())
    
    def create_title_bar(self):
        theme = get_current_theme()
        
        title_bar = QFrame()
        title_bar.setFixedHeight(35)
        title_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['surface']};
                border-bottom: 1px solid {theme.colors['border']};
            }}
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 0, 0)
        title_layout.setSpacing(0)
        
        title_icon = QLabel()
        title_icon.setPixmap(self.icon_manager.get_pixmap("git-branch", size=18))
        title_layout.addWidget(title_icon)
        
        title = QLabel(tr('branch_manager'))
        title.setStyleSheet(f"""
            QLabel {{
                color: {theme.colors['text']};
                font-weight: {theme.fonts['weight_bold']};
                font-size: {theme.fonts['size_md']}px;
                margin-left: {theme.spacing['xs']}px;
            }}
        """)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        close_button = QPushButton()
        close_button.setIcon(self.icon_manager.get_icon("x-square", size=14))
        close_button.setFixedSize(40, 35)
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(self.accept)
        close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 0px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['danger']};
            }}
        """)
        title_layout.addWidget(close_button)
        
        title_bar.mousePressEvent = self.title_bar_mouse_press
        
        return title_bar
    
    def title_bar_mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
        super().mouseMoveEvent(event)
        
    def load_branches(self):
        current = self.git_manager.get_current_branch()
        self.current_branch.setText(current)
        
        self.branches_list.clear()
        branches = self.git_manager.get_all_branches()
        
        theme = get_current_theme()
        
        for branch in branches:
            name = branch['name']
            item = QListWidgetItem()
            
            if branch['is_current']:
                item.setText(f"{name} (actual)")
                item.setIcon(self.icon_manager.get_icon("check", size=16))
                item.setForeground(QColor(theme.colors['success']))
            elif branch['is_remote']:
                item.setText(name)
                item.setIcon(self.icon_manager.get_icon("share-network", size=16))
                item.setForeground(QColor(theme.colors['primary']))
            else:
                item.setText(name)
                item.setIcon(self.icon_manager.get_icon("git-branch", size=16))
                item.setForeground(QColor(theme.colors['text']))
            
            item.setData(Qt.ItemDataRole.UserRole, name)
            self.branches_list.addItem(item)
            
    def create_new_branch(self):
        dialog = CreateBranchDialog(self.git_manager, self)
        if dialog.exec():
            self.load_branches()
            
    def switch_to_branch(self, item):
        branch_name = item.data(Qt.ItemDataRole.UserRole)
        self.switch_branch(branch_name)
        
    def switch_to_selected_branch(self):
        current_item = self.branches_list.currentItem()
        if current_item:
            self.switch_to_branch(current_item)
        else:
            QMessageBox.warning(self, tr('warning'), tr('select_branch_first'))
            
    def switch_branch(self, branch_name):
        reply = QMessageBox.question(
            self,
            tr('confirm'),
            tr('change_branch_question', branch=branch_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.git_manager.switch_branch(branch_name)
            if success:
                QMessageBox.information(self, tr('success'), tr('branch_switched', branch=branch_name))
                self.load_branches()
            else:
                QMessageBox.warning(self, tr('error'), f"{tr('error_change_branch')}:\n{message}")
                
    def delete_selected_branch(self):
        current_item = self.branches_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, tr('warning'), tr('select_branch_to_delete'))
            return
            
        branch_name = current_item.data(Qt.ItemDataRole.UserRole)
        
        if "actual" in current_item.text() or "current" in current_item.text().lower():
            QMessageBox.warning(self, tr('error'), tr('cannot_delete_current_branch'))
            return
            
        reply = QMessageBox.question(
            self,
            tr('confirm_delete'),
            tr('confirm_delete_branch', branch=branch_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.git_manager.delete_branch(branch_name)
            if success:
                QMessageBox.information(self, tr('success'), tr('branch_deleted', branch=branch_name))
                self.load_branches()
            else:
                QMessageBox.warning(self, tr('error'), f"{tr('error_delete_branch')}:\n{message}")
                
    def merge_selected_branch(self):
        current_item = self.branches_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, tr('warning'), tr('select_branch_to_merge'))
            return
            
        branch_name = current_item.data(Qt.ItemDataRole.UserRole)
        current = self.git_manager.get_current_branch()
        
        reply = QMessageBox.question(
            self,
            tr('confirm_merge'),
            tr('confirm_merge_question', source=branch_name, target=current),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.git_manager.merge_branch(branch_name)
            if success:
                QMessageBox.information(self, tr('success'), tr('merge_completed'))
            else:
                QMessageBox.warning(self, tr('error'), f"{tr('merge_error')}:\n{message}")

class CreateBranchDialog(QDialog):
    def __init__(self, git_manager, parent=None):
        super().__init__(parent)
        self.git_manager = git_manager
        self.icon_manager = IconManager()
        self.drag_position = QPoint()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle(tr('create_new_branch'))
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        title_bar = self.create_title_bar()
        layout.addWidget(title_bar)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        name_label = QLabel(tr('branch_name_label'))
        name_label.setStyleSheet("color: palette(window-text); font-weight: bold;")
        content_layout.addWidget(name_label)
        
        self.branch_name_input = QLineEdit()
        self.branch_name_input.setPlaceholderText("feature/new-feature")
        content_layout.addWidget(self.branch_name_input)
        
        source_group = QGroupBox(tr('create_from'))
        source_layout = QVBoxLayout()
        
        self.from_current_radio = QRadioButton(tr('current_branch'))
        self.from_current_radio.setChecked(True)
        source_layout.addWidget(self.from_current_radio)
        
        self.from_commit_radio = QRadioButton(tr('specific_commit'))
        source_layout.addWidget(self.from_commit_radio)
        
        self.commit_input = QLineEdit()
        self.commit_input.setPlaceholderText(tr('commit_hash_placeholder'))
        self.commit_input.setEnabled(False)
        source_layout.addWidget(self.commit_input)
        
        self.from_commit_radio.toggled.connect(self.commit_input.setEnabled)
        
        source_group.setLayout(source_layout)
        content_layout.addWidget(source_group)
        
        buttons_layout = QHBoxLayout()
        
        cancel_btn = QPushButton(tr('cancel'))
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton(tr('create_branch'))
        create_btn.setIcon(self.icon_manager.get_icon("check", size=18))
        create_btn.clicked.connect(self.create_branch)
        create_btn.setDefault(True)
        buttons_layout.addWidget(create_btn)
        
        content_layout.addLayout(buttons_layout)
        layout.addWidget(content_widget)
        
        self.apply_styles()
    
    def create_title_bar(self):
        theme = get_current_theme()
        
        title_bar = QFrame()
        title_bar.setFixedHeight(35)
        title_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['surface']};
                border-bottom: 1px solid {theme.colors['border']};
            }}
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 0, 0)
        title_layout.setSpacing(0)
        
        icon_label = QLabel()
        icon_label.setPixmap(self.icon_manager.get_pixmap("plus-circle", 18))
        title_layout.addWidget(icon_label)
        
        title_text = QLabel(tr('create_new_branch'))
        title_text.setStyleSheet(f"color: {theme.colors['text']}; font-weight: bold; font-size: 13px; margin-left: 5px;")
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        
        close_button = QPushButton()
        close_button.setIcon(self.icon_manager.get_icon("x-square", size=14))
        close_button.setFixedSize(40, 35)
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(self.reject)
        close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 0px;
            }}
            QPushButton:hover {{
                background-color: #e81123;
            }}
        """)
        title_layout.addWidget(close_button)
        
        title_bar.mousePressEvent = self.title_bar_mouse_press
        
        return title_bar
    
    def title_bar_mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
        super().mouseMoveEvent(event)
        
    def create_branch(self):
        branch_name = self.branch_name_input.text().strip()
        
        if not branch_name:
            QMessageBox.warning(self, tr('error'), tr('enter_branch_name'))
            return
            
        from_commit = None
        if self.from_commit_radio.isChecked():
            from_commit = self.commit_input.text().strip()
            if not from_commit:
                QMessageBox.warning(self, tr('error'), tr('enter_commit_hash'))
                return
                
        success, message = self.git_manager.create_branch(branch_name, from_commit)
        
        if success:
            QMessageBox.information(self, tr('success'), tr('branch_created_success', branch=branch_name))
            self.accept()
        else:
            QMessageBox.warning(self, tr('error'), f"{tr('error_create_branch')}:\n{message}")
            
    def apply_styles(self):
        from ui.theme import get_current_theme
        theme = get_current_theme()
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme.colors['background']};
            }}
            QLabel {{
                color: {theme.colors['text']};
            }}
            QLineEdit {{
                background-color: {theme.colors['input_bg']};
                color: {theme.colors['text']};
                border: 2px solid {theme.colors['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 2px solid {theme.colors['border_focus']};
            }}
            QLineEdit:disabled {{
                background-color: {theme.colors['surface']};
                color: {theme.colors['text_disabled']};
            }}
            QGroupBox {{
                color: {theme.colors['text']};
                border: 2px solid {theme.colors['border']};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QRadioButton {{
                color: {theme.colors['text']};
                font-size: 13px;
            }}
            QRadioButton::indicator {{
                width: 15px;
                height: 15px;
            }}
            QPushButton {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['text_inverse']};
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
                padding-left: 10px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {theme.colors['primary_pressed']};
            }}
        """)

class CommitActionsDialog(QDialog):
    def __init__(self, git_manager, commit_hash, commit_info, parent=None):
        super().__init__(parent)
        self.git_manager = git_manager
        self.commit_hash = commit_hash
        self.commit_info = commit_info
        self.icon_manager = IconManager()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle(tr('commit_actions'))
        self.setModal(True)
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(self.icon_manager.get_pixmap("git-commit", 24))
        title_layout.addWidget(icon_label)
        
        title_text = QLabel(tr('commit_actions'))
        title_text.setStyleSheet("font-size: 18px; font-weight: bold; color: palette(bright-text);")
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        info_label = QLabel(f"Commit: {self.commit_hash[:7]}")
        info_label.setStyleSheet("color: palette(link); font-size: 14px; font-weight: bold;")
        layout.addWidget(info_label)
        
        msg_label = QLabel(f"{tr('message')}: {self.commit_info}")
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("color: palette(window-text); font-size: 12px; padding: 10px; background-color: palette(button); border-radius: 4px;")
        layout.addWidget(msg_label)
        
        actions_label = QLabel(tr('select_action'))
        actions_label.setStyleSheet("color: palette(window-text); font-weight: bold; margin-top: 10px;")
        layout.addWidget(actions_label)
        
        self.reset_soft_btn = QPushButton(tr('reset_soft'))
        self.reset_soft_btn.setIcon(self.icon_manager.get_icon("arrow-clockwise", size=18))
        self.reset_soft_btn.setToolTip(tr('reset_soft_tooltip'))
        self.reset_soft_btn.clicked.connect(lambda: self.reset_commit('soft'))
        layout.addWidget(self.reset_soft_btn)
        
        self.reset_mixed_btn = QPushButton(tr('reset_mixed'))
        self.reset_mixed_btn.setIcon(self.icon_manager.get_icon("arrow-clockwise", size=18))
        self.reset_mixed_btn.setToolTip(tr('reset_mixed_tooltip'))
        self.reset_mixed_btn.clicked.connect(lambda: self.reset_commit('mixed'))
        layout.addWidget(self.reset_mixed_btn)
        
        self.reset_hard_btn = QPushButton(tr('reset_hard'))
        self.reset_hard_btn.setIcon(self.icon_manager.get_icon("warning", size=18))
        self.reset_hard_btn.setToolTip(tr('reset_hard_tooltip'))
        self.reset_hard_btn.setStyleSheet("""
            QPushButton {
                background-color: palette(highlight);
                color: palette(bright-text);
                padding-left: 10px;
            }
            QPushButton:hover {
                background-color: palette(highlight);
            }
        """)
        self.reset_hard_btn.clicked.connect(lambda: self.reset_commit('hard'))
        layout.addWidget(self.reset_hard_btn)
        
        self.checkout_btn = QPushButton(tr('checkout_commit'))
        self.checkout_btn.setIcon(self.icon_manager.get_icon("sign-in", size=18))
        self.checkout_btn.setToolTip(tr('checkout_commit_tooltip'))
        self.checkout_btn.clicked.connect(self.checkout_commit)
        layout.addWidget(self.checkout_btn)
        
        self.create_branch_btn = QPushButton(tr('create_branch_from_here'))
        self.create_branch_btn.setIcon(self.icon_manager.get_icon("git-branch", size=18))
        self.create_branch_btn.setToolTip(tr('create_branch_from_here_tooltip'))
        self.create_branch_btn.clicked.connect(self.create_branch_from_commit)
        layout.addWidget(self.create_branch_btn)
        
        layout.addStretch()
        
        close_btn = QPushButton(tr('close'))
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)
        
        self.apply_styles()
        
    def reset_commit(self, mode):
        mode_names = {
            'soft': tr('reset_soft'),
            'mixed': tr('reset_mixed'),
            'hard': tr('reset_hard')
        }
        
        reply = QMessageBox.question(
            self,
            tr('confirm_reset'),
            f"{tr('confirm_reset_question', mode=mode_names[mode], commit=self.commit_hash[:7])}\n\n" +
            (tr('warning_lose_changes') if mode == 'hard' else ""),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.git_manager.reset_to_commit(self.commit_hash, mode)
            if success:
                QMessageBox.information(self, tr('success'), tr('reset_completed', mode=mode))
                self.accept()
            else:
                QMessageBox.warning(self, tr('error'), f"{tr('error_reset')}:\n{message}")
                
    def checkout_commit(self):
        reply = QMessageBox.question(
            self,
            tr('confirm_checkout'),
            f"{tr('confirm_checkout_question', commit=self.commit_hash[:7])}\n\n" +
            tr('detached_head_warning'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.git_manager.checkout_commit(self.commit_hash)
            if success:
                QMessageBox.information(self, tr('success'), tr('checkout_commit_success', commit=self.commit_hash[:7]))
                self.accept()
            else:
                QMessageBox.warning(self, tr('error'), f"{tr('error')}:\n{message}")
                
    def create_branch_from_commit(self):
        branch_name, ok = QLineEdit().getText(
            self,
            tr('create_new_branch'),
            tr('new_branch_name'),
            QLineEdit.EchoMode.Normal
        )
        
        if ok and branch_name:
            success, message = self.git_manager.create_branch(branch_name, self.commit_hash)
            if success:
                QMessageBox.information(self, tr('success'), tr('branch_created_from_commit', branch=branch_name, commit=self.commit_hash[:7]))
                self.accept()
            else:
                QMessageBox.warning(self, tr('error'), f"{tr('error')}:\n{message}")
                
    def apply_styles(self):
        from ui.theme import get_current_theme
        theme = get_current_theme()
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme.colors['background']};
            }}
            QLabel {{
                color: {theme.colors['text']};
            }}
            QPushButton {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['text_inverse']};
                border: none;
                border-radius: 4px;
                padding: 12px 15px;
                font-weight: bold;
                font-size: 13px;
                text-align: left;
                min-height: 40px;
                padding-left: 10px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {theme.colors['primary_pressed']};
            }}
        """)

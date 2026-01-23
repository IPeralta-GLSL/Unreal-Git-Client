from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFileDialog, QFrame, QWidget,
                             QMessageBox, QComboBox, QCheckBox)
from PyQt6.QtCore import Qt, QPoint
from ui.icon_manager import IconManager
from ui.theme import get_current_theme
from core.translations import tr
from core.settings_manager import SettingsManager
import os
import re

class CloneDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_manager = IconManager()
        self.theme = get_current_theme()
        self.settings_manager = SettingsManager()
        self.drag_position = None
        self.init_ui()
        self.retranslate_ui()
        self.load_saved_paths()
        
    def init_ui(self):
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Main frame
        self.main_frame = QFrame()
        self.main_frame.setObjectName("MainFrame")
        self.main_frame.setStyleSheet(f"""
            QFrame#MainFrame {{
                background-color: {self.theme.colors['background']};
                border: 1px solid {self.theme.colors['border']};
                border-radius: 8px;
            }}
        """)
        main_layout.addWidget(self.main_frame)
        
        # Frame layout
        frame_layout = QVBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)
        
        # Title Bar
        self.setup_title_bar(frame_layout)
        
        # Content Area
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(self.theme.spacing['md'])
        layout.setContentsMargins(self.theme.spacing['xl'], self.theme.spacing['md'], 
                                 self.theme.spacing['xl'], self.theme.spacing['xl'])
        frame_layout.addWidget(content_widget)
        
        # Content
        title_layout = QHBoxLayout()
        
        self.title_label = QLabel()
        self.title_label.setStyleSheet(self.theme.get_title_label_style())
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        self.description_label = QLabel()
        self.description_label.setStyleSheet(self.theme.get_secondary_label_style())
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)
        
        self.url_label = QLabel()
        self.url_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.colors['text']};
                font-weight: {self.theme.fonts['weight_bold']};
                font-size: {self.theme.fonts['size_md']}px;
            }}
        """)
        layout.addWidget(self.url_label)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://github.com/usuario/repositorio.git")
        self.url_input.setStyleSheet(self.theme.get_input_style())
        self.url_input.setMinimumHeight(40)
        layout.addWidget(self.url_input)
        
        layout.addSpacing(self.theme.spacing['md'])
        
        self.path_label = QLabel()
        self.path_label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.colors['text']};
                font-weight: {self.theme.fonts['weight_bold']};
                font-size: {self.theme.fonts['size_md']}px;
            }}
        """)
        layout.addWidget(self.path_label)
        
        self.path_combo = QComboBox()
        self.path_combo.setEditable(True)
        self.path_combo.setMinimumHeight(40)
        self.path_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.theme.colors['background']};
                border: {self.theme.borders['width_thin']}px solid {self.theme.colors['border']};
                border-radius: {self.theme.borders['radius_md']}px;
                padding: 8px 12px;
                font-size: {self.theme.fonts['size_md']}px;
                color: {self.theme.colors['text']};
            }}
            QComboBox:focus {{
                border-color: {self.theme.colors['border_focus']};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.theme.colors['surface']};
                border: 1px solid {self.theme.colors['border']};
                selection-background-color: {self.theme.colors['primary']};
            }}
        """)

        path_layout = QHBoxLayout()
        path_layout.setSpacing(self.theme.spacing['md'])
        path_layout.addWidget(self.path_combo, 1)
        
        self.browse_btn = QPushButton()
        self.browse_btn.setIcon(self.icon_manager.get_icon("folder-open", size=18))
        self.browse_btn.setMinimumHeight(40)
        self.browse_btn.setMinimumWidth(120)
        self.browse_btn.clicked.connect(self.browse_folder)
        self.theme.apply_button_style(self.browse_btn, 'default')
        path_layout.addWidget(self.browse_btn)
        
        layout.addLayout(path_layout)
        
        self.create_folder_check = QCheckBox()
        self.create_folder_check.setChecked(self.settings_manager.get_create_repo_folder())
        self.create_folder_check.stateChanged.connect(self.update_helper_text)
        self.create_folder_check.setStyleSheet(f"""
            QCheckBox {{
                color: {self.theme.colors['text']};
                font-size: {self.theme.fonts['size_sm']}px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid {self.theme.colors['border']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.theme.colors['primary']};
                border-color: {self.theme.colors['primary']};
            }}
        """)
        layout.addWidget(self.create_folder_check)
        
        self.helper_text = QLabel()
        self.helper_text.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.colors['text_link']};
                font-size: {self.theme.fonts['size_xs']}px;
                font-style: italic;
            }}
        """)
        self.helper_text.setWordWrap(True)
        layout.addWidget(self.helper_text)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton()
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.setMinimumWidth(120)
        self.cancel_btn.clicked.connect(self.reject)
        self.theme.apply_button_style(self.cancel_btn, 'default')
        button_layout.addWidget(self.cancel_btn)
        
        self.clone_btn = QPushButton()
        self.clone_btn.setIcon(self.icon_manager.get_icon("download", size=18))
        self.clone_btn.setMinimumHeight(40)
        self.clone_btn.setMinimumWidth(180)
        self.clone_btn.clicked.connect(self.validate_and_accept)
        self.clone_btn.setDefault(True)
        self.theme.apply_button_style(self.clone_btn, 'primary')
        button_layout.addWidget(self.clone_btn)
        
        layout.addLayout(button_layout)
        
    def setup_title_bar(self, parent_layout):
        title_bar = QFrame()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.colors['surface']};
                border-bottom: 1px solid {self.theme.colors['border']};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
        """)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(15, 0, 5, 0)
        
        # Icon
        icon_label = QLabel()
        icon_label.setPixmap(self.icon_manager.get_pixmap("git-fork", 20))
        layout.addWidget(icon_label)
        
        layout.addSpacing(10)
        
        # Title
        self.window_title_label = QLabel(tr('clone_repository'))
        self.window_title_label.setStyleSheet(f"font-weight: bold; color: {self.theme.colors['text']}; font-size: 14px;")
        layout.addWidget(self.window_title_label)
        
        layout.addStretch()
        
        # Close button
        close_btn = QPushButton()
        close_btn.setIcon(self.icon_manager.get_icon("x-square", size=16))
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.reject)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: #e81123;
            }}
        """)
        layout.addWidget(close_btn)
        
        parent_layout.addWidget(title_bar)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
            
    def mouseReleaseEvent(self, event):
        self.drag_position = None
        
    def retranslate_ui(self):
        self.window_title_label.setText(tr('clone_repository'))
        self.title_label.setText(tr('clone_git_repository'))
        self.description_label.setText(tr('clone_description'))
        self.url_label.setText(tr('repository_url') + ":")
        self.path_label.setText(tr('destination_folder') + ":")
        self.browse_btn.setText("  " + tr('browse'))
        self.create_folder_check.setText(tr('create_repo_folder'))
        self.update_helper_text()
        self.cancel_btn.setText(tr('cancel'))
        self.clone_btn.setText("  " + tr('clone_repository'))
    
    def update_helper_text(self):
        if self.create_folder_check.isChecked():
            self.helper_text.setText(tr('clone_helper'))
            self.helper_text.setVisible(True)
        else:
            self.helper_text.setVisible(False)
    
    def load_saved_paths(self):
        self.path_combo.clear()
        paths = self.settings_manager.get_clone_paths()
        default_path = self.settings_manager.get_default_clone_path()
        
        if default_path and os.path.isdir(default_path):
            self.path_combo.addItem(default_path)
        
        for path in paths:
            if path != default_path and os.path.isdir(path):
                self.path_combo.addItem(path)
        
        if self.path_combo.count() == 0:
            self.path_combo.setCurrentText(os.path.expanduser("~"))
    
    def browse_folder(self):
        current_path = self.path_combo.currentText()
        folder = QFileDialog.getExistingDirectory(
            self,
            tr('select_folder'),
            current_path if os.path.isdir(current_path) else os.path.expanduser("~")
        )
        if folder:
            self.path_combo.setCurrentText(folder)
    
    def get_repo_name_from_url(self, url):
        url = url.strip()
        if url.endswith('.git'):
            url = url[:-4]
        match = re.search(r'/([^/]+)/?$', url)
        if match:
            return match.group(1)
        return None
    
    def validate_and_accept(self):
        url = self.url_input.text().strip()
        path = self.path_combo.currentText().strip()
        
        if not url:
            QMessageBox.warning(self, tr('error'), tr('clone_url_required'))
            self.url_input.setFocus()
            return
            
        if not path:
            QMessageBox.warning(self, tr('error'), tr('clone_path_required'))
            self.path_combo.setFocus()
            return
            
        if not os.path.isdir(path):
            QMessageBox.warning(self, tr('error'), tr('clone_path_invalid'))
            self.path_combo.setFocus()
            return
        
        final_path = path
        if self.create_folder_check.isChecked():
            repo_name = self.get_repo_name_from_url(url)
            if repo_name:
                final_path = os.path.join(path, repo_name)
        
        allow_non_empty = self.settings_manager.get_allow_non_empty_clone()
        if os.path.isdir(final_path) and os.listdir(final_path) and not allow_non_empty:
            reply = QMessageBox.question(
                self,
                tr('folder_not_empty'),
                tr('folder_not_empty_msg'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self._final_path = final_path
        self._create_folder = self.create_folder_check.isChecked()
        self.accept()
            
    def get_url(self):
        return self.url_input.text().strip()
        
    def get_path(self):
        return getattr(self, '_final_path', self.path_combo.currentText().strip())
    
    def should_create_folder(self):
        return getattr(self, '_create_folder', self.create_folder_check.isChecked())

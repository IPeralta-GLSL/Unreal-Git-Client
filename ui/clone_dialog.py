from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFileDialog)
from PyQt6.QtCore import Qt
from ui.icon_manager import IconManager
from core.translations import tr
import os

class CloneDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_manager = IconManager()
        self.init_ui()
        self.retranslate_ui()
        
    def init_ui(self):
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(280)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(self.icon_manager.get_pixmap("git-fork", 24))
        title_layout.addWidget(icon_label)
        
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: palette(bright-text); margin-bottom: 10px;")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        self.description_label = QLabel()
        self.description_label.setStyleSheet("color: palette(text); font-size: 12px; margin-bottom: 10px;")
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)
        
        self.url_label = QLabel()
        self.url_label.setStyleSheet("color: palette(window-text); font-weight: bold; font-size: 13px;")
        layout.addWidget(self.url_label)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://github.com/usuario/repositorio.git")
        self.url_input.setMinimumHeight(40)
        layout.addWidget(self.url_input)
        
        layout.addSpacing(10)
        
        self.path_label = QLabel()
        self.path_label.setStyleSheet("color: palette(window-text); font-weight: bold; font-size: 13px;")
        layout.addWidget(self.path_label)
        
        path_layout = QHBoxLayout()
        path_layout.setSpacing(10)
        self.path_input = QLineEdit()
        self.path_input.setText(os.path.expanduser("~"))
        self.path_input.setMinimumHeight(40)
        path_layout.addWidget(self.path_input)
        
        self.browse_btn = QPushButton()
        self.browse_btn.setIcon(self.icon_manager.get_icon("folder-open", size=18))
        self.browse_btn.setMinimumHeight(40)
        self.browse_btn.setMinimumWidth(120)
        self.browse_btn.clicked.connect(self.browse_folder)
        path_layout.addWidget(self.browse_btn)
        
        layout.addLayout(path_layout)
        
        self.helper_text = QLabel()
        self.helper_text.setStyleSheet("color: palette(link); font-size: 11px; font-style: italic;")
        self.helper_text.setWordWrap(True)
        layout.addWidget(self.helper_text)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton()
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.setMinimumWidth(120)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.clone_btn = QPushButton()
        self.clone_btn.setIcon(self.icon_manager.get_icon("download", size=18))
        self.clone_btn.setMinimumHeight(40)
        self.clone_btn.setMinimumWidth(180)
        self.clone_btn.clicked.connect(self.accept)
        self.clone_btn.setDefault(True)
        self.clone_btn.setStyleSheet("""
            QPushButton {
                background-color: palette(highlight);
                color: palette(bright-text);
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: palette(highlight);
            }
            QPushButton:pressed {
                background-color: palette(highlight);
            }
        """)
        button_layout.addWidget(self.clone_btn)
        
        layout.addLayout(button_layout)
        
        self.apply_styles()
        
    def retranslate_ui(self):
        self.setWindowTitle(tr('clone_repository'))
        self.title_label.setText(tr('clone_git_repository'))
        self.description_label.setText(tr('clone_description'))
        self.url_label.setText(tr('repository_url') + ":")
        self.path_label.setText(tr('destination_folder') + ":")
        self.browse_btn.setText("  " + tr('browse'))
        self.helper_text.setText(tr('clone_helper'))
        self.cancel_btn.setText(tr('cancel'))
        self.clone_btn.setText("  " + tr('clone_repository'))
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            tr('select_folder'),
            self.path_input.text()
        )
        if folder:
            self.path_input.setText(folder)
            
    def get_url(self):
        return self.url_input.text().strip()
        
    def get_path(self):
        return self.path_input.text().strip()
        
    def apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: palette(window);
            }
            QLabel {
                color: palette(window-text);
            }
            QLineEdit {
                background-color: palette(base);
                color: palette(window-text);
                border: 2px solid #3d3d3d;
                border-radius: 4px;
                padding: 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #0e639c;
            }
            QPushButton {
                background-color: palette(link);
                color: palette(bright-text);
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: palette(highlight);
            }
            QPushButton:pressed {
                background-color: palette(highlight);
            }
        """)

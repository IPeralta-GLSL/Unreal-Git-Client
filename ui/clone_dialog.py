from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFileDialog)
from PyQt6.QtCore import Qt
from ui.icon_manager import IconManager
import os

class CloneDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_manager = IconManager()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Clonar Repositorio")
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
        
        title = QLabel("Clonar Repositorio Git")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-bottom: 10px;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        description = QLabel("Descarga una copia de un repositorio remoto a tu computadora")
        description.setStyleSheet("color: palette(mid); font-size: 12px; margin-bottom: 10px;")
        description.setWordWrap(True)
        layout.addWidget(description)
        
        url_label = QLabel("URL del Repositorio:")
        url_label.setStyleSheet("color: palette(window-text); font-weight: bold; font-size: 13px;")
        layout.addWidget(url_label)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://github.com/usuario/repositorio.git")
        self.url_input.setMinimumHeight(40)
        layout.addWidget(self.url_input)
        
        layout.addSpacing(10)
        
        path_label = QLabel("Carpeta de Destino:")
        path_label.setStyleSheet("color: palette(window-text); font-weight: bold; font-size: 13px;")
        layout.addWidget(path_label)
        
        path_layout = QHBoxLayout()
        path_layout.setSpacing(10)
        self.path_input = QLineEdit()
        self.path_input.setText(os.path.expanduser("~"))
        self.path_input.setMinimumHeight(40)
        path_layout.addWidget(self.path_input)
        
        browse_btn = QPushButton("  Explorar")
        browse_btn.setIcon(self.icon_manager.get_icon("folder-open", size=18))
        browse_btn.setMinimumHeight(40)
        browse_btn.setMinimumWidth(120)
        browse_btn.clicked.connect(self.browse_folder)
        path_layout.addWidget(browse_btn)
        
        layout.addLayout(path_layout)
        
        helper_text = QLabel("ℹ️ El repositorio se clonará en una nueva carpeta dentro de la ubicación seleccionada")
        helper_text.setStyleSheet("color: palette(link); font-size: 11px; font-style: italic;")
        helper_text.setWordWrap(True)
        layout.addWidget(helper_text)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(120)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        clone_btn = QPushButton("  Clonar Repositorio")
        clone_btn.setIcon(self.icon_manager.get_icon("download", size=18))
        clone_btn.setMinimumHeight(40)
        clone_btn.setMinimumWidth(180)
        clone_btn.clicked.connect(self.accept)
        clone_btn.setDefault(True)
        clone_btn.setStyleSheet("""
            QPushButton {
                background-color: #16825d;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1a9d6f;
            }
            QPushButton:pressed {
                background-color: #136d4d;
            }
        """)
        button_layout.addWidget(clone_btn)
        
        layout.addLayout(button_layout)
        
        self.apply_styles()
        
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Carpeta de Destino",
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
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0d5a8f;
            }
        """)

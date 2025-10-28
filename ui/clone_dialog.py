from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFileDialog)
from PyQt6.QtCore import Qt
import os

class CloneDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Clonar Repositorio")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        url_label = QLabel("URL del Repositorio:")
        layout.addWidget(url_label)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://github.com/usuario/repositorio.git")
        layout.addWidget(self.url_input)
        
        layout.addSpacing(10)
        
        path_label = QLabel("Carpeta de Destino:")
        layout.addWidget(path_label)
        
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setText(os.path.expanduser("~"))
        path_layout.addWidget(self.path_input)
        
        browse_btn = QPushButton("Explorar")
        browse_btn.clicked.connect(self.browse_folder)
        path_layout.addWidget(browse_btn)
        
        layout.addLayout(path_layout)
        
        layout.addSpacing(20)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        clone_btn = QPushButton("Clonar")
        clone_btn.clicked.connect(self.accept)
        clone_btn.setDefault(True)
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
                background-color: #1e1e1e;
            }
            QLabel {
                color: #cccccc;
                font-weight: bold;
            }
            QLineEdit {
                background-color: #252526;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 8px;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0d5a8f;
            }
        """)

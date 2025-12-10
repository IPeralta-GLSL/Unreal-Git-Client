from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFileDialog, QFrame, QWidget)
from PyQt6.QtCore import Qt, QPoint
from ui.icon_manager import IconManager
from ui.theme import get_current_theme
from core.translations import tr
import os

class CloneDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.icon_manager = IconManager()
        self.theme = get_current_theme()
        self.drag_position = None
        self.init_ui()
        self.retranslate_ui()
        
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
        
        path_layout = QHBoxLayout()
        path_layout.setSpacing(self.theme.spacing['md'])
        self.path_input = QLineEdit()
        self.path_input.setText(os.path.expanduser("~"))
        self.path_input.setStyleSheet(self.theme.get_input_style())
        self.path_input.setMinimumHeight(40)
        path_layout.addWidget(self.path_input)
        
        self.browse_btn = QPushButton()
        self.browse_btn.setIcon(self.icon_manager.get_icon("folder-open", size=18))
        self.browse_btn.setMinimumHeight(40)
        self.browse_btn.setMinimumWidth(120)
        self.browse_btn.clicked.connect(self.browse_folder)
        self.theme.apply_button_style(self.browse_btn, 'default')
        path_layout.addWidget(self.browse_btn)
        
        layout.addLayout(path_layout)
        
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
        self.clone_btn.clicked.connect(self.accept)
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
        close_btn.setIcon(self.icon_manager.get_icon("x", size=16))
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

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTabWidget, QToolBar, QStatusBar,
                             QFileDialog, QMessageBox, QLabel)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon
from ui.repository_tab import RepositoryTab
from core.git_manager import GitManager
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.git_manager = GitManager()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Unreal Git Client")
        self.setGeometry(100, 100, 1400, 900)
        
        self.setup_statusbar()
        self.setup_toolbar()
        self.setup_central_widget()
        
        self.apply_styles()
        
    def setup_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        new_repo_action = QAction("📁 Abrir Repositorio", self)
        new_repo_action.triggered.connect(self.open_repository)
        toolbar.addAction(new_repo_action)
        
        toolbar.addSeparator()
        
        clone_action = QAction("⬇️ Clonar Repositorio", self)
        clone_action.triggered.connect(self.clone_repository)
        toolbar.addAction(clone_action)
        
        toolbar.addSeparator()
        
        new_tab_action = QAction("➕ Nueva Pestaña", self)
        new_tab_action.triggered.connect(self.add_empty_tab)
        toolbar.addAction(new_tab_action)
        
        close_tab_action = QAction("❌ Cerrar Pestaña", self)
        close_tab_action.triggered.connect(self.close_current_tab)
        toolbar.addAction(close_tab_action)
        
    def setup_central_widget(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        layout.addWidget(self.tab_widget)
        
        self.add_empty_tab()
        
    def setup_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Listo")
        
    def add_empty_tab(self):
        repo_tab = RepositoryTab(self.git_manager)
        index = self.tab_widget.addTab(repo_tab, "📂 Sin Repositorio")
        self.tab_widget.setCurrentIndex(index)
        
    def open_repository(self):
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Seleccionar Repositorio Git",
            os.path.expanduser("~")
        )
        
        if folder:
            if self.git_manager.is_git_repository(folder):
                current_tab = self.tab_widget.currentWidget()
                if isinstance(current_tab, RepositoryTab):
                    current_tab.load_repository(folder)
                    repo_name = os.path.basename(folder)
                    self.tab_widget.setTabText(self.tab_widget.currentIndex(), f"📁 {repo_name}")
                    self.status_bar.showMessage(f"Repositorio cargado: {folder}")
            else:
                QMessageBox.warning(
                    self, 
                    "No es un repositorio Git",
                    f"La carpeta seleccionada no contiene un repositorio Git.\n\n{folder}"
                )
                
    def clone_repository(self):
        from ui.clone_dialog import CloneDialog
        dialog = CloneDialog(self)
        if dialog.exec():
            url = dialog.get_url()
            path = dialog.get_path()
            
            current_tab = self.tab_widget.currentWidget()
            if isinstance(current_tab, RepositoryTab):
                current_tab.clone_repository(url, path)
                
    def close_tab(self, index):
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)
        else:
            QMessageBox.information(
                self,
                "No se puede cerrar",
                "Debe haber al menos una pestaña abierta."
            )
            
    def close_current_tab(self):
        current_index = self.tab_widget.currentIndex()
        self.close_tab(current_index)
        
    def on_tab_changed(self, index):
        if index >= 0:
            tab = self.tab_widget.widget(index)
            if isinstance(tab, RepositoryTab) and tab.repo_path:
                self.status_bar.showMessage(f"Repositorio: {tab.repo_path}")
            else:
                self.status_bar.showMessage("Listo")
                
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QToolBar {
                background-color: #2d2d2d;
                border: none;
                padding: 8px;
                spacing: 5px;
            }
            QToolBar QToolButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QToolBar QToolButton:hover {
                background-color: #1177bb;
            }
            QToolBar QToolButton:pressed {
                background-color: #0d5a8f;
            }
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                background-color: #252526;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #252526;
                color: white;
                border-bottom: 2px solid #0e639c;
            }
            QTabBar::tab:hover {
                background-color: #3d3d3d;
            }
            QStatusBar {
                background-color: #007acc;
                color: white;
                font-weight: bold;
            }
        """)

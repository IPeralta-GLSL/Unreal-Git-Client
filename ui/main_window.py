from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTabWidget, QToolBar, QStatusBar,
                             QFileDialog, QMessageBox, QLabel)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut
from ui.repository_tab import RepositoryTab
from ui.clone_dialog import CloneDialog
from core.git_manager import GitManager
from core.settings_manager import SettingsManager
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.git_manager = GitManager()
        self.settings_manager = SettingsManager()
        self.init_ui()
        self.setup_shortcuts()
        
    def init_ui(self):
        self.setWindowTitle("Git Client")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 600)
        
        self.setup_statusbar()
        self.setup_central_widget()
        
        self.apply_styles()
        
    def setup_toolbar(self):
        pass
        
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
        
        self.new_tab_button = QPushButton("+")
        self.new_tab_button.setFixedSize(35, 35)
        self.new_tab_button.setToolTip("Nueva pestaña (Ctrl+T)")
        self.new_tab_button.clicked.connect(self.add_empty_tab)
        self.new_tab_button.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                font-size: 20px;
                font-weight: bold;
                padding: 0px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #1177bb;
                color: white;
            }
            QPushButton:pressed {
                background-color: #094771;
            }
        """)
        
        self.tab_widget.setCornerWidget(self.new_tab_button, Qt.Corner.TopRightCorner)
        
        layout.addWidget(self.tab_widget)
        
        self.setup_shortcuts()
        
        self.add_empty_tab()
        
    def setup_shortcuts(self):
        new_tab_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        new_tab_shortcut.activated.connect(self.add_empty_tab)
        
        close_tab_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_tab_shortcut.activated.connect(self.close_current_tab)
        
        next_tab_shortcut = QShortcut(QKeySequence("Ctrl+Tab"), self)
        next_tab_shortcut.activated.connect(self.next_tab)
        
        prev_tab_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        prev_tab_shortcut.activated.connect(self.prev_tab)
        
    def setup_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Listo")
        
    def add_empty_tab(self):
        repo_tab = RepositoryTab(self.git_manager, self.settings_manager, parent_window=self)
        index = self.tab_widget.addTab(repo_tab, "🏠 Inicio")
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
        
    def next_tab(self):
        current = self.tab_widget.currentIndex()
        next_index = (current + 1) % self.tab_widget.count()
        self.tab_widget.setCurrentIndex(next_index)
        
    def prev_tab(self):
        current = self.tab_widget.currentIndex()
        prev_index = (current - 1) % self.tab_widget.count()
        self.tab_widget.setCurrentIndex(prev_index)
        
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
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                background-color: #252526;
                border-top: 2px solid #0e639c;
            }
            QTabBar {
                background-color: #2d2d2d;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background-color: #252526;
                color: white;
                border-bottom: 2px solid #0e639c;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3d3d3d;
            }
            QTabBar::close-button {
                image: url(none);
                subcontrol-position: right;
                margin-right: 4px;
            }
            QTabBar::close-button:hover {
                background-color: #e81123;
                border-radius: 2px;
            }
            QStatusBar {
                background-color: #007acc;
                color: white;
                font-weight: bold;
            }
        """)

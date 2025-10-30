from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTabWidget, QToolBar, QStatusBar,
                             QFileDialog, QMessageBox, QLabel, QMenuBar, QMenu)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut
from ui.repository_tab import RepositoryTab
from ui.clone_dialog import CloneDialog
from ui.theme import get_current_theme
from core.git_manager import GitManager
from core.settings_manager import SettingsManager
from core.account_manager import AccountManager
import os

class MainWindow(QMainWindow):
    def __init__(self, plugin_manager=None):
        super().__init__()
        self.git_manager = GitManager()
        self.settings_manager = SettingsManager()
        self.account_manager = AccountManager()
        self.plugin_manager = plugin_manager
        self.init_ui()
        self.setup_shortcuts()
        
    def init_ui(self):
        self.setWindowTitle("Git Client")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 600)
        
        self.setup_menubar()
        self.setup_statusbar()
        self.setup_central_widget()
        
        self.apply_styles()
        
    def setup_menubar(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("Archivo")
        
        open_action = QAction("Abrir Repositorio", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_repository)
        file_menu.addAction(open_action)
        
        clone_action = QAction("Clonar Repositorio", self)
        clone_action.setShortcut("Ctrl+Shift+C")
        clone_action.triggered.connect(self.clone_repository)
        file_menu.addAction(clone_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Salir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
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
                background-color: palette(link);
                color: palette(bright-text);
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                font-size: 20px;
                font-weight: bold;
                padding: 0px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: palette(highlight);
                color: palette(bright-text);
            }
            QPushButton:pressed {
                background-color: palette(highlight);
            }
        """)
        
        self.tab_widget.setCornerWidget(self.new_tab_button, Qt.Corner.TopRightCorner)
        
        layout.addWidget(self.tab_widget)
        
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
        
        self.settings_button = QPushButton("⚙️")
        self.settings_button.setFixedSize(35, 28)
        self.settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_button.setToolTip("Configuración y cuentas")
        self.settings_button.clicked.connect(self.open_settings)
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                font-size: 16px;
                color: palette(bright-text);
                padding: 2px;
                margin-left: 5px;
                margin-right: 10px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        self.status_bar.addWidget(self.settings_button)
        self.status_bar.showMessage("Listo")
        
    def add_empty_tab(self):
        repo_tab = RepositoryTab(self.git_manager, self.settings_manager, parent_window=self, plugin_manager=self.plugin_manager)
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
                    current_index = self.tab_widget.currentIndex()
                    self.tab_widget.setTabText(current_index, f"📁 {repo_name}")
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
        self.tab_widget.removeTab(index)
        
        if self.tab_widget.count() == 0:
            self.add_empty_tab()
            
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
    
    def open_settings(self):
        from ui.accounts_dialog import AccountsDialog
        dialog = AccountsDialog(self.account_manager, self.plugin_manager, self)
        dialog.accounts_changed.connect(self.on_accounts_changed)
        dialog.exec()
    
    def on_accounts_changed(self):
        self.status_bar.showMessage("Cuentas actualizadas", 3000)
                
    def apply_styles(self):
        theme = get_current_theme()
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: palette(window);
            }}
            QTabWidget::pane {{
                border: 1px solid {theme.colors['border']};
                background-color: palette(base);
                border-top: 2px solid {theme.colors['primary']};
            }}
            QTabBar {{
                background-color: palette(button);
            }}
            QTabBar::tab {{
                background-color: palette(button);
                color: palette(window-text);
                border: 1px solid {theme.colors['border']};
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 120px;
            }}
            QTabBar::tab:selected {{
                background-color: palette(base);
                color: palette(bright-text);
                border-bottom: 2px solid {theme.colors['primary']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: palette(text);
            }}
            QTabBar::close-button {{
                image: url(none);
                subcontrol-position: right;
                margin-right: 4px;
            }}
            QTabBar::close-button:hover {{
                background-color: {theme.colors['danger']};
                border-radius: 2px;
            }}
            QStatusBar {{
                background-color: {theme.colors['primary']};
                color: palette(bright-text);
                font-weight: bold;
            }}
            QMenuBar {{
                background-color: palette(button);
                color: palette(window-text);
                padding: 4px;
            }}
            QMenuBar::item {{
                background-color: transparent;
                padding: 8px 12px;
                border-radius: 4px;
            }}
            QMenuBar::item:selected {{
                background-color: palette(text);
            }}
            QMenu {{
                background-color: palette(button);
                color: palette(window-text);
                border: 1px solid {theme.colors['border']};
                padding: 5px;
            }}
            QMenu::item {{
                padding: 8px 30px 8px 20px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: palette(highlight);
                color: palette(bright-text);
            }}
            QMenu::separator {{
                height: 1px;
                background-color: palette(text);
                margin: 5px 0px;
            }}
        """)

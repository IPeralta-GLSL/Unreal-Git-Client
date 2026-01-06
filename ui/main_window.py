from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTabWidget, QToolBar, QStatusBar,
                             QFileDialog, QMessageBox, QLabel, QMenuBar, QMenu, QFrame,
                             QSystemTrayIcon, QApplication, QProgressDialog, QToolButton, QTabBar)
from PyQt6.QtCore import Qt, QSize, QTimer, QPoint, QRect, QEvent
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut, QCursor
from ui.repository_tab import RepositoryTab
from ui.clone_dialog import CloneDialog
from ui.theme import get_current_theme
from core.git_manager import GitManager
from core.settings_manager import SettingsManager
from core.account_manager import AccountManager
from core.translations import tr
from core.updater import UpdateChecker
import os
import sys
import platform
import webbrowser

from ui.icon_manager import IconManager


class PlusTabBar(QTabBar):
    def __init__(self, icon_manager, add_callback):
        super().__init__()
        self.icon_manager = icon_manager
        self.add_callback = add_callback
        self.plus_button = QToolButton(self)
        self.plus_button.setIcon(self.icon_manager.get_icon("file-plus", size=18))
        self.plus_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.plus_button.setAutoRaise(True)
        self.plus_button.setToolTip(f"{tr('new_tab')} (Ctrl+T)")
        self.plus_button.clicked.connect(self.add_callback)
        self.plus_button.resize(28, 24)
        self.setMovable(True)
        self.setTabsClosable(True)
        self._margin = 8

    def _position_plus(self):
        if self.count() > 0:
            last_rect = self.tabRect(self.count() - 1)
            x = last_rect.right() + self._margin
        else:
            x = self._margin
        x = min(x, self.width() - self.plus_button.width() - self._margin)
        y = (self.height() - self.plus_button.height()) // 2
        self.plus_button.move(max(self._margin, x), max(0, y))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_plus()

    def tabLayoutChange(self):
        super().tabLayoutChange()
        self._position_plus()

class MainWindow(QMainWindow):
    def __init__(self, plugin_manager=None):
        super().__init__()
        self.git_manager = GitManager()
        self.settings_manager = SettingsManager()
        self.account_manager = AccountManager()
        self.plugin_manager = plugin_manager
        self.icon_manager = IconManager()
        self.drag_position = QPoint()
        self.border_width = 5
        self.init_ui()
        self.setup_shortcuts()
        
        # Auto-update check
        self.update_checker = UpdateChecker()
        self.update_checker.update_available.connect(self.show_update_dialog)
        self.update_checker.start()
        
    def init_ui(self):
        self.setWindowTitle(tr('app_name'))
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1000, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowSystemMenuHint)
        
        self.setup_statusbar()
        self.setup_central_widget()
        self.setup_tray_icon()
        
        self.apply_styles()

    def setup_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Widgets for status bar (all on the left)
        self.status_label = QLabel(tr('ready'))
        self.status_label.setStyleSheet("padding-right: 15px; font-weight: bold;")
        self.status_bar.addWidget(self.status_label)
        
        self.progress_label = QLabel()
        self.progress_label.setStyleSheet("padding-right: 15px; color: #4ec9b0;")
        self.status_bar.addWidget(self.progress_label)

    def update_status_bar(self):
        pass # Removed branch update logic

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.icon_manager.get_icon("git-branch"))
        
        tray_menu = QMenu()
        
        show_action = QAction(tr('show'), self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)
        
        quit_action = QAction(tr('quit'), self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()
        
    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()
            
    def show_window(self):
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.activateWindow()
        self.raise_()
        
    def quit_application(self):
        self.tray_icon.hide()
        QApplication.quit()
        
    def closeEvent(self, event):
        if self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                tr('app_name'),
                tr('app_minimized_to_tray'),
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            event.ignore()
        else:
            event.accept()
        
    def setup_toolbar(self):
        from ui.icon_manager import IconManager
        from ui.theme import get_current_theme
        
        theme = get_current_theme()
        self.icon_manager = IconManager()
        
    def setup_central_widget(self):
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.tab_widget = QTabWidget()
        plus_tab_bar = PlusTabBar(self.icon_manager, self.add_empty_tab)
        self.tab_widget.setTabBar(plus_tab_bar)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        self.tab_widget.setCornerWidget(self.create_window_controls(), Qt.Corner.TopRightCorner)
        self.tab_widget.setCornerWidget(self.create_app_icon(), Qt.Corner.TopLeftCorner)
        
        self.tab_widget.tabBar().installEventFilter(self)
        
        layout.addWidget(self.tab_widget)
        
        self.add_empty_tab()

    def create_app_icon(self):
        container = QWidget()
        container.setObjectName("appCorner")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 0, 5, 0)
        layout.setSpacing(0)
        
        app_icon = QLabel()
        app_icon.setPixmap(self.icon_manager.get_pixmap("git-branch", size=20))
        layout.addWidget(app_icon)
        
        return container

    def create_window_controls(self):
        from ui.theme import get_current_theme
        theme = get_current_theme()
        
        container = QWidget()
        container.setObjectName("windowControls")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.settings_button = QPushButton()
        self.settings_button.setIcon(self.icon_manager.get_icon("gear-six", size=18))
        self.settings_button.setFixedSize(46, 32)
        self.settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_button.setToolTip(tr('settings'))
        self.settings_button.clicked.connect(self.open_settings)
        self.settings_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 0px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['surface_hover']};
            }}
        """)
        layout.addWidget(self.settings_button)
        
        min_button = QPushButton()
        min_button.setIcon(self.icon_manager.get_icon("window-minimize-symbolic-svgrepo-com", size=16))
        min_button.setFixedSize(46, 32)
        min_button.setCursor(Qt.CursorShape.PointingHandCursor)
        min_button.clicked.connect(self.showMinimized)
        min_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 0px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['surface_hover']};
            }}
        """)
        layout.addWidget(min_button)
        
        self.max_button = QPushButton()
        self.max_button.setFixedSize(46, 32)
        self.max_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.max_button.clicked.connect(self.toggle_maximize)
        self.max_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 0px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['surface_hover']};
            }}
        """)
        layout.addWidget(self.max_button)
        
        close_button = QPushButton()
        close_button.setIcon(self.icon_manager.get_icon("x-square", size=16))
        close_button.setFixedSize(46, 32)
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(self.close)
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
        layout.addWidget(close_button)
        
        self.update_window_control_icons()
        return container

    def eventFilter(self, obj, event):
        if obj == self.tab_widget.tabBar():
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    if self.tab_widget.tabBar().tabAt(event.pos()) == -1:
                        if self.windowHandle():
                            self.windowHandle().startSystemMove()
                        return True
            elif event.type() == QEvent.Type.MouseButtonDblClick:
                if event.button() == Qt.MouseButton.LeftButton:
                    if self.tab_widget.tabBar().tabAt(event.pos()) == -1:
                        self.toggle_maximize()
                        return True
        return super().eventFilter(obj, event)

    
    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        self.update_window_control_icons()

    def update_window_control_icons(self):
        if hasattr(self, "max_button"):
            if self.isMaximized():
                self.max_button.setIcon(self.icon_manager.get_icon("window-restore-symbolic-svgrepo-com", size=16))
                self.max_button.setToolTip("Restore")
            else:
                self.max_button.setIcon(self.icon_manager.get_icon("window-maximize-symbolic-svgrepo-com", size=16))
                self.max_button.setToolTip("Maximize")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.isMaximized():
            pos = event.pos()
            edges = self.get_window_edges(pos)
            
            if edges != Qt.Edge(0):
                if self.windowHandle():
                    self.windowHandle().startSystemResize(edges)
                return
        
        super().mousePressEvent(event)
    
    def get_window_edges(self, pos):
        rect = self.rect()
        edges = Qt.Edge(0)
        
        if pos.x() <= self.border_width:
            edges |= Qt.Edge.LeftEdge
        if pos.x() >= rect.width() - self.border_width:
            edges |= Qt.Edge.RightEdge
        if pos.y() <= self.border_width:
            edges |= Qt.Edge.TopEdge
        if pos.y() >= rect.height() - self.border_width:
            edges |= Qt.Edge.BottomEdge
        
        return edges
    
    def mouseMoveEvent(self, event):
        if not self.isMaximized():
            pos = event.pos()
            edges = self.get_window_edges(pos)
            self.update_cursor_for_edges(edges)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        
        super().mouseMoveEvent(event)
    
    def update_cursor_for_edges(self, edges):
        if edges == Qt.Edge(0):
            self.setCursor(Qt.CursorShape.ArrowCursor)
        elif edges == (Qt.Edge.TopEdge | Qt.Edge.LeftEdge):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edges == (Qt.Edge.TopEdge | Qt.Edge.RightEdge):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif edges == (Qt.Edge.BottomEdge | Qt.Edge.LeftEdge):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif edges == (Qt.Edge.BottomEdge | Qt.Edge.RightEdge):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edges == Qt.Edge.TopEdge or edges == Qt.Edge.BottomEdge:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif edges == Qt.Edge.LeftEdge or edges == Qt.Edge.RightEdge:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        

    def add_empty_tab(self):
        repo_tab = RepositoryTab(GitManager(), self.settings_manager, parent_window=self, plugin_manager=self.plugin_manager)
        index = self.tab_widget.addTab(repo_tab, self.icon_manager.get_icon("house-line"), tr('home'))
        self.tab_widget.setCurrentIndex(index)
        self._set_tab_close_button(index)
        
    def open_repository(self):
        folder = QFileDialog.getExistingDirectory(
            self, 
            tr('select_repository'),
            os.path.expanduser("~")
        )
        
        if folder:
            if self.git_manager.is_git_repository(folder):
                current_tab = self.tab_widget.currentWidget()
                if isinstance(current_tab, RepositoryTab):
                    current_tab.load_repository(folder)
                    repo_name = os.path.basename(folder)
                    current_index = self.tab_widget.currentIndex()
                    self.tab_widget.setTabIcon(current_index, self.icon_manager.get_icon("folder-open"))
                    self.tab_widget.setTabText(current_index, repo_name)
                    self.status_bar.showMessage(f"{tr('repository_loaded')}: {folder}")
            else:
                QMessageBox.warning(
                    self, 
                    tr('not_git_repository'),
                    f"{tr('not_git_repository_msg')}\n\n{folder}"
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
                self.status_bar.showMessage(f"{tr('repository')}: {tab.repo_path}")
            else:
                self.status_bar.showMessage(tr('ready'))
    
    def open_settings(self):
        from ui.accounts_dialog import AccountsDialog
        dialog = AccountsDialog(self.account_manager, self.plugin_manager, self)
        dialog.accounts_changed.connect(self.on_accounts_changed)
        dialog.language_changed.connect(self.on_language_changed)
        dialog.exec()
    
    def on_language_changed(self, language_code):
        self.update_translations()
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if hasattr(tab, 'update_translations'):
                tab.update_translations()
            elif hasattr(tab, 'retranslate_ui'):
                tab.retranslate_ui()
            if hasattr(tab, 'home_view') and hasattr(tab.home_view, 'update_translations'):
                tab.home_view.update_translations()
    
    def update_translations(self):
        self.status_bar.showMessage(tr('ready'))
        self.settings_button.setToolTip(tr('settings'))
        tab_bar = self.tab_widget.tabBar()
        if isinstance(tab_bar, PlusTabBar):
            tab_bar.plus_button.setToolTip(f"{tr('new_tab')} (Ctrl+T)")
        for i in range(self.tab_widget.count()):
            self._set_tab_close_button(i)

    def _set_tab_close_button(self, index):
        tab_bar = self.tab_widget.tabBar()
        button = QToolButton(tab_bar)
        button.setIcon(self.icon_manager.get_icon("x-square", size=14))
        button.setAutoRaise(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda _, b=button, tb=tab_bar: self.close_tab(tb.tabAt(b.pos())))
        tab_bar.setTabButton(index, QTabBar.ButtonPosition.RightSide, button)
    
    def on_accounts_changed(self):
        self.status_bar.showMessage("Cuentas actualizadas", 3000)
                
    def apply_styles(self):
        theme = get_current_theme()
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme.colors['background']};
                border: none;
            }}
            QWidget#centralWidget {{
                background-color: {theme.colors['background']};
                border: none;
            }}
            QTabWidget {{
                border: none;
                background-color: {theme.colors['background']};
            }}
            QTabWidget::left-corner, QTabWidget::right-corner {{
                background-color: {theme.colors['background']};
                border: none;
            }}
            QWidget#appCorner {{
                background-color: {theme.colors['background']};
                border: none;
            }}
            QWidget#windowControls {{
                background-color: {theme.colors['background']};
                border: none;
            }}
            QWidget#windowControls QPushButton {{
                background-color: transparent;
                border: none;
            }}
            QWidget#windowControls QPushButton:focus {{
                border: none;
            }}
            QTabWidget::pane {{
                border: none;
                background-color: {theme.colors['background']};
            }}
            QTabWidget::tab-bar {{
                left: 5px;
            }}
            QTabBar {{
                background-color: {theme.colors['background']};
                qproperty-drawBase: 0;
                border-bottom: none;
            }}
            QTabBar::tab {{
                background-color: transparent;
                color: {theme.colors['text']};
                border: none;
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                min-width: 120px;
                max-width: 200px;
            }}
            QTabBar::tab:selected {{
                background-color: {theme.colors['surface']};
                color: {theme.colors['primary']};
                border-bottom: 2px solid {theme.colors['surface']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {theme.colors['surface_hover']};
            }}
            QTabBar::close-button {{
                subcontrol-position: right;
                margin-right: 4px;
                border-radius: 2px;
            }}
            QTabBar::close-button:hover {{
                background-color: {theme.colors['danger']};
            }}
            QStatusBar {{
                background-color: {theme.colors['surface']};
                color: {theme.colors['text']};
                border-top: 1px solid {theme.colors['border']};
            }}
        """)
    
    def setup_shortcuts(self):
        new_tab_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        new_tab_shortcut.activated.connect(self.add_empty_tab)
        
        close_tab_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_tab_shortcut.activated.connect(self.close_current_tab)
        
        next_tab_shortcut = QShortcut(QKeySequence("Ctrl+Tab"), self)
        next_tab_shortcut.activated.connect(self.next_tab)
        
        prev_tab_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        prev_tab_shortcut.activated.connect(self.prev_tab)
        
        open_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        open_shortcut.activated.connect(self.open_repository)
        
        clone_shortcut = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
        clone_shortcut.activated.connect(self.clone_repository)
        
        settings_shortcut = QShortcut(QKeySequence("Ctrl+,"), self)
        settings_shortcut.activated.connect(self.open_settings)
        
        quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        quit_shortcut.activated.connect(self.close)

    def show_update_dialog(self, version, url, notes):
        msg = QMessageBox(self)
        msg.setWindowTitle(tr('update_available'))
        msg.setText(f"{tr('new_version_available')}: {version}")
        msg.setInformativeText(f"{tr('update_question')}\n\n{notes}")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        
        if msg.exec() == QMessageBox.StandardButton.Yes:
            # Check if it's a direct download link (exe) and if we are running frozen
            is_frozen = getattr(sys, 'frozen', False)
            if url.endswith('.exe') and is_frozen:
                self.start_auto_update(url)
            else:
                webbrowser.open(url)

    def start_auto_update(self, url):
        from core.updater import UpdateDownloader, install_update
        
        self.progress_dialog = QProgressDialog(tr('downloading_update'), tr('cancel'), 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.show()
        
        self.downloader = UpdateDownloader(url, "update_temp.exe")
        self.downloader.progress.connect(self.progress_dialog.setValue)
        self.downloader.finished.connect(self.on_update_downloaded)
        self.downloader.error.connect(self.on_update_error)
        self.downloader.start()
        
    def on_update_downloaded(self, file_path):
        from core.updater import install_update
        self.progress_dialog.close()
        
        success, message = install_update(file_path)
        if success:
            QApplication.quit()
        else:
            QMessageBox.critical(self, tr('error'), f"Update failed: {message}")
            
    def on_update_error(self, error_message):
        self.progress_dialog.close()
        QMessageBox.critical(self, tr('error'), f"Download failed: {error_message}")

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange:
            if self.isActiveWindow():
                current_widget = self.tab_widget.currentWidget()
                if isinstance(current_widget, RepositoryTab):
                    current_widget.refresh_status()
        if event.type() == QEvent.Type.WindowStateChange:
            self.update_window_control_icons()
        super().changeEvent(event)

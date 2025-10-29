from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                             QListWidget, QTextEdit, QPushButton, QLabel,
                             QGroupBox, QLineEdit, QMessageBox, QListWidgetItem,
                             QProgressDialog, QScrollArea, QFrame, QCheckBox, QStackedWidget,
                             QSizePolicy, QMenu, QInputDialog, QApplication)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QPoint, QByteArray, QUrl
from PyQt6.QtGui import QFont, QIcon, QCursor, QAction, QColor, QPixmap, QPainter, QBrush
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from ui.home_view import HomeView
from ui.icon_manager import IconManager
import os
import hashlib

class CloneThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, git_manager, url, path):
        super().__init__()
        self.git_manager = git_manager
        self.url = url
        self.path = path
        
    def run(self):
        success, message = self.git_manager.clone_repository(self.url, self.path)
        self.finished.emit(success, message)

class RepositoryTab(QWidget):
    def __init__(self, git_manager, settings_manager=None, parent_window=None):
        super().__init__()
        self.git_manager = git_manager
        self.settings_manager = settings_manager
        self.repo_path = None
        self.parent_window = parent_window
        self.avatar_cache = {}
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.on_avatar_downloaded)
        self.icon_manager = IconManager()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.stacked_widget = QStackedWidget()
        
        self.home_view = HomeView(self.settings_manager)
        self.home_view.open_repo_requested.connect(self.on_home_open_repo)
        self.home_view.clone_repo_requested.connect(self.on_home_clone_repo)
        self.home_view.open_recent_repo.connect(self.load_repository)
        self.stacked_widget.addWidget(self.home_view)
        
        self.repo_view = QWidget()
        repo_layout = QVBoxLayout(self.repo_view)
        repo_layout.setContentsMargins(0, 0, 0, 0)
        repo_layout.setSpacing(0)
        
        self.create_top_bar()
        repo_layout.addWidget(self.top_bar)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([350, 1050])
        splitter.setHandleWidth(2)
        
        repo_layout.addWidget(splitter)
        self.stacked_widget.addWidget(self.repo_view)
        
        layout.addWidget(self.stacked_widget)
        
        self.show_home_view()
        
    def create_top_bar(self):
        self.top_bar = QFrame()
        self.top_bar.setMaximumHeight(70)
        self.top_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.top_bar.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-bottom: 2px solid #0e639c;
            }
        """)
        
        layout = QHBoxLayout(self.top_bar)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(15)
        
        branch_container = QWidget()
        branch_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        branch_layout = QVBoxLayout(branch_container)
        branch_layout.setContentsMargins(0, 0, 0, 0)
        branch_layout.setSpacing(3)
        
        branch_title = QLabel("RAMA ACTUAL (clic para cambiar)")
        branch_title.setStyleSheet("color: #888888; font-size: 9px; font-weight: bold;")
        branch_title.setMaximumHeight(14)
        branch_layout.addWidget(branch_title)
        
        self.branch_button = QPushButton()
        self.branch_button.setText("main")
        self.branch_button.setMinimumSize(180, 28)
        self.branch_button.setMaximumHeight(28)
        self.branch_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.branch_button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 13px;
                color: #4ec9b0;
                background-color: #1e1e1e;
                border: 2px solid #4ec9b0;
                border-radius: 5px;
                padding: 2px 12px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #2d2d2d;
                border-color: #5fd9c0;
                color: #5fd9c0;
            }
            QPushButton:pressed {
                background-color: #0e639c;
            }
        """)
        self.branch_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.branch_button.clicked.connect(self.show_branch_menu)
        branch_layout.addWidget(self.branch_button)
        
        layout.addWidget(branch_container, 1)
        
        layout.addStretch()
        
        self.pull_btn = QPushButton(" Pull")
        self.pull_btn.setIcon(self.icon_manager.get_icon("download", size=18))
        self.pull_btn.setMinimumSize(85, 36)
        self.pull_btn.setMaximumSize(110, 36)
        self.pull_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.pull_btn.setToolTip("Descargar cambios del servidor")
        self.pull_btn.clicked.connect(self.do_pull)
        layout.addWidget(self.pull_btn)
        
        self.push_btn = QPushButton(" Push")
        self.push_btn.setIcon(self.icon_manager.get_icon("git-pull-request", size=18))
        self.push_btn.setMinimumSize(85, 36)
        self.push_btn.setMaximumSize(110, 36)
        self.push_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.push_btn.setToolTip("Subir tus cambios al servidor")
        self.push_btn.clicked.connect(self.do_push)
        layout.addWidget(self.push_btn)
        
        self.fetch_btn = QPushButton(" Fetch")
        self.fetch_btn.setIcon(self.icon_manager.get_icon("git-diff", size=18))
        self.fetch_btn.setMinimumSize(85, 36)
        self.fetch_btn.setMaximumSize(110, 36)
        self.fetch_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.fetch_btn.setToolTip("Actualizar información sin descargar")
        self.fetch_btn.clicked.connect(self.do_fetch)
        layout.addWidget(self.fetch_btn)
        
        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(self.icon_manager.get_icon("git-commit", size=20))
        self.refresh_btn.setFixedSize(36, 36)
        self.refresh_btn.setToolTip("Actualizar estado del repositorio")
        self.refresh_btn.clicked.connect(self.refresh_status)
        layout.addWidget(self.refresh_btn)
        
    def create_left_panel(self):
        widget = QWidget()
        widget.setStyleSheet("background-color: #252526;")
        widget.setMinimumWidth(300)
        widget.setMaximumWidth(600)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        changes_header = self.create_section_header("CAMBIOS", "Archivos modificados en tu repositorio", "file-text")
        layout.addWidget(changes_header)
        
        changes_container = QWidget()
        changes_container.setStyleSheet("background-color: #1e1e1e; padding: 10px;")
        changes_layout = QVBoxLayout(changes_container)
        changes_layout.setContentsMargins(10, 10, 10, 10)
        
        self.changes_list = QListWidget()
        self.changes_list.setMinimumHeight(200)
        self.changes_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 5px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 2px;
                border-left: 3px solid transparent;
            }
            QListWidget::item:hover {
                background-color: #2d2d2d;
            }
            QListWidget::item:selected {
                background-color: #094771;
                border-left-color: #007acc;
            }
        """)
        self.changes_list.itemClicked.connect(self.on_file_selected)
        self.changes_list.itemDoubleClicked.connect(self.on_change_double_clicked)
        changes_layout.addWidget(self.changes_list)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)
        
        self.stage_all_btn = QPushButton(" Agregar Todo")
        self.stage_all_btn.setIcon(self.icon_manager.get_icon("folder-plus", size=16))
        self.stage_all_btn.setToolTip("Agregar todos los cambios")
        self.stage_all_btn.clicked.connect(self.stage_all)
        btn_layout.addWidget(self.stage_all_btn)
        
        self.stage_btn = QPushButton(" Agregar")
        self.stage_btn.setIcon(self.icon_manager.get_icon("file-plus", size=16))
        self.stage_btn.setToolTip("Agregar archivo seleccionado")
        self.stage_btn.clicked.connect(self.stage_selected)
        btn_layout.addWidget(self.stage_btn)
        
        self.unstage_btn = QPushButton(" Quitar")
        self.unstage_btn.setIcon(self.icon_manager.get_icon("file-minus", size=16))
        self.unstage_btn.setToolTip("Quitar archivo del staging")
        self.unstage_btn.clicked.connect(self.unstage_selected)
        btn_layout.addWidget(self.unstage_btn)
        
        changes_layout.addLayout(btn_layout)
        layout.addWidget(changes_container)
        
        commit_header = self.create_section_header("COMMIT", "Guardar cambios con un mensaje descriptivo", "git-commit")
        layout.addWidget(commit_header)
        
        commit_container = QWidget()
        commit_container.setStyleSheet("background-color: #1e1e1e; padding: 10px;")
        commit_layout = QVBoxLayout(commit_container)
        commit_layout.setContentsMargins(10, 10, 10, 10)
        
        self.commit_message = QTextEdit()
        self.commit_message.setPlaceholderText("Describe tus cambios...")
        self.commit_message.setMaximumHeight(100)
        self.commit_message.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.commit_message.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
                color: #cccccc;
            }
            QTextEdit:focus {
                border-color: #007acc;
            }
        """)
        commit_layout.addWidget(self.commit_message)
        
        self.commit_btn = QPushButton(" Hacer Commit y Guardar")
        self.commit_btn.setIcon(self.icon_manager.get_icon("git-commit", size=18))
        self.commit_btn.setMinimumHeight(40)
        self.commit_btn.setStyleSheet("""
            QPushButton {
                background-color: #16825d;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1a9d6f;
            }
            QPushButton:pressed {
                background-color: #136d4d;
            }
        """)
        self.commit_btn.setToolTip("Guardar todos los cambios preparados con este mensaje")
        self.commit_btn.clicked.connect(self.do_commit)
        commit_layout.addWidget(self.commit_btn)
        
        layout.addWidget(commit_container)
        
        lfs_header = self.create_section_header("GIT LFS", "Manejo de archivos grandes de Unreal Engine", "files")
        layout.addWidget(lfs_header)
        
        lfs_container = QWidget()
        lfs_container.setStyleSheet("background-color: #1e1e1e; padding: 10px;")
        lfs_layout = QVBoxLayout(lfs_container)
        lfs_layout.setContentsMargins(10, 10, 10, 10)
        
        status_widget = QWidget()
        status_widget.setStyleSheet("background-color: #2d2d2d; border-radius: 4px; padding: 8px;")
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(10, 8, 10, 8)
        
        status_icon = QLabel()
        status_icon.setPixmap(self.icon_manager.get_pixmap("info", 16))
        status_layout.addWidget(status_icon)
        
        self.lfs_status_label = QLabel("Estado: No inicializado")
        self.lfs_status_label.setStyleSheet("color: #cccccc; font-weight: bold;")
        status_layout.addWidget(self.lfs_status_label)
        status_layout.addStretch()
        
        lfs_layout.addWidget(status_widget)
        lfs_layout.addSpacing(10)
        
        lfs_btn_layout = QHBoxLayout()
        lfs_btn_layout.setSpacing(5)
        
        self.lfs_install_btn = QPushButton(" Instalar")
        self.lfs_install_btn.setIcon(self.icon_manager.get_icon("download", size=16))
        self.lfs_install_btn.setToolTip("Instalar Git LFS en este repositorio")
        self.lfs_install_btn.clicked.connect(self.install_lfs)
        lfs_btn_layout.addWidget(self.lfs_install_btn)
        
        self.lfs_track_btn = QPushButton(" Config Unreal")
        self.lfs_track_btn.setIcon(self.icon_manager.get_icon("file-code", size=16))
        self.lfs_track_btn.setToolTip("Configurar LFS para archivos de Unreal Engine")
        self.lfs_track_btn.clicked.connect(self.track_unreal_files)
        lfs_btn_layout.addWidget(self.lfs_track_btn)
        
        lfs_layout.addLayout(lfs_btn_layout)
        
        self.lfs_pull_btn = QPushButton(" Descargar Archivos LFS")
        self.lfs_pull_btn.setIcon(self.icon_manager.get_icon("download", size=16))
        self.lfs_pull_btn.setToolTip("Descargar archivos grandes rastreados por LFS")
        self.lfs_pull_btn.clicked.connect(self.do_lfs_pull)
        lfs_layout.addWidget(self.lfs_pull_btn)
        
        layout.addWidget(lfs_container)
        
        layout.addStretch()
        
        self.apply_left_panel_styles()
        
        return widget
        
    def create_section_header(self, title, description, icon_name=None):
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-bottom: 1px solid #3d3d3d;
            }
        """)
        header.setMinimumHeight(50)
        header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(10)
        
        if icon_name:
            icon_label = QLabel()
            icon_label.setPixmap(self.icon_manager.get_pixmap(icon_name, size=20))
            icon_label.setFixedSize(24, 24)
            layout.addWidget(icon_label)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        text_layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #888888; font-size: 10px;")
        text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout)
        
        return header
    
    def create_right_panel(self):
        widget = QWidget()
        widget.setStyleSheet("background-color: #1e1e1e;")
        widget.setMinimumWidth(400)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        info_header = self.create_section_header("INFORMACIÓN", "Detalles del repositorio actual", "folder")
        layout.addWidget(info_header)
        
        info_container = QWidget()
        info_container.setStyleSheet("background-color: #252526; padding: 15px;")
        info_container.setMinimumHeight(100)
        info_container.setMaximumHeight(150)
        info_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        info_layout = QVBoxLayout(info_container)
        
        self.repo_info = QLabel("No hay repositorio cargado")
        self.repo_info.setWordWrap(True)
        self.repo_info.setStyleSheet("color: #cccccc; line-height: 1.6;")
        info_layout.addWidget(self.repo_info)
        
        info_group = QWidget()
        info_group_layout = QVBoxLayout(info_group)
        info_group_layout.setContentsMargins(0, 0, 0, 0)
        info_group_layout.setSpacing(0)
        info_group_layout.addWidget(info_header)
        info_group_layout.addWidget(info_container)
        
        diff_header = self.create_section_header("DIFERENCIAS", "Cambios en el archivo seleccionado", "git-diff")
        
        diff_container = QWidget()
        diff_container.setStyleSheet("background-color: #1e1e1e; padding: 10px;")
        diff_layout = QVBoxLayout(diff_container)
        diff_layout.setContentsMargins(10, 10, 10, 10)
        
        self.diff_view = QTextEdit()
        self.diff_view.setReadOnly(True)
        self.diff_view.setFont(QFont("Courier New", 10))
        self.diff_view.setPlaceholderText("Selecciona un archivo para ver sus cambios...")
        self.diff_view.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.6;
                color: #cccccc;
            }
        """)
        diff_layout.addWidget(self.diff_view)
        
        diff_group = QWidget()
        diff_group_layout = QVBoxLayout(diff_group)
        diff_group_layout.setContentsMargins(0, 0, 0, 0)
        diff_group_layout.setSpacing(0)
        diff_group_layout.addWidget(diff_header)
        diff_group_layout.addWidget(diff_container)
        
        history_header = self.create_section_header("HISTORIAL", "Últimos commits del repositorio", "git-commit")
        
        history_container = QWidget()
        history_container.setStyleSheet("background-color: #1e1e1e; padding: 10px;")
        history_layout = QVBoxLayout(history_container)
        history_layout.setContentsMargins(10, 10, 10, 10)
        
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 5px;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }
            QListWidget::item {
                padding: 12px 10px;
                border-left: 3px solid transparent;
                border-radius: 4px;
                margin: 3px 0;
            }
            QListWidget::item:hover {
                background-color: #2d2d2d;
                border-left-color: #4ec9b0;
            }
            QListWidget::item:selected {
                background-color: #094771;
                border-left-color: #007acc;
            }
        """)
        self.history_list.itemClicked.connect(self.on_commit_selected)
        self.history_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self.show_commit_context_menu)
        history_layout.addWidget(self.history_list)
        
        history_group = QWidget()
        history_group_layout = QVBoxLayout(history_group)
        history_group_layout.setContentsMargins(0, 0, 0, 0)
        history_group_layout.setSpacing(0)
        history_group_layout.addWidget(history_header)
        history_group_layout.addWidget(history_container)
        
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.setHandleWidth(3)
        right_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #3d3d3d;
            }
            QSplitter::handle:hover {
                background-color: #007acc;
            }
        """)
        right_splitter.addWidget(info_group)
        right_splitter.addWidget(diff_group)
        right_splitter.addWidget(history_group)
        right_splitter.setStretchFactor(0, 1)
        right_splitter.setStretchFactor(1, 3)
        right_splitter.setStretchFactor(2, 3)
        right_splitter.setSizes([150, 400, 400])
        
        layout.addWidget(right_splitter)
        
        self.apply_right_panel_styles()
        
        return widget
        
    def show_home_view(self):
        self.stacked_widget.setCurrentWidget(self.home_view)
        
    def show_repo_view(self):
        self.stacked_widget.setCurrentWidget(self.repo_view)
        
    def on_home_open_repo(self):
        if self.parent_window:
            self.parent_window.open_repository()
            
    def on_home_clone_repo(self):
        if self.parent_window:
            self.parent_window.clone_repository()
    
    def load_repository(self, path):
        self.repo_path = path
        self.git_manager.set_repository(path)
        
        if self.settings_manager:
            repo_name = os.path.basename(path)
            self.settings_manager.add_recent_repo(path, repo_name)
            self.home_view.refresh_recent_repos()
        
        self.show_repo_view()
        self.refresh_status()
        self.update_repo_info()
        self.load_history()
        self.check_lfs_status()
        self.detect_unreal_project()
        
    def refresh_status(self):
        if not self.repo_path:
            return
            
        branch = self.git_manager.get_current_branch()
        self.branch_button.setText(f" {branch}")
        self.branch_button.setIcon(self.icon_manager.get_icon("git-branch", size=16))
        
        status = self.git_manager.get_status()
        self.changes_list.clear()
        
        if not status:
            item = QListWidgetItem("  No hay cambios - Todo está actualizado")
            item.setIcon(self.icon_manager.get_icon("check", size=16))
            item.setForeground(QColor("#4ec9b0"))
            font = QFont("Segoe UI", 11)
            font.setBold(True)
            item.setFont(font)
            self.changes_list.addItem(item)
            return
        
        for file_path, state in status.items():
            if state in ["M", "A", "D"]:
                state_text = {"M": "Modificado", "A": "Agregado", "D": "Eliminado"}.get(state, state)
                state_color = {"M": "#dcdcaa", "A": "#4ec9b0", "D": "#f48771"}.get(state, "#cccccc")
                
                item = QListWidgetItem(f"  {file_path}")
                if state == "M":
                    item.setIcon(self.icon_manager.get_icon("file-text", size=16))
                elif state == "A":
                    item.setIcon(self.icon_manager.get_icon("file-plus", size=16))
                elif state == "D":
                    item.setIcon(self.icon_manager.get_icon("file-x", size=16))
                item.setToolTip(f"{state_text}: {file_path}")
                item.setForeground(QColor(state_color))
            else:
                item = QListWidgetItem(f"  {file_path}")
                item.setIcon(self.icon_manager.get_icon("file", size=16))
                item.setToolTip(f"Sin seguimiento: {file_path}")
                item.setForeground(QColor("#858585"))
            
            font = QFont("Consolas", 11)
            item.setFont(font)
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            self.changes_list.addItem(item)
            
    def on_change_double_clicked(self, item):
        original_line = item.data(Qt.ItemDataRole.UserRole)
        if original_line:
            file_path = original_line.split(' ', 1)[1] if ' ' in original_line else original_line
            file_path = file_path.strip()
            diff = self.git_manager.get_file_diff(file_path)
            formatted_diff = self.format_diff(diff)
            self.diff_view.setHtml(formatted_diff)
        
    def stage_all(self):
        success, message = self.git_manager.stage_all()
        if success:
            self.refresh_status()
            QMessageBox.information(self, "Éxito", "Todos los archivos han sido agregados")
        else:
            QMessageBox.warning(self, "Error", message)
    
    def stage_selected(self):
        current_item = self.changes_list.currentItem()
        if current_item:
            file_path = current_item.data(Qt.ItemDataRole.UserRole)
            success, message = self.git_manager.stage_file(file_path)
            if success:
                self.refresh_status()
            else:
                QMessageBox.warning(self, "Error", message)
                
    def unstage_selected(self):
        current_item = self.changes_list.currentItem()
        if current_item:
            file_path = current_item.data(Qt.ItemDataRole.UserRole)
            success, message = self.git_manager.unstage_file(file_path)
            if success:
                self.refresh_status()
            else:
                QMessageBox.warning(self, "Error", message)
                
    def do_commit(self):
        message = self.commit_message.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "Error", "Debes escribir un mensaje para el commit")
            return
            
        success, result = self.git_manager.commit(message)
        if success:
            QMessageBox.information(self, "Éxito", "Commit realizado correctamente")
            self.commit_message.clear()
            self.refresh_status()
            self.load_history()
        else:
            QMessageBox.warning(self, "Error", result)
            
    def do_pull(self):
        success, message = self.git_manager.pull()
        if success:
            QMessageBox.information(self, "Éxito", "Pull completado")
            self.refresh_status()
            self.load_history()
        else:
            QMessageBox.warning(self, "Error", message)
            
    def do_push(self):
        success, message = self.git_manager.push()
        if success:
            QMessageBox.information(self, "Éxito", "Push completado")
        else:
            QMessageBox.warning(self, "Error", message)
            
    def do_fetch(self):
        success, message = self.git_manager.fetch()
        if success:
            QMessageBox.information(self, "Éxito", "Fetch completado")
            self.load_history()
        else:
            QMessageBox.warning(self, "Error", message)
            
    def update_repo_info(self):
        if not self.repo_path:
            return
            
        info = self.git_manager.get_repository_info()
        
        project_type = ""
        if self.git_manager.is_unreal_project():
            project_name = self.git_manager.get_unreal_project_name()
            if project_name:
                project_type = f"<b>Proyecto Unreal:</b> {project_name}<br>"
            else:
                project_type = "<b>Tipo:</b> Proyecto Unreal Engine<br>"
        
        info_text = f"""
{project_type}<b>Ruta:</b> {self.repo_path}<br>
<b>Rama actual:</b> {info.get('branch', 'N/A')}<br>
<b>Remoto:</b> {info.get('remote', 'N/A')}<br>
<b>Último commit:</b> {info.get('last_commit', 'N/A')}<br>
        """
        self.repo_info.setText(info_text)
        
    def load_history(self):
        if not self.repo_path:
            return
            
        self.history_list.clear()
        history = self.git_manager.get_commit_history(20)
        
        if not history:
            item = QListWidgetItem("  No hay commits todavía")
            item.setIcon(self.icon_manager.get_icon("folder", size=16))
            item.setForeground(QColor("#858585"))
            font = QFont("Segoe UI", 11)
            font.setBold(True)
            item.setFont(font)
            self.history_list.addItem(item)
            return
        
        for commit in history:
            commit_hash = commit['hash'][:7]
            message = commit['message']
            author = commit['author']
            author_email = commit.get('email', '')
            date = commit['date']
            
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, commit['hash'])
            item.setData(Qt.ItemDataRole.UserRole + 1, author_email)
            item.setToolTip(f"Commit: {commit['hash']}\nAutor: {author}\nEmail: {author_email}\nFecha: {date}\n\n{message}")
            
            item.setSizeHint(QSize(0, 70))
            
            avatar_icon = self.get_avatar_icon(author_email, author)
            if avatar_icon:
                item.setIcon(avatar_icon)
            
            display_text = f"{commit_hash} • {message}\n"
            display_text += f"{author}  •  {date}"
            item.setText(display_text)
            
            font = QFont("Segoe UI", 10)
            item.setFont(font)
            
            self.history_list.addItem(item)
            
            if author_email and author_email not in self.avatar_cache:
                self.download_gravatar(author_email, author)
            
    def on_commit_selected(self, item):
        commit_hash = item.data(Qt.ItemDataRole.UserRole)
        if commit_hash:
            diff = self.git_manager.get_commit_diff(commit_hash)
            formatted_diff = self.format_diff(diff)
            self.diff_view.setHtml(formatted_diff)
    
    def on_file_selected(self, item):
        original_line = item.data(Qt.ItemDataRole.UserRole)
        if original_line:
            file_path = original_line.split(' ', 1)[1] if ' ' in original_line else original_line
            file_path = file_path.strip()
            diff = self.git_manager.get_file_diff(file_path)
            formatted_diff = self.format_diff(diff)
            self.diff_view.setHtml(formatted_diff)
    
    def format_diff(self, diff_text):
        lines = diff_text.split('\n')
        html = '<pre style="margin: 0; line-height: 1.6;">'
        
        for line in lines:
            if line.startswith('diff --git'):
                html += f'<span style="color: #569cd6; font-weight: bold;">{line}</span>\n'
            elif line.startswith('index ') or line.startswith('---') or line.startswith('+++'):
                html += f'<span style="color: #858585;">{line}</span>\n'
            elif line.startswith('@@'):
                html += f'<span style="color: #c586c0; font-weight: bold;">{line}</span>\n'
            elif line.startswith('+') and not line.startswith('+++'):
                html += f'<span style="background-color: #1a3d1a; color: #4ec9b0;">{line}</span>\n'
            elif line.startswith('-') and not line.startswith('---'):
                html += f'<span style="background-color: #3d1a1a; color: #f48771;">{line}</span>\n'
            else:
                html += f'<span style="color: #cccccc;">{line}</span>\n'
        
        html += '</pre>'
        return html
    
    def show_commit_context_menu(self, position):
        item = self.history_list.itemAt(position)
        if not item:
            return
        
        commit_hash = item.data(Qt.ItemDataRole.UserRole)
        if not commit_hash:
            return
        
        commit_text = item.text().split('\n')[0].replace('🔹 ', '').split(' - ', 1)
        commit_msg = commit_text[1] if len(commit_text) > 1 else "Sin mensaje"
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #094771;
            }
        """)
        
        create_branch_action = QAction("  Crear rama desde aquí", self)
        create_branch_action.setIcon(self.icon_manager.get_icon("git-branch", size=16))
        create_branch_action.triggered.connect(lambda: self.create_branch_from_commit_quick(commit_hash))
        menu.addAction(create_branch_action)
        
        menu.addSeparator()
        
        reset_soft_action = QAction("  Reset Soft (mantener cambios)", self)
        reset_soft_action.setIcon(self.icon_manager.get_icon("git-commit", size=16))
        reset_soft_action.triggered.connect(lambda: self.reset_commit_quick(commit_hash, 'soft'))
        menu.addAction(reset_soft_action)
        
        reset_mixed_action = QAction("  Reset Mixed", self)
        reset_mixed_action.setIcon(self.icon_manager.get_icon("arrows-clockwise", size=16))
        reset_mixed_action.triggered.connect(lambda: self.reset_commit_quick(commit_hash, 'mixed'))
        menu.addAction(reset_mixed_action)
        
        reset_hard_action = QAction("  Reset Hard (descartar todo)", self)
        reset_hard_action.setIcon(self.icon_manager.get_icon("x-square", size=16))
        reset_hard_action.triggered.connect(lambda: self.reset_commit_quick(commit_hash, 'hard'))
        menu.addAction(reset_hard_action)
        
        menu.addSeparator()
        
        checkout_action = QAction("  Ver este commit", self)
        checkout_action.setIcon(self.icon_manager.get_icon("sign-in", size=16))
        checkout_action.triggered.connect(lambda: self.checkout_commit_quick(commit_hash))
        menu.addAction(checkout_action)
        
        copy_hash_action = QAction("  Copiar hash", self)
        copy_hash_action.setIcon(self.icon_manager.get_icon("link", size=16))
        copy_hash_action.triggered.connect(lambda: self.copy_commit_hash(commit_hash))
        menu.addAction(copy_hash_action)
        
        menu.exec(self.history_list.mapToGlobal(position))
    
    def create_branch_from_commit_quick(self, commit_hash):
        branch_name, ok = QInputDialog.getText(
            self,
            "Crear Rama",
            f"Nombre de la nueva rama desde commit {commit_hash[:7]}:",
            QLineEdit.EchoMode.Normal,
            ""
        )
        
        if ok and branch_name:
            success, message = self.git_manager.create_branch(branch_name, commit_hash)
            if success:
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Rama '{branch_name}' creada desde el commit {commit_hash[:7]}"
                )
                self.refresh_status()
            else:
                QMessageBox.warning(self, "Error", f"No se pudo crear la rama:\n{message}")
    
    def reset_commit_quick(self, commit_hash, mode):
        mode_names = {
            'soft': 'Soft (mantener cambios)',
            'mixed': 'Mixed (descartar staging)',
            'hard': 'Hard (descartar todo)'
        }
        
        warning = ""
        if mode == 'hard':
            warning = "\n\n⚠ ADVERTENCIA: Perderás todos los cambios no guardados!"
        
        reply = QMessageBox.question(
            self,
            "Confirmar Reset",
            f"¿Hacer reset {mode_names[mode]} al commit {commit_hash[:7]}?{warning}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.git_manager.reset_to_commit(commit_hash, mode)
            if success:
                QMessageBox.information(self, "Éxito", f"Reset {mode} completado")
                self.refresh_status()
                self.load_history()
                self.update_repo_info()
            else:
                QMessageBox.warning(self, "Error", f"Error en reset:\n{message}")
    
    def checkout_commit_quick(self, commit_hash):
        reply = QMessageBox.question(
            self,
            "Confirmar Checkout",
            f"¿Ver el commit {commit_hash[:7]}?\n\n" +
            "Estarás en modo 'detached HEAD'.\n" +
            "Para guardar cambios, crea una nueva rama.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.git_manager.checkout_commit(commit_hash)
            if success:
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Ahora estás viendo el commit {commit_hash[:7]}\n\n" +
                    "Usa el menú de ramas para volver a una rama normal."
                )
                self.refresh_status()
                self.update_repo_info()
            else:
                QMessageBox.warning(self, "Error", f"Error:\n{message}")
    
    def copy_commit_hash(self, commit_hash):
        clipboard = QApplication.clipboard()
        clipboard.setText(commit_hash)
        self.statusBar().showMessage(f"Hash copiado: {commit_hash[:7]}", 2000) if hasattr(self, 'statusBar') else None
    
    def show_branch_menu(self):
        branches = self.git_manager.get_all_branches()
        current_branch = self.git_manager.get_current_branch()
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                padding: 5px;
            }
            QMenu::item {
                padding: 10px 30px;
                border-radius: 3px;
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: #094771;
            }
            QMenu::separator {
                height: 1px;
                background-color: #3d3d3d;
                margin: 5px 0;
            }
        """)
        
        header = QAction("  Cambiar Rama", self)
        header.setIcon(self.icon_manager.get_icon("git-branch", size=16))
        header.setEnabled(False)
        menu.addAction(header)
        menu.addSeparator()
        
        local_branches = [b for b in branches if not b['is_remote']]
        remote_branches = [b for b in branches if b['is_remote']]
        
        for branch in local_branches:
            name = branch['name']
            action = QAction(f"  {name}", self)
            if branch['is_current']:
                action.setIcon(self.icon_manager.get_icon("check", size=16))
            else:
                action.setIcon(self.icon_manager.get_icon("git-branch", size=16))
            
            if branch['is_current']:
                action.setEnabled(False)
            else:
                action.triggered.connect(lambda checked, b=name: self.switch_branch_quick(b))
            
            menu.addAction(action)
        
        if remote_branches:
            menu.addSeparator()
            remote_header = QAction("  Ramas Remotas", self)
            remote_header.setIcon(self.icon_manager.get_icon("share-network", size=16))
            remote_header.setEnabled(False)
            menu.addAction(remote_header)
            
            for branch in remote_branches[:5]:
                name = branch['name']
                action = QAction(f"  {name}", self)
                action.setIcon(self.icon_manager.get_icon("share-network", size=16))
                action.triggered.connect(lambda checked, b=name: self.switch_branch_quick(b))
                menu.addAction(action)
        
        menu.addSeparator()
        
        new_branch_action = QAction("  Nueva Rama...", self)
        new_branch_action.setIcon(self.icon_manager.get_icon("plus-circle", size=16))
        new_branch_action.triggered.connect(self.create_new_branch_quick)
        menu.addAction(new_branch_action)
        
        manage_action = QAction("  Administrar Ramas...", self)
        manage_action.setIcon(self.icon_manager.get_icon("gear-six", size=16))
        manage_action.triggered.connect(self.open_branch_manager)
        menu.addAction(manage_action)
        
        menu.exec(QCursor.pos())
    
    def switch_branch_quick(self, branch_name):
        clean_name = branch_name.replace('remotes/origin/', '')
        
        reply = QMessageBox.question(
            self,
            "Cambiar Rama",
            f"¿Cambiar a la rama '{clean_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.git_manager.switch_branch(branch_name)
            if success:
                self.refresh_status()
                self.load_history()
                self.update_repo_info()
            else:
                QMessageBox.warning(self, "Error", f"No se pudo cambiar de rama:\n{message}")
    
    def create_new_branch_quick(self):
        branch_name, ok = QInputDialog.getText(
            self,
            "Nueva Rama",
            "Nombre de la nueva rama:",
            QLineEdit.EchoMode.Normal,
            ""
        )
        
        if ok and branch_name:
            success, message = self.git_manager.create_branch(branch_name)
            if success:
                reply = QMessageBox.question(
                    self,
                    "Rama Creada",
                    f"Rama '{branch_name}' creada correctamente.\n\n¿Cambiar a esta rama ahora?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.git_manager.switch_branch(branch_name)
                
                self.refresh_status()
                self.load_history()
                self.update_repo_info()
            else:
                QMessageBox.warning(self, "Error", f"No se pudo crear la rama:\n{message}")
    
    def on_commit_double_clicked(self, item):
        commit_hash = item.data(Qt.ItemDataRole.UserRole)
        if not commit_hash:
            return
        
        from ui.branch_manager import CommitActionsDialog
        commit_text = item.text().split('\n')[0].replace('🔹 ', '').split(' - ', 1)
        commit_msg = commit_text[1] if len(commit_text) > 1 else "Sin mensaje"
        
        dialog = CommitActionsDialog(self.git_manager, commit_hash, commit_msg, self)
        if dialog.exec():
            self.refresh_status()
            self.load_history()
            self.update_repo_info()
    
    def open_branch_manager(self):
        from ui.branch_manager import BranchManagerDialog
        dialog = BranchManagerDialog(self.git_manager, self)
        if dialog.exec():
            self.refresh_status()
            self.update_repo_info()
    
    def get_avatar_icon(self, email, author_name):
        if email in self.avatar_cache:
            return self.avatar_cache[email]
        
        return self.create_initial_avatar(author_name)
    
    def create_initial_avatar(self, author_name):
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        colors = ['#4ec9b0', '#007acc', '#c586c0', '#dcdcaa', '#ce9178', '#4fc1ff', '#b5cea8']
        color_index = sum(ord(c) for c in author_name) % len(colors)
        color = QColor(colors[color_index])
        
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 48, 48)
        
        initials = self.get_initials(author_name)
        painter.setPen(QColor('#ffffff'))
        font = QFont('Arial', 16, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(0, 0, 48, 48, Qt.AlignmentFlag.AlignCenter, initials)
        
        painter.end()
        
        return QIcon(pixmap)
    
    def get_initials(self, name):
        parts = name.strip().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        elif len(parts) == 1 and len(parts[0]) > 0:
            return parts[0][0].upper()
        return "?"
    
    def download_gravatar(self, email, author_name):
        if not email or '@' not in email:
            return
        
        email_hash = hashlib.md5(email.lower().encode()).hexdigest()
        url = f"https://www.gravatar.com/avatar/{email_hash}?s=48&d=404"
        
        request = QNetworkRequest(QUrl(url))
        request.setAttribute(QNetworkRequest.Attribute.User, (email, author_name))
        self.network_manager.get(request)
    
    def on_avatar_downloaded(self, reply):
        if reply.error() == reply.NetworkError.NoError:
            email, author_name = reply.request().attribute(QNetworkRequest.Attribute.User)
            image_data = reply.readAll()
            
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                pixmap = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, 
                                      Qt.TransformationMode.SmoothTransformation)
                
                rounded_pixmap = QPixmap(48, 48)
                rounded_pixmap.fill(Qt.GlobalColor.transparent)
                
                painter = QPainter(rounded_pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setBrush(QBrush(pixmap))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(0, 0, 48, 48)
                painter.end()
                
                icon = QIcon(rounded_pixmap)
                self.avatar_cache[email] = icon
                
                for i in range(self.history_list.count()):
                    item = self.history_list.item(i)
                    item_email = item.data(Qt.ItemDataRole.UserRole + 1)
                    if item_email == email:
                        item.setIcon(icon)
        
        reply.deleteLater()
    
    def detect_unreal_project(self):
        if not self.repo_path:
            return
        
        if self.git_manager.is_unreal_project():
            project_name = self.git_manager.get_unreal_project_name()
            if project_name:
                QMessageBox.information(
                    self,
                    "Proyecto de Unreal Engine Detectado",
                    f"Se ha detectado un proyecto de Unreal Engine:\n\n"
                    f"Proyecto: {project_name}\n\n"
                    f"ℹ️ Recomendación: Asegúrate de tener Git LFS configurado para archivos .uasset, .umap, etc."
                )
            else:
                QMessageBox.information(
                    self,
                    "Proyecto de Unreal Engine Detectado",
                    f"Se ha detectado un proyecto de Unreal Engine.\n\n"
                    f"ℹ️ Recomendación: Configura Git LFS en la sección correspondiente."
                )
        
    def check_lfs_status(self):
        if not self.repo_path:
            return
            
        if self.git_manager.is_lfs_installed():
            self.lfs_status_label.setText("Estado: LFS instalado")
        else:
            self.lfs_status_label.setText("Estado: LFS no instalado")
            
    def install_lfs(self):
        success, message = self.git_manager.install_lfs()
        if success:
            QMessageBox.information(self, "Éxito", "Git LFS instalado correctamente")
            self.check_lfs_status()
        else:
            QMessageBox.warning(self, "Error", message)
            
    def track_unreal_files(self):
        success, message = self.git_manager.track_unreal_files()
        if success:
            QMessageBox.information(self, "Éxito", "Archivos de Unreal Engine configurados para LFS")
        else:
            QMessageBox.warning(self, "Error", message)
            
    def do_lfs_pull(self):
        success, message = self.git_manager.lfs_pull()
        if success:
            QMessageBox.information(self, "Éxito", "LFS Pull completado")
        else:
            QMessageBox.warning(self, "Error", message)
            
    def clone_repository(self, url, path):
        self.progress_dialog = QProgressDialog("Clonando repositorio...", "Cancelar", 0, 0, self)
        self.progress_dialog.setWindowTitle("Clonando")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()
        
        self.clone_thread = CloneThread(self.git_manager, url, path)
        self.clone_thread.finished.connect(self.on_clone_finished)
        self.clone_thread.start()
        
    def on_clone_finished(self, success, message):
        self.progress_dialog.close()
        
        if success:
            repo_path = message
            self.load_repository(repo_path)
            
            if self.parent_window:
                tab_widget = self.parent_window.tab_widget
                index = tab_widget.indexOf(self)
                repo_name = os.path.basename(repo_path)
                tab_widget.setTabText(index, repo_name)
                
            QMessageBox.information(self, "Éxito", f"Repositorio clonado en:\n{repo_path}")
        else:
            QMessageBox.warning(self, "Error", f"Error al clonar:\n{message}")
            
    def apply_left_panel_styles(self):
        style = """
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 12px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0d5a8f;
            }
            QPushButton:disabled {
                background-color: #3d3d3d;
                color: #888888;
            }
            QListWidget {
                background-color: #1e1e1e;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 3px;
                margin: 2px 0;
            }
            QListWidget::item:selected {
                background-color: #094771;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #2d2d2d;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
                line-height: 1.4;
            }
        """
        self.setStyleSheet(style)
        
    def apply_right_panel_styles(self):
        diff_style = """
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                line-height: 1.5;
            }
        """
        self.diff_view.setStyleSheet(diff_style)
        
        history_style = """
            QListWidget {
                background-color: #1e1e1e;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #2d2d2d;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #094771;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #2d2d2d;
            }
        """
        self.history_list.setStyleSheet(history_style)

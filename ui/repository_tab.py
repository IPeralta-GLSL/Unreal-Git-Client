from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                             QListWidget, QTextEdit, QPushButton, QLabel,
                             QGroupBox, QLineEdit, QMessageBox, QListWidgetItem,
                             QProgressDialog, QScrollArea, QFrame, QCheckBox, QStackedWidget,
                             QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon
from ui.home_view import HomeView
import os

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
    def __init__(self, git_manager, parent_window=None):
        super().__init__()
        self.git_manager = git_manager
        self.repo_path = None
        self.parent_window = parent_window
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.stacked_widget = QStackedWidget()
        
        self.home_view = HomeView()
        self.home_view.open_repo_requested.connect(self.on_home_open_repo)
        self.home_view.clone_repo_requested.connect(self.on_home_clone_repo)
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
        self.top_bar.setMinimumHeight(60)
        self.top_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.top_bar.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-bottom: 2px solid #0e639c;
            }
        """)
        
        layout = QHBoxLayout(self.top_bar)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)
        
        branch_container = QWidget()
        branch_layout = QVBoxLayout(branch_container)
        branch_layout.setContentsMargins(0, 0, 0, 0)
        branch_layout.setSpacing(2)
        
        branch_title = QLabel("RAMA ACTUAL")
        branch_title.setStyleSheet("color: #888888; font-size: 10px; font-weight: bold;")
        branch_layout.addWidget(branch_title)
        
        self.branch_label = QLabel("main")
        self.branch_label.setWordWrap(True)
        self.branch_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #4ec9b0;")
        branch_layout.addWidget(self.branch_label)
        
        layout.addWidget(branch_container)
        layout.addStretch()
        
        sync_layout = QHBoxLayout()
        sync_layout.setSpacing(8)
        
        self.pull_btn = QPushButton("⬇ Pull")
        self.pull_btn.setMinimumSize(80, 38)
        self.pull_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.pull_btn.setToolTip("Descargar cambios del servidor")
        self.pull_btn.clicked.connect(self.do_pull)
        sync_layout.addWidget(self.pull_btn)
        
        self.push_btn = QPushButton("⬆ Push")
        self.push_btn.setMinimumSize(80, 38)
        self.push_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.push_btn.setToolTip("Subir tus cambios al servidor")
        self.push_btn.clicked.connect(self.do_push)
        sync_layout.addWidget(self.push_btn)
        
        self.fetch_btn = QPushButton("🔍 Fetch")
        self.fetch_btn.setMinimumSize(80, 38)
        self.fetch_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.fetch_btn.setToolTip("Actualizar información sin descargar")
        self.fetch_btn.clicked.connect(self.do_fetch)
        sync_layout.addWidget(self.fetch_btn)
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(38, 38)
        self.refresh_btn.setToolTip("Actualizar estado del repositorio")
        self.refresh_btn.clicked.connect(self.refresh_status)
        sync_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(sync_layout)
        
    def create_left_panel(self):
        widget = QWidget()
        widget.setStyleSheet("background-color: #252526;")
        widget.setMinimumWidth(280)
        widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        changes_header = self.create_section_header("📝 CAMBIOS", "Archivos modificados en tu repositorio")
        layout.addWidget(changes_header)
        
        changes_container = QWidget()
        changes_container.setStyleSheet("background-color: #1e1e1e; padding: 10px;")
        changes_layout = QVBoxLayout(changes_container)
        changes_layout.setContentsMargins(10, 10, 10, 10)
        
        self.changes_list = QListWidget()
        self.changes_list.setMinimumHeight(200)
        self.changes_list.itemClicked.connect(self.on_file_selected)
        changes_layout.addWidget(self.changes_list)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)
        
        self.stage_all_btn = QPushButton("➕ Agregar Todo")
        self.stage_all_btn.setToolTip("Agregar todos los cambios")
        self.stage_all_btn.clicked.connect(self.stage_all)
        btn_layout.addWidget(self.stage_all_btn)
        
        self.stage_btn = QPushButton("➕ Agregar")
        self.stage_btn.setToolTip("Agregar archivo seleccionado")
        self.stage_btn.clicked.connect(self.stage_selected)
        btn_layout.addWidget(self.stage_btn)
        
        self.unstage_btn = QPushButton("➖ Quitar")
        self.unstage_btn.setToolTip("Quitar archivo del staging")
        self.unstage_btn.clicked.connect(self.unstage_selected)
        btn_layout.addWidget(self.unstage_btn)
        
        changes_layout.addLayout(btn_layout)
        layout.addWidget(changes_container)
        
        commit_header = self.create_section_header("💬 COMMIT", "Guardar cambios con un mensaje descriptivo")
        layout.addWidget(commit_header)
        
        commit_container = QWidget()
        commit_container.setStyleSheet("background-color: #1e1e1e; padding: 10px;")
        commit_layout = QVBoxLayout(commit_container)
        commit_layout.setContentsMargins(10, 10, 10, 10)
        
        self.commit_message = QTextEdit()
        self.commit_message.setPlaceholderText("Escribe un mensaje descriptivo de tus cambios...\n\nEjemplo: 'Añadido nuevo nivel con terreno y vegetación'")
        self.commit_message.setMinimumHeight(80)
        self.commit_message.setMaximumHeight(120)
        commit_layout.addWidget(self.commit_message)
        
        self.commit_btn = QPushButton("✅ Hacer Commit y Guardar")
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
        
        lfs_header = self.create_section_header("� GIT LFS", "Manejo de archivos grandes de Unreal Engine")
        layout.addWidget(lfs_header)
        
        lfs_container = QWidget()
        lfs_container.setStyleSheet("background-color: #1e1e1e; padding: 10px;")
        lfs_layout = QVBoxLayout(lfs_container)
        lfs_layout.setContentsMargins(10, 10, 10, 10)
        
        status_widget = QWidget()
        status_widget.setStyleSheet("background-color: #2d2d2d; border-radius: 4px; padding: 8px;")
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(10, 8, 10, 8)
        
        status_icon = QLabel("ℹ️")
        status_icon.setStyleSheet("font-size: 16px;")
        status_layout.addWidget(status_icon)
        
        self.lfs_status_label = QLabel("Estado: No inicializado")
        self.lfs_status_label.setStyleSheet("color: #cccccc; font-weight: bold;")
        status_layout.addWidget(self.lfs_status_label)
        status_layout.addStretch()
        
        lfs_layout.addWidget(status_widget)
        lfs_layout.addSpacing(10)
        
        lfs_btn_layout = QHBoxLayout()
        lfs_btn_layout.setSpacing(5)
        
        self.lfs_install_btn = QPushButton("🔧 Instalar")
        self.lfs_install_btn.setToolTip("Instalar Git LFS en este repositorio")
        self.lfs_install_btn.clicked.connect(self.install_lfs)
        lfs_btn_layout.addWidget(self.lfs_install_btn)
        
        self.lfs_track_btn = QPushButton("🎮 Config Unreal")
        self.lfs_track_btn.setToolTip("Configurar LFS para archivos de Unreal Engine")
        self.lfs_track_btn.clicked.connect(self.track_unreal_files)
        lfs_btn_layout.addWidget(self.lfs_track_btn)
        
        lfs_layout.addLayout(lfs_btn_layout)
        
        self.lfs_pull_btn = QPushButton("⬇️ Descargar Archivos LFS")
        self.lfs_pull_btn.setToolTip("Descargar archivos grandes rastreados por LFS")
        self.lfs_pull_btn.clicked.connect(self.do_lfs_pull)
        lfs_layout.addWidget(self.lfs_pull_btn)
        
        layout.addWidget(lfs_container)
        
        layout.addStretch()
        
        self.apply_left_panel_styles()
        
        return widget
        
    def create_section_header(self, title, description):
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-bottom: 1px solid #3d3d3d;
            }
        """)
        header.setMinimumHeight(50)
        header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        layout = QVBoxLayout(header)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(desc_label)
        
        return header
    
    def create_right_panel(self):
        widget = QWidget()
        widget.setStyleSheet("background-color: #1e1e1e;")
        widget.setMinimumWidth(400)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        info_header = self.create_section_header("ℹ️ INFORMACIÓN", "Detalles del repositorio actual")
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
        
        layout.addWidget(info_container)
        
        diff_header = self.create_section_header("📄 DIFERENCIAS", "Cambios en el archivo seleccionado")
        layout.addWidget(diff_header)
        
        diff_container = QWidget()
        diff_container.setStyleSheet("background-color: #1e1e1e; padding: 10px;")
        diff_layout = QVBoxLayout(diff_container)
        diff_layout.setContentsMargins(10, 10, 10, 10)
        
        self.diff_view = QTextEdit()
        self.diff_view.setReadOnly(True)
        self.diff_view.setFont(QFont("Courier New", 10))
        self.diff_view.setPlaceholderText("Selecciona un archivo para ver sus cambios...")
        diff_layout.addWidget(self.diff_view)
        
        layout.addWidget(diff_container, stretch=2)
        
        history_header = self.create_section_header("📜 HISTORIAL", "Últimos commits del repositorio")
        layout.addWidget(history_header)
        
        history_container = QWidget()
        history_container.setStyleSheet("background-color: #1e1e1e; padding: 10px;")
        history_layout = QVBoxLayout(history_container)
        history_layout.setContentsMargins(10, 10, 10, 10)
        
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.on_commit_selected)
        history_layout.addWidget(self.history_list)
        
        layout.addWidget(history_container, stretch=1)
        
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
        self.show_repo_view()
        self.refresh_status()
        self.update_repo_info()
        self.load_history()
        self.check_lfs_status()
        
    def refresh_status(self):
        if not self.repo_path:
            return
            
        branch = self.git_manager.get_current_branch()
        self.branch_label.setText(branch)
        
        status = self.git_manager.get_status()
        self.changes_list.clear()
        
        if not status:
            item = QListWidgetItem("✅ No hay cambios - Todo está actualizado")
            item.setForeground(Qt.GlobalColor.green)
            self.changes_list.addItem(item)
            return
        
        for file_path, state in status.items():
            if state in ["M", "A", "D"]:
                state_icon = {"M": "✏️", "A": "➕", "D": "🗑️"}.get(state, "📝")
                state_text = {"M": "Modificado", "A": "Agregado", "D": "Eliminado"}.get(state, state)
                item_text = f"{state_icon} {state_text}: {file_path}"
                item = QListWidgetItem(item_text)
                item.setForeground(Qt.GlobalColor.green)
            else:
                item_text = f"❓ Sin preparar: {file_path}"
                item = QListWidgetItem(item_text)
                item.setForeground(Qt.GlobalColor.yellow)
            
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            self.changes_list.addItem(item)
            
    def on_file_selected(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        diff = self.git_manager.get_file_diff(file_path)
        self.diff_view.setPlainText(diff)
        
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
        info_text = f"""
<b>Ruta:</b> {self.repo_path}<br>
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
            item = QListWidgetItem("📭 No hay commits todavía")
            item.setForeground(Qt.GlobalColor.gray)
            self.history_list.addItem(item)
            return
        
        for commit in history:
            item_text = f"🔹 {commit['hash'][:7]} - {commit['message']}\n   👤 {commit['author']} • 📅 {commit['date']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, commit['hash'])
            self.history_list.addItem(item)
            
    def on_commit_selected(self, item):
        commit_hash = item.data(Qt.ItemDataRole.UserRole)
        diff = self.git_manager.get_commit_diff(commit_hash)
        self.diff_view.setPlainText(diff)
        
    def check_lfs_status(self):
        if not self.repo_path:
            return
            
        if self.git_manager.is_lfs_installed():
            self.lfs_status_label.setText("Estado: ✅ LFS instalado")
        else:
            self.lfs_status_label.setText("Estado: ❌ LFS no instalado")
            
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
                tab_widget.setTabText(index, f"📁 {repo_name}")
                
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

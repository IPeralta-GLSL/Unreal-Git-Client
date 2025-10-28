from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                             QListWidget, QTextEdit, QPushButton, QLabel,
                             QGroupBox, QLineEdit, QMessageBox, QListWidgetItem,
                             QProgressDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
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
    def __init__(self, git_manager):
        super().__init__()
        self.git_manager = git_manager
        self.repo_path = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([400, 1000])
        
        layout.addWidget(splitter)
        
    def create_left_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.branch_label = QLabel("Rama: main")
        self.branch_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #4ec9b0;")
        layout.addWidget(self.branch_label)
        
        changes_group = QGroupBox("📝 Cambios")
        changes_layout = QVBoxLayout()
        
        self.changes_list = QListWidget()
        self.changes_list.itemClicked.connect(self.on_file_selected)
        changes_layout.addWidget(self.changes_list)
        
        btn_layout = QHBoxLayout()
        self.stage_btn = QPushButton("➕ Agregar")
        self.stage_btn.clicked.connect(self.stage_selected)
        btn_layout.addWidget(self.stage_btn)
        
        self.unstage_btn = QPushButton("➖ Quitar")
        self.unstage_btn.clicked.connect(self.unstage_selected)
        btn_layout.addWidget(self.unstage_btn)
        
        changes_layout.addLayout(btn_layout)
        changes_group.setLayout(changes_layout)
        layout.addWidget(changes_group)
        
        commit_group = QGroupBox("💬 Commit")
        commit_layout = QVBoxLayout()
        
        self.commit_message = QTextEdit()
        self.commit_message.setPlaceholderText("Describe tus cambios aquí...")
        self.commit_message.setMaximumHeight(100)
        commit_layout.addWidget(self.commit_message)
        
        self.commit_btn = QPushButton("✅ Hacer Commit")
        self.commit_btn.clicked.connect(self.do_commit)
        commit_layout.addWidget(self.commit_btn)
        
        commit_group.setLayout(commit_layout)
        layout.addWidget(commit_group)
        
        sync_group = QGroupBox("🔄 Sincronización")
        sync_layout = QVBoxLayout()
        
        sync_btn_layout = QHBoxLayout()
        self.pull_btn = QPushButton("⬇️ Pull")
        self.pull_btn.clicked.connect(self.do_pull)
        sync_btn_layout.addWidget(self.pull_btn)
        
        self.push_btn = QPushButton("⬆️ Push")
        self.push_btn.clicked.connect(self.do_push)
        sync_btn_layout.addWidget(self.push_btn)
        
        sync_layout.addLayout(sync_btn_layout)
        
        self.fetch_btn = QPushButton("🔍 Fetch")
        self.fetch_btn.clicked.connect(self.do_fetch)
        sync_layout.addWidget(self.fetch_btn)
        
        sync_group.setLayout(sync_layout)
        layout.addWidget(sync_group)
        
        lfs_group = QGroupBox("📦 Git LFS")
        lfs_layout = QVBoxLayout()
        
        self.lfs_status_label = QLabel("Estado: No inicializado")
        lfs_layout.addWidget(self.lfs_status_label)
        
        lfs_btn_layout = QHBoxLayout()
        self.lfs_install_btn = QPushButton("Instalar LFS")
        self.lfs_install_btn.clicked.connect(self.install_lfs)
        lfs_btn_layout.addWidget(self.lfs_install_btn)
        
        self.lfs_track_btn = QPushButton("Trackear .uasset")
        self.lfs_track_btn.clicked.connect(self.track_unreal_files)
        lfs_btn_layout.addWidget(self.lfs_track_btn)
        
        lfs_layout.addLayout(lfs_btn_layout)
        
        self.lfs_pull_btn = QPushButton("⬇️ LFS Pull")
        self.lfs_pull_btn.clicked.connect(self.do_lfs_pull)
        lfs_layout.addWidget(self.lfs_pull_btn)
        
        lfs_group.setLayout(lfs_layout)
        layout.addWidget(lfs_group)
        
        self.refresh_btn = QPushButton("🔄 Actualizar")
        self.refresh_btn.clicked.connect(self.refresh_status)
        layout.addWidget(self.refresh_btn)
        
        layout.addStretch()
        
        self.apply_left_panel_styles()
        
        return widget
        
    def create_right_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info_group = QGroupBox("ℹ️ Información del Repositorio")
        info_layout = QVBoxLayout()
        
        self.repo_info = QLabel("No hay repositorio cargado")
        self.repo_info.setWordWrap(True)
        info_layout.addWidget(self.repo_info)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        diff_group = QGroupBox("📄 Diferencias")
        diff_layout = QVBoxLayout()
        
        self.diff_view = QTextEdit()
        self.diff_view.setReadOnly(True)
        self.diff_view.setFont(QFont("Courier New", 10))
        diff_layout.addWidget(self.diff_view)
        
        diff_group.setLayout(diff_layout)
        layout.addWidget(diff_group)
        
        history_group = QGroupBox("📜 Historial")
        history_layout = QVBoxLayout()
        
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.on_commit_selected)
        history_layout.addWidget(self.history_list)
        
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        self.apply_right_panel_styles()
        
        return widget
        
    def load_repository(self, path):
        self.repo_path = path
        self.git_manager.set_repository(path)
        self.refresh_status()
        self.update_repo_info()
        self.load_history()
        self.check_lfs_status()
        
    def refresh_status(self):
        if not self.repo_path:
            return
            
        branch = self.git_manager.get_current_branch()
        self.branch_label.setText(f"Rama: {branch}")
        
        status = self.git_manager.get_status()
        self.changes_list.clear()
        
        for file_path, state in status.items():
            item = QListWidgetItem(f"{state} {file_path}")
            if state in ["M", "A", "D"]:
                item.setForeground(Qt.GlobalColor.green)
            else:
                item.setForeground(Qt.GlobalColor.red)
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            self.changes_list.addItem(item)
            
    def on_file_selected(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        diff = self.git_manager.get_file_diff(file_path)
        self.diff_view.setPlainText(diff)
        
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
        
        for commit in history:
            item_text = f"{commit['hash'][:7]} - {commit['message']} ({commit['author']}, {commit['date']})"
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
            
            tab_widget = self.parent()
            if hasattr(tab_widget, 'setTabText'):
                index = tab_widget.indexOf(self)
                repo_name = os.path.basename(repo_path)
                tab_widget.setTabText(index, f"📁 {repo_name}")
                
            QMessageBox.information(self, "Éxito", f"Repositorio clonado en:\n{repo_path}")
        else:
            QMessageBox.warning(self, "Error", f"Error al clonar:\n{message}")
            
    def apply_left_panel_styles(self):
        style = """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #cccccc;
                background-color: #252526;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0d5a8f;
            }
            QListWidget {
                background-color: #1e1e1e;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #cccccc;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
            }
        """
        self.setStyleSheet(style)
        
    def apply_right_panel_styles(self):
        pass

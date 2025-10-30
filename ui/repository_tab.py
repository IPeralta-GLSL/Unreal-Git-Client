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
from ui.commit_graph_widget import CommitGraphWidget
from ui.theme import get_current_theme
import os
import sys
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
    def __init__(self, git_manager, settings_manager=None, parent_window=None, plugin_manager=None):
        super().__init__()
        self.git_manager = git_manager
        self.settings_manager = settings_manager
        self.repo_path = None
        self.parent_window = parent_window
        self.plugin_manager = plugin_manager
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
        
        middle_panel = self.create_middle_panel()
        splitter.addWidget(middle_panel)
        
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([350, 400, 650])
        splitter.setHandleWidth(2)
        
        repo_layout.addWidget(splitter)
        self.stacked_widget.addWidget(self.repo_view)
        
        layout.addWidget(self.stacked_widget)
        
        self.show_home_view()
        
    def create_top_bar(self):
        theme = get_current_theme()
        self.top_bar = QFrame()
        self.top_bar.setMaximumHeight(70)
        self.top_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.top_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['surface']};
                border-bottom: {theme.borders['width_thin']}px solid {theme.colors['border']};
            }}
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
        branch_title.setStyleSheet(f"color: {theme.colors['primary']}; font-size: {theme.fonts['size_xs']}px; font-weight: {theme.fonts['weight_bold']};")
        branch_title.setMaximumHeight(14)
        branch_layout.addWidget(branch_title)
        
        self.branch_button = QPushButton()
        self.branch_button.setText("main")
        self.branch_button.setMinimumSize(180, 28)
        self.branch_button.setMaximumHeight(28)
        self.branch_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.branch_button.setStyleSheet(f"""
            QPushButton {{
                font-weight: {theme.fonts['weight_bold']};
                font-size: {theme.fonts['size_md']}px;
                color: {theme.colors['primary']};
                background-color: {theme.colors['background']};
                border: {theme.borders['width_medium']}px solid {theme.colors['primary']};
                border-radius: {theme.borders['radius_md']}px;
                padding: {theme.spacing['xs']}px {theme.spacing['md']}px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['surface']};
                border-color: {theme.colors['primary_hover']};
                color: {theme.colors['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['primary_text']};
            }}
        """)
        self.branch_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.branch_button.clicked.connect(self.show_branch_menu)
        branch_layout.addWidget(self.branch_button)
        
        layout.addWidget(branch_container, 1)
        
        self.plugin_indicators_container = QWidget()
        self.plugin_indicators_layout = QHBoxLayout(self.plugin_indicators_container)
        self.plugin_indicators_layout.setContentsMargins(0, 0, 0, 0)
        self.plugin_indicators_layout.setSpacing(8)
        layout.addWidget(self.plugin_indicators_container)
        
        layout.addSpacing(10)
        
        separator1 = QWidget()
        separator1.setFixedWidth(1)
        separator1.setFixedHeight(24)
        separator1.setStyleSheet(f"background-color: {theme.colors['border']};")
        layout.addWidget(separator1)
        
        layout.addSpacing(10)
        
        button_style = f"""
            QPushButton {{
                color: {theme.colors['primary']};
                background-color: transparent;
                border: {theme.borders['width_thin']}px solid transparent;
                border-radius: {theme.borders['radius_md']}px;
                padding: {theme.spacing['sm']}px {theme.spacing['md']}px;
                font-size: {theme.fonts['size_md']}px;
                font-weight: {theme.fonts['weight_bold']};
            }}
            QPushButton:hover {{
                background-color: {theme.colors['surface_hover']};
                border-color: {theme.colors['primary']};
            }}
            QPushButton:pressed {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['primary_text']};
            }}
        """
        
        self.open_folder_btn = QPushButton(" Carpeta")
        self.open_folder_btn.setIcon(self.icon_manager.get_icon("folder-open", size=18))
        self.open_folder_btn.setMinimumSize(100, 36)
        self.open_folder_btn.setMaximumSize(130, 36)
        self.open_folder_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.open_folder_btn.setStyleSheet(button_style)
        self.open_folder_btn.setToolTip("Abrir carpeta del proyecto")
        self.open_folder_btn.clicked.connect(self.open_project_folder)
        layout.addWidget(self.open_folder_btn)
        
        self.open_terminal_btn = QPushButton(" Terminal")
        self.open_terminal_btn.setIcon(self.icon_manager.get_icon("terminal", size=18))
        self.open_terminal_btn.setMinimumSize(100, 36)
        self.open_terminal_btn.setMaximumSize(130, 36)
        self.open_terminal_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.open_terminal_btn.setStyleSheet(button_style)
        self.open_terminal_btn.setToolTip("Abrir terminal en la carpeta del proyecto")
        self.open_terminal_btn.clicked.connect(self.open_terminal)
        layout.addWidget(self.open_terminal_btn)
        
        self.open_unreal_btn = QPushButton(" Unreal")
        self.open_unreal_btn.setIcon(self.icon_manager.get_icon("unreal-engine-svgrepo-com", size=18))
        self.open_unreal_btn.setMinimumSize(100, 36)
        self.open_unreal_btn.setMaximumSize(130, 36)
        self.open_unreal_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.open_unreal_btn.setStyleSheet(button_style)
        self.open_unreal_btn.setToolTip("Abrir proyecto con Unreal Engine")
        self.open_unreal_btn.clicked.connect(self.open_with_unreal)
        layout.addWidget(self.open_unreal_btn)
        
        layout.addSpacing(10)
        
        separator2 = QWidget()
        separator2.setFixedWidth(1)
        separator2.setFixedHeight(24)
        separator2.setStyleSheet(f"background-color: {theme.colors['border']};")
        layout.addWidget(separator2)
        
        layout.addSpacing(10)
        
        self.pull_btn = QPushButton(" Pull")
        self.pull_btn.setIcon(self.icon_manager.get_icon("download", size=18))
        self.pull_btn.setMinimumSize(85, 36)
        self.pull_btn.setMaximumSize(110, 36)
        self.pull_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.pull_btn.setStyleSheet(button_style)
        self.pull_btn.setToolTip("Descargar cambios del servidor")
        self.pull_btn.clicked.connect(self.do_pull)
        layout.addWidget(self.pull_btn)
        
        self.push_btn = QPushButton(" Push")
        self.push_btn.setIcon(self.icon_manager.get_icon("git-pull-request", size=18))
        self.push_btn.setMinimumSize(85, 36)
        self.push_btn.setMaximumSize(110, 36)
        self.push_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.push_btn.setStyleSheet(button_style)
        self.push_btn.setToolTip("Subir tus cambios al servidor")
        self.push_btn.clicked.connect(self.do_push)
        layout.addWidget(self.push_btn)
        
        self.fetch_btn = QPushButton(" Fetch")
        self.fetch_btn.setIcon(self.icon_manager.get_icon("git-diff", size=18))
        self.fetch_btn.setMinimumSize(85, 36)
        self.fetch_btn.setMaximumSize(110, 36)
        self.fetch_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.fetch_btn.setStyleSheet(button_style)
        self.fetch_btn.setToolTip("Actualizar información sin descargar")
        self.fetch_btn.clicked.connect(self.do_fetch)
        layout.addWidget(self.fetch_btn)
        
        self.refresh_btn = QPushButton(" Refresh")
        self.refresh_btn.setIcon(self.icon_manager.get_icon("arrows-clockwise", size=18))
        self.refresh_btn.setMinimumSize(85, 36)
        self.refresh_btn.setMaximumSize(110, 36)
        self.refresh_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.refresh_btn.setStyleSheet(button_style)
        self.refresh_btn.setToolTip("Actualizar estado del repositorio")
        self.refresh_btn.clicked.connect(self.refresh_status)
        layout.addWidget(self.refresh_btn)
        
        layout.addStretch()
        
    def create_left_panel(self):
        widget = QWidget()
        widget.setStyleSheet("background-color: palette(base);")
        widget.setMinimumWidth(300)
        widget.setMaximumWidth(600)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        changes_header = self.create_section_header("CAMBIOS", "Archivos modificados en tu repositorio", "file-text")
        layout.addWidget(changes_header)
        
        changes_container = QWidget()
        changes_container.setStyleSheet("background-color: palette(window); padding: 10px;")
        changes_layout = QVBoxLayout(changes_container)
        changes_layout.setContentsMargins(10, 10, 10, 10)
        
        self.changes_list = QListWidget()
        self.changes_list.setMinimumHeight(200)
        self.changes_list.setStyleSheet("""
            QListWidget {
                background-color: palette(window);
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
                background-color: palette(button);
            }
            QListWidget::item:selected {
                background-color: palette(highlight);
                border-left-color: {theme.colors['border_focus']};
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
        commit_container.setStyleSheet("background-color: palette(window); padding: 10px;")
        commit_layout = QVBoxLayout(commit_container)
        commit_layout.setContentsMargins(10, 10, 10, 10)
        
        self.commit_message = QTextEdit()
        self.commit_message.setPlaceholderText("Describe tus cambios...")
        self.commit_message.setMaximumHeight(100)
        self.commit_message.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.commit_message.setStyleSheet("""
            QTextEdit {
                background-color: palette(window);
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
                color: palette(window-text);
            }
            QTextEdit:focus {
                border-color: {theme.colors['border_focus']};
            }
        """)
        commit_layout.addWidget(self.commit_message)
        
        self.commit_btn = QPushButton(" Hacer Commit y Guardar")
        self.commit_btn.setIcon(self.icon_manager.get_icon("git-commit", size=18))
        self.commit_btn.setMinimumHeight(40)
        self.commit_btn.setStyleSheet("""
            QPushButton {
                background-color: palette(highlight);
                color: palette(bright-text);
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: palette(highlight);
            }
            QPushButton:pressed {
                background-color: palette(highlight);
            }
        """)
        self.commit_btn.setToolTip("Guardar todos los cambios preparados con este mensaje")
        self.commit_btn.clicked.connect(self.do_commit)
        commit_layout.addWidget(self.commit_btn)
        
        layout.addWidget(commit_container)
        
        lfs_header = self.create_section_header("GIT LFS", "Manejo de archivos grandes de Unreal Engine", "files")
        layout.addWidget(lfs_header)
        
        lfs_container = QWidget()
        lfs_container.setStyleSheet("background-color: palette(window); padding: 10px;")
        lfs_layout = QVBoxLayout(lfs_container)
        lfs_layout.setContentsMargins(10, 10, 10, 10)
        
        status_widget = QWidget()
        status_widget.setStyleSheet("background-color: palette(button); border-radius: 4px; padding: 8px;")
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(10, 8, 10, 8)
        
        status_icon = QLabel()
        status_icon.setPixmap(self.icon_manager.get_pixmap("info", 16))
        status_layout.addWidget(status_icon)
        
        self.lfs_status_label = QLabel("Estado: No inicializado")
        self.lfs_status_label.setStyleSheet("color: palette(window-text); font-weight: bold;")
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
        theme = get_current_theme()
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['surface']};
                border-bottom: {theme.borders['width_thin']}px solid {theme.colors['border']};
                border-radius: {theme.borders['radius_sm']}px {theme.borders['radius_sm']}px 0px 0px;
            }}
        """)
        header.setMinimumHeight(50)
        header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(theme.spacing['lg'], theme.spacing['sm'], theme.spacing['lg'], theme.spacing['sm'])
        layout.setSpacing(theme.spacing['md'])
        
        if icon_name:
            icon_label = QLabel()
            icon_label.setPixmap(self.icon_manager.get_pixmap(icon_name, size=20))
            icon_label.setFixedSize(24, 24)
            layout.addWidget(icon_label)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet(f"color: {theme.colors['primary']}; font-size: {theme.fonts['size_base']}px; font-weight: {theme.fonts['weight_bold']};")
        text_layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {theme.colors['text_secondary']}; font-size: {theme.fonts['size_xs']}px;")
        text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout)
        
        return header
    
    def create_middle_panel(self):
        widget = QWidget()
        widget.setStyleSheet("background-color: palette(window);")
        widget.setMinimumWidth(400)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        history_header = self.create_section_header("HISTORIAL", "Gráfico de commits del repositorio", "git-commit")
        layout.addWidget(history_header)
        
        history_container = QWidget()
        history_container.setStyleSheet("background-color: palette(window); padding: 10px;")
        history_layout = QVBoxLayout(history_container)
        history_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: palette(window);
                border: 1px solid #3d3d3d;
                border-radius: 5px;
            }
            QScrollBar:vertical {
                background-color: palette(window);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: palette(text);
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: {theme.colors['primary']};
            }
        """)
        
        self.commit_graph = CommitGraphWidget()
        self.commit_graph.setStyleSheet("background-color: palette(window);")
        self.commit_graph.commit_clicked.connect(self.on_graph_commit_clicked)
        scroll.setWidget(self.commit_graph)
        
        history_layout.addWidget(scroll)
        layout.addWidget(history_container)
        
        return widget
    
    def create_right_panel(self):
        widget = QWidget()
        widget.setStyleSheet("background-color: palette(window);")
        widget.setMinimumWidth(400)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        info_header = self.create_section_header("INFORMACIÓN", "Detalles del repositorio actual", "folder")
        layout.addWidget(info_header)
        
        info_container = QWidget()
        info_container.setStyleSheet("background-color: palette(base); padding: 15px;")
        info_container.setMinimumHeight(100)
        info_container.setMaximumHeight(150)
        info_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        info_layout = QVBoxLayout(info_container)
        
        self.repo_info = QLabel("No hay repositorio cargado")
        self.repo_info.setWordWrap(True)
        self.repo_info.setStyleSheet("color: palette(window-text); line-height: 1.6;")
        info_layout.addWidget(self.repo_info)
        
        info_group = QWidget()
        info_group_layout = QVBoxLayout(info_group)
        info_group_layout.setContentsMargins(0, 0, 0, 0)
        info_group_layout.setSpacing(0)
        info_group_layout.addWidget(info_header)
        info_group_layout.addWidget(info_container)
        
        diff_header = self.create_section_header("DIFERENCIAS", "Cambios en el archivo seleccionado", "git-diff")
        
        diff_container = QWidget()
        diff_container.setStyleSheet("background-color: palette(window); padding: 10px;")
        diff_layout = QVBoxLayout(diff_container)
        diff_layout.setContentsMargins(10, 10, 10, 10)
        
        self.diff_view = QTextEdit()
        self.diff_view.setReadOnly(True)
        self.diff_view.setFont(QFont("Courier New", 10))
        self.diff_view.setPlaceholderText("Selecciona un archivo para ver sus cambios...")
        self.diff_view.setStyleSheet("""
            QTextEdit {
                background-color: palette(window);
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.6;
                color: palette(window-text);
            }
        """)
        palette = self.diff_view.palette()
        palette.setColor(palette.ColorRole.PlaceholderText, palette.color(palette.ColorRole.Text))
        self.diff_view.setPalette(palette)
        diff_layout.addWidget(self.diff_view)
        
        diff_group = QWidget()
        diff_group_layout = QVBoxLayout(diff_group)
        diff_group_layout.setContentsMargins(0, 0, 0, 0)
        diff_group_layout.setSpacing(0)
        diff_group_layout.addWidget(diff_header)
        diff_group_layout.addWidget(diff_container)
        
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.setHandleWidth(3)
        right_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: palette(text);
            }
            QSplitter::handle:hover {
                background-color: {theme.colors['primary']};
            }
        """)
        right_splitter.addWidget(info_group)
        right_splitter.addWidget(diff_group)
        right_splitter.setStretchFactor(0, 1)
        right_splitter.setStretchFactor(1, 4)
        right_splitter.setSizes([150, 600])
        
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
        
        if self.parent_window:
            repo_name = os.path.basename(path)
            tab_widget = self.parent_window.tab_widget
            current_index = tab_widget.indexOf(self)
            if current_index >= 0:
                tab_widget.setTabText(current_index, f" {repo_name}")
                tab_widget.setTabIcon(current_index, self.icon_manager.get_icon("folder", size=16))
        
        self.show_repo_view()
        self.refresh_status()
        self.update_repo_info()
        self.load_history()
        self.check_lfs_status()
        self.update_plugin_indicators()
        
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
        if self.plugin_manager:
            unreal_plugin = self.plugin_manager.get_plugin('unreal_engine')
            if unreal_plugin and unreal_plugin.is_unreal_project(self.repo_path):
                uproject = unreal_plugin.get_uproject_file(self.repo_path)
                if uproject:
                    project_name = os.path.basename(uproject).replace('.uproject', '')
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
            
        history = self.git_manager.get_commit_history(50)
        
        if not history:
            return
        
        branch = self.git_manager.get_current_branch()
        
        formatted_commits = []
        for commit in history:
            formatted_commit = {
                'hash': commit['hash'],
                'message': commit['message'],
                'author': commit['author'],
                'email': commit.get('email', ''),
                'date': commit['date'],
                'branch': branch
            }
            formatted_commits.append(formatted_commit)
            
            email = commit.get('email', '')
            if email and email not in self.avatar_cache:
                self.download_gravatar(email, commit['author'])
        
        self.commit_graph.set_commits(formatted_commits)
            
    def on_graph_commit_clicked(self, commit_hash):
        if commit_hash:
            diff = self.git_manager.get_commit_diff(commit_hash)
            formatted_diff = self.format_diff(diff)
            self.diff_view.setHtml(formatted_diff)
    
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
        theme = get_current_theme()
        lines = diff_text.split('\n')
        html = '<pre style="margin: 0; line-height: 1.6;">'
        
        for line in lines:
            if line.startswith('diff --git'):
                html += f'<span style="color: palette(link); font-weight: bold;">{line}</span>\n'
            elif line.startswith('index ') or line.startswith('---') or line.startswith('+++'):
                html += f'<span style="color: palette(text);">{line}</span>\n'
            elif line.startswith('@@'):
                html += f'<span style="color: palette(link); font-weight: bold;">{line}</span>\n'
            elif line.startswith('+') and not line.startswith('+++'):
                html += f'<span style="background-color: {theme.colors["success_pressed"]}; color: palette(link);">{line}</span>\n'
            elif line.startswith('-') and not line.startswith('---'):
                html += f'<span style="background-color: {theme.colors["danger_pressed"]}; color: palette(bright-text);">{line}</span>\n'
            else:
                html += f'<span style="color: palette(window-text);">{line}</span>\n'
        
        html += '</pre>'
        return html
    
    def show_commit_context_menu(self, position):
        pass
    
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
                background-color: palette(button);
                color: palette(window-text);
                border: 1px solid #3d3d3d;
                padding: 5px;
            }
            QMenu::item {
                padding: 10px 30px;
                border-radius: 3px;
                font-size: 13px;
            }
            QMenu::item:selected {
                background-color: palette(highlight);
            }
            QMenu::separator {
                height: 1px;
                background-color: palette(text);
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
                
                self.commit_graph.set_avatar(email, rounded_pixmap)
        
        reply.deleteLater()
    
    def update_plugin_indicators(self):
        theme = get_current_theme()
        if not self.plugin_manager or not self.repo_path:
            return
        
        while self.plugin_indicators_layout.count():
            item = self.plugin_indicators_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        indicators = self.plugin_manager.get_repository_indicators(self.repo_path)
        
        for indicator in indicators:
            btn = QPushButton(f"{indicator['icon']} {indicator['text']}")
            btn.setToolTip(indicator['tooltip'])
            btn.setMinimumHeight(36)
            btn.setMaximumHeight(36)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {indicator.get('color', theme.colors['surface'])};
                    color: palette(bright-text);
                    border: 1px solid {theme.colors['primary']};
                    border-radius: 5px;
                    padding: 4px 12px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: palette(text);
                    border-color: {theme.colors['primary_hover']};
                }}
            """)
            btn.clicked.connect(lambda checked, ind=indicator: self.show_plugin_actions())
            self.plugin_indicators_layout.addWidget(btn)
        
        unreal_plugin = self.plugin_manager.get_plugin('unreal_engine')
        is_unreal_enabled = unreal_plugin is not None
        
        if hasattr(self, 'open_unreal_btn'):
            self.open_unreal_btn.setVisible(is_unreal_enabled)
        if hasattr(self, 'lfs_track_btn'):
            self.lfs_track_btn.setVisible(is_unreal_enabled)
    
    def show_plugin_actions(self):
        if not self.plugin_manager or not self.repo_path:
            return
        
        actions = self.plugin_manager.get_plugin_actions('repository')
        
        if not actions:
            return
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: palette(button);
                border: 1px solid #4ec9b0;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                color: palette(window-text);
            }
            QMenu::item:selected {
                background-color: palette(highlight);
                color: palette(bright-text);
            }
        """)
        
        for action_data in actions:
            if not action_data.get('requires_unreal'):
                continue
            
            action = QAction(f"{action_data['icon']} {action_data['name']}", self)
            action.triggered.connect(lambda checked, ad=action_data: self.execute_plugin_action(ad))
            menu.addAction(action)
        
        cursor_pos = QCursor.pos()
        menu.exec(cursor_pos)
    
    def execute_plugin_action(self, action_data):
        if not self.repo_path:
            return
        
        callback = action_data.get('callback')
        if not callback:
            return
        
        success, message = callback(self.repo_path)
        
        if success:
            if len(message) > 100:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle(action_data['name'])
                msg_box.setText(message)
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.exec()
            else:
                QMessageBox.information(self, action_data['name'], message)
        else:
            QMessageBox.warning(self, "Error", message)
        
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
        if not self.plugin_manager:
            return
        
        unreal_plugin = self.plugin_manager.get_plugin('unreal_engine')
        if not unreal_plugin:
            QMessageBox.warning(
                self,
                "Plugin desactivado",
                "El plugin de Unreal Engine está desactivado.\n\n"
                "Actívalo desde Ajustes > Plugins para usar esta función."
            )
            return
        
        success, message = unreal_plugin.track_unreal_files(self.repo_path)
        if success:
            QMessageBox.information(self, "Éxito", message)
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
                background-color: palette(link);
                color: palette(bright-text);
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 12px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: palette(highlight);
            }
            QPushButton:pressed {
                background-color: palette(highlight);
            }
            QPushButton:disabled {
                background-color: palette(text);
                color: palette(text);
            }
            QListWidget {
                background-color: palette(window);
                color: palette(window-text);
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
                background-color: palette(highlight);
                color: palette(bright-text);
            }
            QListWidget::item:hover {
                background-color: palette(button);
            }
            QTextEdit {
                background-color: palette(window);
                color: palette(window-text);
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
                background-color: palette(window);
                color: palette(window-text);
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
                background-color: palette(window);
                color: palette(window-text);
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
                background-color: palette(highlight);
                color: palette(bright-text);
            }
            QListWidget::item:hover {
                background-color: palette(button);
            }
        """
    
    def open_project_folder(self):
        import subprocess
        import platform
        
        repo_path = os.path.abspath(self.git_manager.repo_path)
        
        system = platform.system()
        if system == "Windows":
            subprocess.Popen(['explorer', repo_path])
        elif system == "Darwin":
            subprocess.Popen(["open", repo_path])
        else:
            subprocess.Popen(["xdg-open", repo_path])
    
    def open_terminal(self):
        import subprocess
        import platform
        
        repo_path = os.path.abspath(self.git_manager.repo_path)
        
        system = platform.system()
        if system == "Windows":
            subprocess.Popen(["cmd.exe", "/K", f"cd /d {repo_path}"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        elif system == "Darwin":
            subprocess.Popen(["open", "-a", "Terminal", repo_path])
        else:
            subprocess.Popen(["gnome-terminal", "--working-directory", repo_path])
    
    def open_with_unreal(self):
        if not self.plugin_manager:
            return
        
        unreal_plugin = self.plugin_manager.get_plugin('unreal_engine')
        if not unreal_plugin:
            QMessageBox.warning(
                self,
                "Plugin desactivado",
                "El plugin de Unreal Engine está desactivado.\n\n"
                "Actívalo desde Ajustes > Plugins para usar esta función."
            )
            return
        
        if not unreal_plugin.is_unreal_project(self.repo_path):
            QMessageBox.information(
                self,
                "No es un proyecto de Unreal",
                "Este repositorio no parece ser un proyecto de Unreal Engine."
            )
            return
        
        success, message = unreal_plugin.open_in_unreal(self.repo_path)
        
        if not success:
            QMessageBox.warning(self, "Error", message)

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                             QListWidget, QTextEdit, QPushButton, QLabel,
                             QGroupBox, QLineEdit, QMessageBox, QListWidgetItem,
                             QProgressDialog, QScrollArea, QFrame, QCheckBox, QStackedWidget,
                             QProgressBar, QComboBox, QFileDialog,
                             QSizePolicy, QMenu, QInputDialog, QApplication, QDialog,
                             QTableWidget, QTableWidgetItem, QHeaderView, QGridLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QPoint, QByteArray, QUrl, QTimer, QObject
from PyQt6.QtGui import QFont, QIcon, QCursor, QAction, QColor, QPixmap, QPainter, QBrush
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from concurrent.futures import ThreadPoolExecutor
from ui.home_view import HomeView
from ui.icon_manager import IconManager
from ui.commit_graph_widget import CommitGraphWidget
from ui.lfs_tracking_dialog import LFSTrackingDialog, LFSLocksDialog
from ui.stash_dialog import StashDialog
from ui.repo_info_dialog import RepoInfoPopup
from ui.ai_chat_popup import AIChatPopup
from ui.theme import get_current_theme
from core.translations import tr
import os
import sys
import hashlib
import fnmatch
import re

class StatusWorkerSignals(QObject):
    finished = pyqtSignal(object)

class HistoryWorkerSignals(QObject):
    finished = pyqtSignal(object)

class CloneThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, git_manager, url, path):
        super().__init__()
        self.git_manager = git_manager
        self.url = url
        self.path = path
        
    def run(self):
        success, message = self.git_manager.clone_repository(
            self.url, 
            self.path, 
            progress_callback=self.progress.emit
        )
        self.finished.emit(success, message)

class PushThread(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)
    
    def __init__(self, git_manager):
        super().__init__()
        self.git_manager = git_manager
        
    def run(self):
        success, message = self.git_manager.push(progress_callback=self.progress.emit)
        self.finished.emit(success, message)


class PushProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        theme = get_current_theme()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.resize(560, 160)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.container = QFrame()
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['background']};
                border: 1px solid {theme.colors['border']};
                border-radius: 10px;
            }}
        """)
        outer.addWidget(self.container)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(10)

        title = QLabel(tr('push'))
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {theme.colors['text']};")
        layout.addWidget(title)

        self.message_label = QLabel(tr('pushing_changes'))
        self.message_label.setStyleSheet(f"color: {theme.colors['text_secondary']};")
        layout.addWidget(self.message_label)

        self.details_label = QLabel("")
        self.details_label.setStyleSheet(f"color: {theme.colors['text']};")
        self.details_label.setWordWrap(True)
        layout.addWidget(self.details_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {theme.colors['border']};
                border-radius: 6px;
                text-align: center;
                background-color: {theme.colors['surface']};
                color: {theme.colors['text']};
            }}
            QProgressBar::chunk {{
                background-color: {theme.colors['primary']};
                border-radius: 5px;
            }}
        """)
        layout.addWidget(self.progress_bar)

    def set_details(self, text: str):
        self.details_label.setText(text or "")

    def set_percent(self, percent: int | None):
        if percent is None:
            if self.progress_bar.maximum() != 0:
                self.progress_bar.setRange(0, 0)
            return

        percent = max(0, min(100, int(percent)))
        if self.progress_bar.maximum() != 100:
            self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(percent)


class CommitFileItem(QFrame):
    def __init__(self, file_path, status, diff_content, icon_manager, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.status = status
        self.diff_content = diff_content
        self.icon_manager = icon_manager
        self.is_expanded = False
        self.theme = get_current_theme()
        
        self.setObjectName("commitFileItem")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setup_ui()
        self.update_style()
        
    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.header = QFrame()
        self.header.setObjectName("commitFileHeader")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(8, 6, 8, 6)
        header_layout.setSpacing(8)
        
        self.expand_icon = QLabel()
        self.expand_icon.setFixedSize(12, 12)
        header_layout.addWidget(self.expand_icon)
        
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(8, 8)
        header_layout.addWidget(self.status_dot)
        
        self.file_label = QLabel(self.file_path)
        header_layout.addWidget(self.file_label, 1)
        
        self.main_layout.addWidget(self.header)
        
        self.diff_container = QFrame()
        self.diff_container.setObjectName("commitDiffContainer")
        self.diff_container.setVisible(False)
        diff_layout = QVBoxLayout(self.diff_container)
        diff_layout.setContentsMargins(0, 0, 0, 0)
        diff_layout.setSpacing(0)
        
        self.diff_view = QTextEdit()
        self.diff_view.setReadOnly(True)
        self.diff_view.setMinimumHeight(80)
        self.diff_view.setMaximumHeight(300)
        self.diff_view.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.theme.colors['background']};
                border: none;
                font-family: 'Cascadia Code', 'Consolas', monospace;
                font-size: 11px;
                padding: 6px 8px;
            }}
        """)
        diff_layout.addWidget(self.diff_view)
        
        self.main_layout.addWidget(self.diff_container)
        
        self._update_icons()
        
    def _update_icons(self):
        is_added = self.status == 'A'
        is_deleted = self.status == 'D'
        is_modified = self.status == 'M'
        is_renamed = self.status == 'R'
        
        if is_added:
            color = "#3fb950"
        elif is_deleted:
            color = "#f85149"
        elif is_renamed:
            color = "#a371f7"
        elif is_modified:
            color = "#d29922"
        else:
            color = "#848d97"
        
        self.status_dot.setStyleSheet(f"""
            background-color: {color};
            border-radius: 4px;
        """)
        
        self.file_label.setStyleSheet(f"""
            color: {self.theme.colors['text']};
            font-family: 'Segoe UI', sans-serif;
            font-size: 12px;
        """)
        
        expand_icon = "caret-right" if not self.is_expanded else "caret-down"
        self.expand_icon.setPixmap(self.icon_manager.get_icon(expand_icon, size=12).pixmap(12, 12))
        
    def update_style(self):
        hover_bg = f"{self.theme.colors['text']}08"
        expanded_bg = f"{self.theme.colors['text']}05" if self.is_expanded else "transparent"
        
        self.setStyleSheet(f"""
            QFrame#commitFileItem {{
                background-color: {expanded_bg};
                border: none;
                border-bottom: 1px solid {self.theme.colors['border']}50;
            }}
            QFrame#commitFileItem:hover {{
                background-color: {hover_bg};
            }}
            QFrame#commitFileHeader {{
                background-color: transparent;
                border: none;
            }}
            QFrame#commitDiffContainer {{
                background-color: {self.theme.colors['background']};
                border: none;
                margin: 0px 8px 8px 8px;
                border-radius: 4px;
            }}
        """)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_expand()
        super().mousePressEvent(event)
        
    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.diff_container.setVisible(self.is_expanded)
        self._update_icons()
        self.update_style()
        
        if self.is_expanded and self.diff_view.toPlainText() == "":
            self.load_diff()
            
    def load_diff(self):
        if self.diff_content:
            formatted = self.format_diff_simple(self.diff_content)
            self.diff_view.setHtml(formatted)
        else:
            self.diff_view.setPlainText(tr('no_changes'))
        
    def format_diff_simple(self, diff_text):
        if not diff_text:
            return "<p style='color: #858585;'>No diff available</p>"
            
        lines = diff_text.split('\n')
        html_parts = ["<pre style='margin:0; font-family: Consolas, monospace; font-size: 11px; line-height: 1.4;'>"]
        
        for line in lines:
            escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            if line.startswith('+') and not line.startswith('+++'):
                html_parts.append(f"<div style='background-color: #2d4a3e; color: #4ec9b0;'>{escaped}</div>")
            elif line.startswith('-') and not line.startswith('---'):
                html_parts.append(f"<div style='background-color: #4a2d2d; color: #f48771;'>{escaped}</div>")
            elif line.startswith('@@'):
                html_parts.append(f"<div style='background-color: #2d3a4a; color: #569cd6;'>{escaped}</div>")
            elif line.startswith('diff ') or line.startswith('index '):
                html_parts.append(f"<div style='color: #858585;'>{escaped}</div>")
            else:
                html_parts.append(f"<div style='color: #d4d4d4;'>{escaped}</div>")
                
        html_parts.append("</pre>")
        return ''.join(html_parts)


class RepositoryTab(QWidget):
    def __init__(self, git_manager, settings_manager=None, parent_window=None, plugin_manager=None):
        super().__init__()
        self.git_manager = git_manager
        self.settings_manager = settings_manager
        self.repo_path = None
        self.parent_window = parent_window
        self.plugin_manager = plugin_manager
        self.avatar_cache = {}
        self.diff_cache = {}
        self.diff_cache_max_size = 50
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.on_avatar_downloaded)
        self.icon_manager = IconManager()
        self.large_files = []
        self.status_worker = None
        self.status_worker_pending = False
        self.history_worker = None
        self.history_worker_pending = False
        self.repo_splitter = None
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.setInterval(2000)
        self.auto_refresh_timer.timeout.connect(self._auto_refresh_tick)
        self.scan_large_files = True
        self.current_branch_name = ""
        self.last_status_summary = {}
        self.status_future = None
        self.history_future = None
        self.history_branch_requested = ""
        self.git_op_future = None
        self.diff_future = None
        self.pending_diff_commit = None
        self.diff_debounce_timer = QTimer(self)
        self.diff_debounce_timer.setSingleShot(True)
        self.diff_debounce_timer.setInterval(100)
        self.diff_debounce_timer.timeout.connect(self._load_pending_diff)
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.busy_timer = QTimer(self)
        self.busy_timer.setSingleShot(True)
        self.busy_timer.setInterval(300)
        self.busy_timer.timeout.connect(self._show_busy)
        self.busy_message = ""
        self.status_signals = StatusWorkerSignals()
        self.status_signals.finished.connect(self._on_status_future)
        self.init_ui()

    def closeEvent(self, event):
        self.auto_refresh_timer.stop()
        self.busy_timer.stop()
        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)
        super().closeEvent(event)

    def _show_busy(self):
        if self.parent_window and self.busy_message:
            self.parent_window.status_label.setText(self.busy_message)
            self.parent_window.progress_label.setText("...")

    def _stop_busy(self):
        if self.parent_window:
            self.parent_window.status_label.setText(tr('ready'))
            self.parent_window.progress_label.clear()
        self.busy_timer.stop()
        self.busy_message = ""
    
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        self.home_view = HomeView(self.settings_manager)
        self.home_view.open_repo_requested.connect(self.on_home_open_repo)
        self.home_view.clone_repo_requested.connect(self.on_home_clone_repo)
        self.home_view.open_recent_repo.connect(self.load_repository)
        self.home_view.folder_dropped.connect(self.load_repository)
        self.stacked_widget.addWidget(self.home_view)
        
        # Loading View
        self.loading_view = self.create_loading_view()
        self.stacked_widget.addWidget(self.loading_view)
        
        # Clone View
        self.clone_view = self.create_clone_view()
        self.stacked_widget.addWidget(self.clone_view)

        self.repo_view = QWidget()
        repo_layout = QVBoxLayout(self.repo_view)
        repo_layout.setContentsMargins(0, 0, 0, 0)
        repo_layout.setSpacing(0)
        
        self.create_top_bar()
        repo_layout.addWidget(self.top_bar)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.repo_splitter = splitter
        
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([400, 700])
        splitter.setHandleWidth(2)
        
        repo_layout.addWidget(splitter)
        self.stacked_widget.addWidget(self.repo_view)
        
        self.show_home_view()
        
    def create_loading_view(self):
        theme = get_current_theme()
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        
        # Loading Icon
        icon_label = QLabel()
        icon = self.icon_manager.get_icon("git-branch") 
        pixmap = icon.pixmap(64, 64)
        icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Status Label
        self.loading_label = QLabel(tr('loading'))
        self.loading_label.setFont(QFont("Segoe UI", 12))
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet(f"color: {theme.colors['text']};")
        layout.addWidget(self.loading_label)
        
        # Details Label
        self.loading_details = QLabel("")
        self.loading_details.setFont(QFont("Segoe UI", 10))
        self.loading_details.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_details.setStyleSheet(f"color: {theme.colors['text_secondary']};")
        layout.addWidget(self.loading_details)
        
        # Progress Bar
        self.loading_progress = QProgressBar()
        self.loading_progress.setFixedWidth(400)
        self.loading_progress.setTextVisible(False)
        self.loading_progress.setFixedHeight(4)
        self.loading_progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {theme.colors['surface']};
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {theme.colors['primary']};
                border-radius: 2px;
            }}
        """)
        layout.addWidget(self.loading_progress)
        
        return container
    
    def create_clone_view(self):
        theme = get_current_theme()
        container = QWidget()
        
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: palette(window);
            }}
            QScrollBar:vertical {{
                background-color: transparent;
                width: 14px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background-color: palette(mid);
                border-radius: 7px;
                min-height: 40px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme.colors['surface_hover']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        layout.setSpacing(24)
        layout.setContentsMargins(50, 40, 50, 50)
        
        header_container = QWidget()
        header_container.setMaximumWidth(600)
        header_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(16)
        
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)
        
        title_row = QHBoxLayout()
        title_row.setSpacing(12)
        
        icon_label = QLabel()
        icon_label.setPixmap(self.icon_manager.get_pixmap("download", 28))
        title_row.addWidget(icon_label)
        
        self.clone_title = QLabel(tr('clone_repository'))
        self.clone_title.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {theme.colors['text']};
        """)
        title_row.addWidget(self.clone_title)
        title_row.addStretch()
        title_layout.addLayout(title_row)
        
        self.clone_description = QLabel(tr('clone_description'))
        self.clone_description.setStyleSheet(f"color: {theme.colors['text_secondary']}; font-size: 14px;")
        self.clone_description.setWordWrap(True)
        title_layout.addWidget(self.clone_description)
        
        header_layout.addWidget(title_container, 1)
        layout.addWidget(header_container)
        
        form_container = QFrame()
        form_container.setMaximumWidth(600)
        form_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        form_container.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                border-radius: 12px;
            }}
        """)
        
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(20)
        form_layout.setContentsMargins(24, 24, 24, 24)
        
        url_section = QWidget()
        url_layout = QVBoxLayout(url_section)
        url_layout.setContentsMargins(0, 0, 0, 0)
        url_layout.setSpacing(8)
        
        self.clone_url_label = QLabel(tr('repository_url'))
        self.clone_url_label.setStyleSheet(f"color: {theme.colors['text']}; font-weight: bold; font-size: 13px;")
        url_layout.addWidget(self.clone_url_label)
        
        self.clone_url_input = QLineEdit()
        self.clone_url_input.setPlaceholderText("https://github.com/user/repo.git")
        self.clone_url_input.setMinimumHeight(44)
        self.clone_url_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {theme.colors['background']};
                border: 1px solid {theme.colors['border']};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                color: {theme.colors['text']};
            }}
            QLineEdit:focus {{
                border-color: {theme.colors['primary']};
            }}
        """)
        url_layout.addWidget(self.clone_url_input)
        form_layout.addWidget(url_section)
        
        path_section = QWidget()
        path_layout_v = QVBoxLayout(path_section)
        path_layout_v.setContentsMargins(0, 0, 0, 0)
        path_layout_v.setSpacing(8)
        
        self.clone_path_label = QLabel(tr('destination_folder'))
        self.clone_path_label.setStyleSheet(f"color: {theme.colors['text']}; font-weight: bold; font-size: 13px;")
        path_layout_v.addWidget(self.clone_path_label)
        
        path_row = QHBoxLayout()
        path_row.setSpacing(10)
        
        self.clone_path_combo = QComboBox()
        self.clone_path_combo.setEditable(True)
        self.clone_path_combo.setMinimumHeight(44)
        self.clone_path_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {theme.colors['background']};
                border: 1px solid {theme.colors['border']};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                color: {theme.colors['text']};
            }}
            QComboBox:focus {{
                border-color: {theme.colors['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                selection-background-color: {theme.colors['primary']};
                border-radius: 8px;
            }}
        """)
        path_row.addWidget(self.clone_path_combo, 1)
        
        browse_btn = QPushButton(tr('browse'))
        browse_btn.setIcon(self.icon_manager.get_icon("folder-open", size=16))
        browse_btn.setMinimumHeight(44)
        browse_btn.setMinimumWidth(110)
        browse_btn.clicked.connect(self.browse_clone_folder)
        theme.apply_button_style(browse_btn, 'default')
        path_row.addWidget(browse_btn)
        
        path_layout_v.addLayout(path_row)
        form_layout.addWidget(path_section)
        
        options_section = QWidget()
        options_layout = QVBoxLayout(options_section)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(8)
        
        self.clone_create_folder_check = QCheckBox(tr('create_repo_folder'))
        self.clone_create_folder_check.setStyleSheet(f"""
            QCheckBox {{
                color: {theme.colors['text']};
                font-size: 13px;
                spacing: 10px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 5px;
                border: 2px solid {theme.colors['border']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {theme.colors['primary']};
                border-color: {theme.colors['primary']};
            }}
        """)
        self.clone_create_folder_check.stateChanged.connect(self.update_clone_helper)
        options_layout.addWidget(self.clone_create_folder_check)
        
        self.clone_helper_text = QLabel(tr('clone_helper'))
        self.clone_helper_text.setStyleSheet(f"""
            color: {theme.colors['text_secondary']};
            font-size: 12px;
            padding-left: 30px;
        """)
        self.clone_helper_text.setWordWrap(True)
        options_layout.addWidget(self.clone_helper_text)
        
        options_layout.addSpacing(8)
        
        self.clone_allow_non_empty_check = QCheckBox(tr('allow_non_empty_clone'))
        self.clone_allow_non_empty_check.setStyleSheet(f"""
            QCheckBox {{
                color: {theme.colors['text']};
                font-size: 13px;
                spacing: 10px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 5px;
                border: 2px solid {theme.colors['border']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {theme.colors['primary']};
                border-color: {theme.colors['primary']};
            }}
        """)
        options_layout.addWidget(self.clone_allow_non_empty_check)
        
        clone_non_empty_note = QLabel(tr('allow_non_empty_clone_note'))
        clone_non_empty_note.setStyleSheet(f"""
            color: {theme.colors['text_secondary']};
            font-size: 12px;
            padding-left: 30px;
        """)
        clone_non_empty_note.setWordWrap(True)
        options_layout.addWidget(clone_non_empty_note)
        
        form_layout.addWidget(options_section)
        
        layout.addWidget(form_container)
        
        buttons_container = QWidget()
        buttons_container.setMaximumWidth(600)
        buttons_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 8, 0, 0)
        buttons_layout.setSpacing(12)
        buttons_layout.addStretch()
        
        self.clone_cancel_btn = QPushButton(tr('cancel'))
        self.clone_cancel_btn.setMinimumHeight(44)
        self.clone_cancel_btn.setMinimumWidth(110)
        self.clone_cancel_btn.clicked.connect(self.show_home_view)
        theme.apply_button_style(self.clone_cancel_btn, 'default')
        buttons_layout.addWidget(self.clone_cancel_btn)
        
        self.clone_start_btn = QPushButton(tr('clone_repository'))
        self.clone_start_btn.setIcon(self.icon_manager.get_icon("download", size=18))
        self.clone_start_btn.setMinimumHeight(44)
        self.clone_start_btn.setMinimumWidth(180)
        self.clone_start_btn.clicked.connect(self.start_clone)
        theme.apply_button_style(self.clone_start_btn, 'primary')
        buttons_layout.addWidget(self.clone_start_btn)
        
        layout.addWidget(buttons_container)
        layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
        
        return container

    def show_loading(self, title, details="", is_indeterminate=True):
        self.loading_label.setText(title)
        self.loading_details.setText(details)
        if is_indeterminate:
            self.loading_progress.setRange(0, 0)
        else:
            self.loading_progress.setRange(0, 100)
            self.loading_progress.setValue(0)
        self.stacked_widget.setCurrentWidget(self.loading_view)

    def create_top_bar(self):
        theme = get_current_theme()
        self.top_bar = QFrame()
        self.top_bar.setMinimumHeight(88)
        self.top_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.top_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['surface']};
                border-bottom: {theme.borders['width_thin']}px solid {theme.colors['border']};
            }}
        """)
        
        layout = QHBoxLayout(self.top_bar)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        
        branch_container = QWidget()
        branch_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        branch_layout = QVBoxLayout(branch_container)
        branch_layout.setContentsMargins(0, 0, 0, 0)
        branch_layout.setSpacing(8)
        
        self.branch_title = QLabel(tr('current_branch_label'))
        self.branch_title.setStyleSheet(f"color: {theme.colors['primary']}; font-size: {theme.fonts['size_xs']}px; font-weight: {theme.fonts['weight_bold']};")
        branch_layout.addWidget(self.branch_title)
        
        self.branch_button = QPushButton()
        self.branch_button.setText("main")
        self.branch_button.setMinimumSize(200, 45)
        self.branch_button.setMaximumHeight(50)
        self.branch_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.branch_button.setStyleSheet(f"""
            QPushButton {{
                font-weight: {theme.fonts['weight_bold']};
                font-size: {theme.fonts['size_md']}px;
                color: {theme.colors['primary']};
                background-color: {theme.colors['background']};
                border: {theme.borders['width_medium']}px solid {theme.colors['primary']};
                border-radius: {theme.borders['radius_md']}px;
                padding: 8px 15px;
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
        self.plugin_indicators_container.hide()
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
        
        self.lfs_btn = QPushButton("LFS")
        self.lfs_btn.setIcon(self.icon_manager.get_icon("lfs-icon", size=18))
        self.lfs_btn.setMinimumHeight(36)
        self.lfs_btn.setMinimumWidth(90)
        self.lfs_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.lfs_btn.setStyleSheet(button_style)
        self.lfs_btn.setToolTip(tr('lfs_title'))
        self.lfs_btn.clicked.connect(self.show_lfs_menu)
        layout.addWidget(self.lfs_btn)

        self.open_folder_btn = QPushButton(tr('folder_button'))
        self.open_folder_btn.setIcon(self.icon_manager.get_icon("folder-open", size=18))
        self.open_folder_btn.setMinimumHeight(36)
        self.open_folder_btn.setMinimumWidth(100)
        self.open_folder_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.open_folder_btn.setStyleSheet(button_style)
        self.open_folder_btn.setToolTip(tr('folder_tooltip'))
        self.open_folder_btn.clicked.connect(self.open_project_folder)
        layout.addWidget(self.open_folder_btn)
        
        self.open_terminal_btn = QPushButton(tr('terminal_button'))
        self.open_terminal_btn.setIcon(self.icon_manager.get_icon("terminal", size=18))
        self.open_terminal_btn.setMinimumHeight(36)
        self.open_terminal_btn.setMinimumWidth(100)
        self.open_terminal_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.open_terminal_btn.setStyleSheet(button_style)
        self.open_terminal_btn.setToolTip(tr('terminal_tooltip'))
        self.open_terminal_btn.clicked.connect(self.open_terminal)
        layout.addWidget(self.open_terminal_btn)
        
        layout.addSpacing(10)
        
        separator2 = QWidget()
        separator2.setFixedWidth(1)
        separator2.setFixedHeight(24)
        separator2.setStyleSheet(f"background-color: {theme.colors['border']};")
        layout.addWidget(separator2)
        
        layout.addSpacing(10)
        
        self.pull_btn = QPushButton(tr('pull'))
        self.pull_btn.setIcon(self.icon_manager.get_icon("download", size=18))
        self.pull_btn.setMinimumHeight(36)
        self.pull_btn.setMinimumWidth(90)
        self.pull_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.pull_btn.setStyleSheet(button_style)
        self.pull_btn.setToolTip(tr('pull_tooltip'))
        self.pull_btn.clicked.connect(self.do_pull)
        layout.addWidget(self.pull_btn)
        
        self.push_btn = QPushButton(tr('push'))
        self.push_btn.setIcon(self.icon_manager.get_icon("git-pull-request", size=18))
        self.push_btn.setMinimumHeight(36)
        self.push_btn.setMinimumWidth(90)
        self.push_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.push_btn.setStyleSheet(button_style)
        self.push_btn.setToolTip(tr('push_tooltip'))
        self.push_btn.clicked.connect(self.do_push)
        layout.addWidget(self.push_btn)
        
        self.fetch_btn = QPushButton(tr('fetch'))
        self.fetch_btn.setIcon(self.icon_manager.get_icon("git-diff", size=18))
        self.fetch_btn.setMinimumHeight(36)
        self.fetch_btn.setMinimumWidth(90)
        self.fetch_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.fetch_btn.setStyleSheet(button_style)
        self.fetch_btn.setToolTip(tr('fetch_tooltip'))
        self.fetch_btn.clicked.connect(self.do_fetch)
        layout.addWidget(self.fetch_btn)
        
        layout.addSpacing(10)
        
        separator3 = QWidget()
        separator3.setFixedWidth(1)
        separator3.setFixedHeight(24)
        separator3.setStyleSheet(f"background-color: {theme.colors['border']};")
        layout.addWidget(separator3)
        
        layout.addSpacing(10)
        
        self.ai_chat_btn = QPushButton("AI")
        self.ai_chat_btn.setIcon(self.icon_manager.get_icon("lightbulb", size=18))
        self.ai_chat_btn.setMinimumHeight(36)
        self.ai_chat_btn.setMinimumWidth(70)
        self.ai_chat_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.ai_chat_btn.setStyleSheet(button_style)
        self.ai_chat_btn.setToolTip("AI Chat Assistant")
        self.ai_chat_btn.clicked.connect(self.toggle_ai_sidebar)
        layout.addWidget(self.ai_chat_btn)
        
        # Info button
        self.info_btn = QPushButton()
        self.info_btn.setIcon(self.icon_manager.get_icon("info", size=18))
        self.info_btn.setMinimumHeight(36)
        self.info_btn.setMinimumWidth(40)
        self.info_btn.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.info_btn.setStyleSheet(button_style)
        self.info_btn.setToolTip(tr('info_title'))
        self.info_btn.clicked.connect(self.show_repo_info_dialog)
        layout.addWidget(self.info_btn)
        
        layout.addStretch()
        
    def create_left_panel(self):
        theme = get_current_theme()
        
        panel = QWidget()
        panel.setMinimumWidth(350)
        panel.setMaximumWidth(500)
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        
        tabs_container = QFrame()
        tabs_container.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['surface']};
                border-bottom: 1px solid {theme.colors['border']};
            }}
        """)
        tabs_layout = QHBoxLayout(tabs_container)
        tabs_layout.setContentsMargins(0, 0, 0, 0)
        tabs_layout.setSpacing(0)
        
        changes_tab_container = QWidget()
        changes_tab_container.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        changes_tab_inner = QHBoxLayout(changes_tab_container)
        changes_tab_inner.setContentsMargins(16, 12, 16, 12)
        changes_tab_inner.setSpacing(6)
        changes_tab_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        changes_tab_icon = QLabel()
        changes_tab_icon.setPixmap(self.icon_manager.get_icon("file-text", size=14).pixmap(14, 14))
        changes_tab_inner.addWidget(changes_tab_icon)
        
        self.changes_tab_label = QLabel(tr('changes_title'))
        changes_tab_inner.addWidget(self.changes_tab_label)
        
        self.changes_tab_counter = QLabel("0")
        self.changes_tab_counter.setStyleSheet(f"""
            QLabel {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['text_inverse']};
                border-radius: 9px;
                padding: 1px 6px;
                font-size: 10px;
                font-weight: bold;
            }}
        """)
        changes_tab_inner.addWidget(self.changes_tab_counter)
        
        history_tab_container = QWidget()
        history_tab_container.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        history_tab_inner = QHBoxLayout(history_tab_container)
        history_tab_inner.setContentsMargins(16, 12, 16, 12)
        history_tab_inner.setSpacing(6)
        history_tab_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        history_tab_icon = QLabel()
        history_tab_icon.setPixmap(self.icon_manager.get_icon("git-commit", size=14).pixmap(14, 14))
        history_tab_inner.addWidget(history_tab_icon)
        
        self.history_tab_label = QLabel(tr('history_title'))
        history_tab_inner.addWidget(self.history_tab_label)
        
        self.changes_tab_btn = QPushButton()
        self.changes_tab_btn.setCheckable(True)
        self.changes_tab_btn.setChecked(True)
        self.changes_tab_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.changes_tab_btn.setLayout(changes_tab_inner)
        
        self.history_tab_btn = QPushButton()
        self.history_tab_btn.setCheckable(True)
        self.history_tab_btn.setChecked(False)
        self.history_tab_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.history_tab_btn.setLayout(history_tab_inner)
        
        tab_btn_style = f"""
            QPushButton {{
                background-color: transparent;
                color: {theme.colors['text_secondary']};
                border: none;
                border-bottom: 3px solid transparent;
                padding: 14px 20px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                color: {theme.colors['text']};
                background-color: {theme.colors['surface_hover']};
            }}
            QPushButton:checked {{
                color: {theme.colors['primary']};
                border-bottom: 3px solid {theme.colors['primary']};
            }}
        """
        self.changes_tab_btn.setStyleSheet(tab_btn_style)
        self.history_tab_btn.setStyleSheet(tab_btn_style)
        
        self.changes_tab_btn.clicked.connect(lambda: self.switch_tab('changes'))
        self.history_tab_btn.clicked.connect(lambda: self.switch_tab('history'))
        
        tabs_layout.addWidget(self.changes_tab_btn, 1)
        tabs_layout.addWidget(self.history_tab_btn, 1)
        
        panel_layout.addWidget(tabs_container)
        self.tab_stack = QStackedWidget()
        panel_layout.addWidget(self.tab_stack, 1)
        
        changes_page = self._create_changes_page()
        self.tab_stack.addWidget(changes_page)
        
        history_page = self._create_history_page()
        self.tab_stack.addWidget(history_page)
        
        return panel
    
    def switch_tab(self, tab_name):
        if tab_name == 'changes':
            self.changes_tab_btn.setChecked(True)
            self.history_tab_btn.setChecked(False)
            self.tab_stack.setCurrentIndex(0)
            if hasattr(self, 'right_stack'):
                self.right_stack.setCurrentIndex(0)
        else:
            self.changes_tab_btn.setChecked(False)
            self.history_tab_btn.setChecked(True)
            self.tab_stack.setCurrentIndex(1)
            if hasattr(self, 'right_stack'):
                self.right_stack.setCurrentIndex(1)
    
    def _create_changes_page(self):
        theme = get_current_theme()
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        widget = QWidget()
        widget.setStyleSheet("background-color: palette(base);")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Conflict section (hidden by default)
        self.conflict_container = QWidget()
        self.conflict_container.setVisible(False)
        conflict_layout = QVBoxLayout(self.conflict_container)
        conflict_layout.setContentsMargins(0, 0, 0, 0)
        conflict_layout.setSpacing(0)
        
        self.conflict_header = self.create_section_header(tr('conflicts'), tr('conflicts_desc'), "warning")
        
        self.conflict_counter = QLabel("0")
        self.conflict_counter.setStyleSheet(f"""
            QLabel {{
                background-color: {theme.colors['danger']};
                color: {theme.colors['text_inverse']};
                border-radius: 10px;
                padding: 2px 8px;
                font-weight: {theme.fonts['weight_bold']};
                font-size: {theme.fonts['size_xs']}px;
                min-width: 20px;
            }}
        """)
        self.conflict_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.conflict_header.layout().insertWidget(2, self.conflict_counter)
        conflict_layout.addWidget(self.conflict_header)
        
        # Conflict list
        conflict_list_container = QWidget()
        conflict_list_container.setStyleSheet("background-color: palette(window); padding: 10px;")
        conflict_list_layout = QVBoxLayout(conflict_list_container)
        conflict_list_layout.setContentsMargins(10, 10, 10, 10)
        
        self.conflict_list = QListWidget()
        self.conflict_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.conflict_list.customContextMenuRequested.connect(self.show_conflict_context_menu)
        self.conflict_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['danger']};
                border-radius: 8px;
                padding: 4px;
            }}
            QListWidget::item {{
                color: {theme.colors['danger']};
                padding: 8px;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{
                background-color: {theme.colors['danger']};
                color: {theme.colors['text_inverse']};
            }}
        """)
        self.conflict_list.setMaximumHeight(150)
        conflict_list_layout.addWidget(self.conflict_list)
        
        # Conflict action buttons
        conflict_btn_row = QHBoxLayout()
        conflict_btn_row.setSpacing(8)
        
        self.abort_merge_btn = QPushButton(tr('abort_merge'))
        self.abort_merge_btn.setIcon(self.icon_manager.get_icon("x-circle", size=16))
        self.abort_merge_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.abort_merge_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors['danger']};
                color: {theme.colors['text_inverse']};
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.get('danger_hover', '#c0392b')};
            }}
        """)
        self.abort_merge_btn.clicked.connect(self.abort_merge)
        conflict_btn_row.addWidget(self.abort_merge_btn)
        
        conflict_btn_row.addStretch()
        
        self.continue_merge_btn = QPushButton(tr('continue_merge'))
        self.continue_merge_btn.setIcon(self.icon_manager.get_icon("check-circle", size=16))
        self.continue_merge_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.continue_merge_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors['success']};
                color: {theme.colors['text_inverse']};
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.get('success_hover', '#45a049')};
            }}
        """)
        self.continue_merge_btn.clicked.connect(self.continue_merge)
        conflict_btn_row.addWidget(self.continue_merge_btn)
        
        conflict_list_layout.addLayout(conflict_btn_row)
        conflict_layout.addWidget(conflict_list_container)
        
        layout.addWidget(self.conflict_container)
        
        changes_container = QFrame()
        changes_container.setObjectName("changesContainer")
        changes_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        changes_container.setStyleSheet(f"""
            QFrame#changesContainer {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                border-radius: 10px;
                margin: 4px;
            }}
        """)
        changes_layout = QVBoxLayout(changes_container)
        changes_layout.setContentsMargins(12, 12, 12, 12)
        changes_layout.setSpacing(10)
        
        # Large files banner
        self.large_files_banner = QFrame()
        self.large_files_banner.setObjectName("largeFilesBanner")
        self.large_files_banner.setStyleSheet(f"""
            QFrame#largeFilesBanner {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {theme.colors['warning']}15, 
                    stop:1 {theme.colors['warning']}08);
                border: 1px solid {theme.colors['warning']}40;
                border-left: 4px solid {theme.colors['warning']};
                border-radius: 8px;
                margin-bottom: 8px;
            }}
        """)
        self.large_files_banner.hide()
        
        # Horizontal layout for maximum compactness
        banner_layout = QHBoxLayout(self.large_files_banner)
        banner_layout.setContentsMargins(10, 6, 10, 6)
        banner_layout.setSpacing(8)
        
        # Icon
        warning_icon = QLabel()
        warning_icon.setPixmap(self.icon_manager.get_icon("warning", size=14, color=theme.colors['warning']).pixmap(14, 14))
        warning_icon.setAlignment(Qt.AlignmentFlag.AlignTop)
        banner_layout.addWidget(warning_icon)
        
        # Text
        self.large_files_label = QLabel()
        self.large_files_label.setWordWrap(True)
        self.large_files_label.setStyleSheet(f"color: {theme.colors['text']}; font-size: 11px;")
        banner_layout.addWidget(self.large_files_label, 1)
        
        # Button
        track_btn = QPushButton(tr('track_lfs'))
        track_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        track_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {theme.colors['warning']};
                border: 1px solid {theme.colors['warning']};
                border-radius: 3px;
                padding: 3px 8px;
                font-weight: 600;
                font-size: 10px;
                min-width: 60px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['warning']}1a;
            }}
        """)
        track_btn.clicked.connect(self.track_large_files)
        banner_layout.addWidget(track_btn)
        
        changes_layout.addWidget(self.large_files_banner)
        
        # Selection controls row - ABOVE the list
        selection_row = QHBoxLayout()
        selection_row.setSpacing(8)
        selection_row.setContentsMargins(0, 0, 0, 4)
        
        # Toggle select all button (for checkboxes)
        self._all_checked = True
        self.toggle_select_btn = QPushButton()
        self.toggle_select_btn.setIcon(self.icon_manager.get_icon("check-square", size=14, color="#ffffff"))
        self.toggle_select_btn.setToolTip(tr('deselect_all'))
        self.toggle_select_btn.setFixedSize(28, 28)
        self.toggle_select_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.toggle_select_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme.colors['primary']}, 
                    stop:1 {theme.colors['primary_hover']});
                border: none;
                border-radius: 8px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme.colors['primary_hover']}, 
                    stop:1 {theme.colors['primary']});
            }}
            QPushButton:pressed {{
                background-color: {theme.colors['primary_pressed']};
            }}
        """)
        self.toggle_select_btn.clicked.connect(self.toggle_all_changes)
        selection_row.addWidget(self.toggle_select_btn)
        
        # Checked files counter
        self.checked_label = QLabel()
        self.checked_label.setStyleSheet(f"""
            QLabel {{
                color: {theme.colors['text_secondary']};
                font-size: 11px;
                font-weight: 600;
                padding: 4px 8px;
                background-color: {theme.colors['background']};
                border-radius: 6px;
            }}
        """)
        selection_row.addWidget(self.checked_label)
        
        selection_row.addStretch()
        
        changes_layout.addLayout(selection_row)
        
        self.changes_list = QListWidget()
        self.changes_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.changes_list.setMinimumHeight(200)
        self.changes_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.changes_list.customContextMenuRequested.connect(self.show_changes_context_menu)
        self.changes_list.itemChanged.connect(self.on_item_check_changed)
        
        # Get path to checkmark icon for stylesheet
        import os
        checkmark_path = os.path.join(os.path.dirname(__file__), "Icons", "checkmark.svg").replace("\\", "/")
        
        self.changes_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme.colors['background']};
                border: none;
                border-radius: 8px;
                padding: 6px;
                font-family: 'Cascadia Code', 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-radius: 8px;
                margin: 3px 2px;
                border-left: 3px solid transparent;
                background-color: {theme.colors['surface']};
            }}
            QListWidget::item:hover {{
                background-color: {theme.colors['surface_hover']};
                border-left-color: {theme.colors['primary']}80;
            }}
            QListWidget::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {theme.colors['primary']}25, 
                    stop:1 {theme.colors['surface']});
                border-left-color: {theme.colors['primary']};
            }}
            QListWidget::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 6px;
                border: 2px solid {theme.colors['border']};
                background-color: {theme.colors['background']};
                margin-right: 10px;
            }}
            QListWidget::indicator:hover {{
                border-color: {theme.colors['primary']};
                background-color: {theme.colors['primary']}15;
            }}
            QListWidget::indicator:checked {{
                background-color: {theme.colors['primary']};
                border-color: {theme.colors['primary']};
                image: url({checkmark_path});
            }}
            QListWidget::indicator:checked:hover {{
                background-color: {theme.colors['primary_hover']};
                border-color: {theme.colors['primary_hover']};
                image: url({checkmark_path});
            }}
            QListWidget::indicator:unchecked:pressed {{
                background-color: {theme.colors['primary']}40;
                border-color: {theme.colors['primary']};
            }}
            QListWidget::indicator:checked:pressed {{
                background-color: {theme.colors['primary_pressed']};
                border-color: {theme.colors['primary_pressed']};
            }}
            QScrollBar:vertical {{
                background-color: transparent;
                width: 10px;
                margin: 4px 2px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {theme.colors['border']};
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme.colors['text_secondary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        self.changes_list.itemDoubleClicked.connect(self.on_change_double_clicked)
        self.changes_list.itemClicked.connect(self.on_change_clicked)
        self.changes_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        changes_layout.addWidget(self.changes_list)
        
        layout.addWidget(changes_container, 1)
        
        self.commit_header = self.create_section_header(tr('commit_title'), tr('commit_subtitle'), "git-commit")
        layout.addWidget(self.commit_header)
        
        commit_container = QFrame()
        commit_container.setObjectName("commitContainer")
        commit_container.setStyleSheet(f"""
            QFrame#commitContainer {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                border-radius: 10px;
                margin: 4px;
            }}
        """)
        commit_layout = QVBoxLayout(commit_container)
        commit_layout.setContentsMargins(12, 12, 12, 12)
        commit_layout.setSpacing(10)
        
        self.commit_summary = QLineEdit()
        self.commit_summary.setPlaceholderText(tr('commit_summary_placeholder'))
        self.commit_summary.setStyleSheet(f"""
            QLineEdit {{
                background-color: {theme.colors['background']};
                border: 2px solid {theme.colors['border']};
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
                font-weight: 600;
                color: {theme.colors['text']};
            }}
            QLineEdit:focus {{
                border-color: {theme.colors['primary']};
                background-color: {theme.colors['background']};
            }}
            QLineEdit:hover {{
                border-color: {theme.colors['text_secondary']};
            }}
        """)
        commit_layout.addWidget(self.commit_summary)

        self.commit_message = QTextEdit()
        self.commit_message.setPlaceholderText(tr('commit_placeholder'))
        self.commit_message.setMaximumHeight(90)
        self.commit_message.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.commit_message.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme.colors['background']};
                border: 2px solid {theme.colors['border']};
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 12px;
                color: {theme.colors['text']};
            }}
            QTextEdit:focus {{
                border-color: {theme.colors['primary']};
            }}
            QTextEdit:hover {{
                border-color: {theme.colors['text_secondary']};
            }}
        """)
        commit_layout.addWidget(self.commit_message)
        
        self.commit_btn = QPushButton(tr('commit_and_save'))
        self.commit_btn.setIcon(self.icon_manager.get_icon("git-commit", size=18, color="#ffffff"))
        self.commit_btn.setMinimumHeight(44)
        self.commit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.commit_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme.colors['success']}, 
                    stop:1 {theme.colors['success_hover']});
                color: {theme.colors['text_inverse']};
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 10px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {theme.colors['success_hover']}, 
                    stop:1 {theme.colors['success']});
            }}
            QPushButton:pressed {{
                background-color: {theme.colors['success_pressed']};
            }}
        """)
        self.commit_btn.setToolTip(tr('commit_and_save_tooltip'))
        self.commit_btn.clicked.connect(self.do_commit)
        commit_layout.addWidget(self.commit_btn)
        
        # Stash button
        self.stash_btn = QPushButton(tr('stash'))
        self.stash_btn.setIcon(self.icon_manager.get_icon("download", size=16))
        self.stash_btn.setMinimumHeight(36)
        self.stash_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.stash_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {theme.colors['text_secondary']};
                font-size: 12px;
                font-weight: 600;
                border: 1px solid {theme.colors['border']};
                border-radius: 8px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['surface_hover']};
                border-color: {theme.colors['primary']};
                color: {theme.colors['text']};
            }}
        """)
        self.stash_btn.setToolTip(tr('stash_changes'))
        self.stash_btn.clicked.connect(self.show_stash_dialog)
        commit_layout.addWidget(self.stash_btn)
        
        layout.addWidget(commit_container)
        
        layout.addStretch()
        
        scroll_area.setWidget(widget)
        
        self.apply_left_panel_styles()
        
        return scroll_area
    
    def _create_history_page(self):
        theme = get_current_theme()
        
        widget = QWidget()
        widget.setStyleSheet("background-color: palette(base);")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        filter_container = QFrame()
        filter_container.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['surface']};
                border-bottom: 1px solid {theme.colors['border']};
                padding: 8px;
            }}
        """)
        filter_layout = QHBoxLayout(filter_container)
        filter_layout.setContentsMargins(12, 8, 12, 8)
        
        filter_icon = QLabel()
        filter_icon.setPixmap(self.icon_manager.get_icon("filter", size=14).pixmap(14, 14))
        filter_layout.addWidget(filter_icon)
        
        self.history_filter = QLineEdit()
        self.history_filter.setPlaceholderText(tr('filter'))
        self.history_filter.setStyleSheet(f"""
            QLineEdit {{
                background-color: {theme.colors['background']};
                border: 1px solid {theme.colors['border']};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
                color: {theme.colors['text']};
            }}
            QLineEdit:focus {{
                border-color: {theme.colors['primary']};
            }}
        """)
        filter_layout.addWidget(self.history_filter, 1)
        
        layout.addWidget(filter_container)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: palette(window);
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {theme.colors['background']};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {theme.colors['border']};
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme.colors['primary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        self.commit_graph = CommitGraphWidget()
        self.commit_graph.setStyleSheet("background-color: palette(window);")
        self.commit_graph.commit_clicked.connect(self.on_graph_commit_clicked)
        self.commit_graph.commit_context_menu.connect(self.show_commit_context_menu)
        scroll.setWidget(self.commit_graph)
        
        layout.addWidget(scroll, 1)
        
        return widget
        
    def create_section_header(self, title, description, icon_name=None):
        theme = get_current_theme()
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['surface']};
                border-bottom: {theme.borders['width_thin']}px solid {theme.colors['border']};
            }}
        """)
        header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(theme.spacing['lg'], theme.spacing['lg'], 
                                 theme.spacing['lg'], theme.spacing['lg'])
        layout.setSpacing(theme.spacing['md'])
        
        if icon_name:
            icon_label = QLabel()
            icon_label.setPixmap(self.icon_manager.get_pixmap(icon_name, size=24))
            icon_label.setFixedSize(28, 28)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet("background: transparent; border: none;")
            layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(theme.spacing['xs'])
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {theme.colors['primary']};
                font-size: {theme.fonts['size_md']}px;
                font-weight: {theme.fonts['weight_bold']};
                background: transparent;
                border: none;
                padding: 0px;
            }}
        """)
        text_layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: {theme.colors['text_secondary']};
                font-size: {theme.fonts['size_xs']}px;
                background: transparent;
                border: none;
                padding: 0px;
            }}
        """)
        text_layout.addWidget(desc_label)
        
        layout.addLayout(text_layout, 1)
        layout.addStretch()
        
        header.title_label = title_label
        header.desc_label = desc_label
        
        return header
    
    def create_right_panel(self):
        theme = get_current_theme()
        widget = QWidget()
        widget.setStyleSheet("background-color: palette(window);")
        widget.setMinimumWidth(400)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Keep repo_info as a hidden label for backward compatibility
        self.repo_info = QLabel(tr('no_repo_loaded'))
        self.repo_info.hide()
        
        self.right_stack = QStackedWidget()
        
        changes_diff_page = self._create_changes_diff_view()
        self.right_stack.addWidget(changes_diff_page)
        
        history_diff_page = self._create_history_diff_view()
        self.right_stack.addWidget(history_diff_page)
        
        layout.addWidget(self.right_stack)
        
        self.apply_right_panel_styles()
        
        return widget
    
    def _create_changes_diff_view(self):
        theme = get_current_theme()
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        self.changes_diff_header = self.create_section_header(tr('diff_title'), tr('changes_subtitle'), "git-diff")
        container_layout.addWidget(self.changes_diff_header)
        
        diff_container = QWidget()
        diff_container.setStyleSheet("background-color: palette(window); padding: 10px;")
        diff_layout = QVBoxLayout(diff_container)
        diff_layout.setContentsMargins(10, 10, 10, 10)
        
        self.changes_diff_view = QTextEdit()
        self.changes_diff_view.setReadOnly(True)
        self.changes_diff_view.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme.colors['background']};
                border: 1px solid {theme.colors['border']};
                border-radius: 8px;
                font-family: 'Cascadia Code', 'Consolas', monospace;
                font-size: 12px;
                padding: 10px;
            }}
        """)
        self.changes_diff_view.setPlaceholderText(tr('select_file_diff'))
        diff_layout.addWidget(self.changes_diff_view)
        
        container_layout.addWidget(diff_container, 1)
        
        return container
    
    def _create_history_diff_view(self):
        theme = get_current_theme()
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        self.diff_header = self.create_section_header(tr('diff_title'), tr('diff_subtitle'), "git-diff")
        container_layout.addWidget(self.diff_header)
        
        diff_container = QWidget()
        diff_container.setStyleSheet("background-color: palette(window); padding: 10px;")
        diff_layout = QVBoxLayout(diff_container)
        diff_layout.setContentsMargins(10, 10, 10, 10)
        
        self.diff_scroll = QScrollArea()
        self.diff_scroll.setWidgetResizable(True)
        self.diff_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.diff_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {theme.colors['background']};
                border: 1px solid {theme.colors['border']};
                border-radius: 8px;
            }}
            QScrollBar:vertical {{
                background-color: {theme.colors['background']};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {theme.colors['border']};
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme.colors['primary']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        self.diff_files_widget = QWidget()
        self.diff_files_layout = QVBoxLayout(self.diff_files_widget)
        self.diff_files_layout.setContentsMargins(8, 8, 8, 8)
        self.diff_files_layout.setSpacing(4)
        self.diff_files_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.diff_placeholder = QLabel(tr('select_file_diff'))
        self.diff_placeholder.setStyleSheet(f"""
            color: {theme.colors['text_secondary']};
            font-size: 13px;
            padding: 40px;
        """)
        self.diff_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.diff_files_layout.addWidget(self.diff_placeholder)
        
        self.diff_scroll.setWidget(self.diff_files_widget)
        diff_layout.addWidget(self.diff_scroll)
        
        self.commit_file_items = []
        
        container_layout.addWidget(diff_container, 1)
        
        return container
        
    def show_home_view(self):
        self.stacked_widget.setCurrentWidget(self.home_view)
        if self.auto_refresh_timer.isActive():
            self.auto_refresh_timer.stop()
        
    def show_repo_view(self):
        self.stacked_widget.setCurrentWidget(self.repo_view)
        if self.repo_path and not self.auto_refresh_timer.isActive():
            self.auto_refresh_timer.start()
        if self.repo_path:
            self.refresh_status()
    
    def show_clone_view(self):
        if self.settings_manager:
            self.clone_path_combo.clear()
            paths = self.settings_manager.get_clone_paths()
            default_path = self.settings_manager.get_default_clone_path()
            
            if default_path and os.path.isdir(default_path):
                self.clone_path_combo.addItem(default_path)
            
            for path in paths:
                if path != default_path and os.path.isdir(path):
                    self.clone_path_combo.addItem(path)
            
            if self.clone_path_combo.count() == 0:
                self.clone_path_combo.setCurrentText(os.path.expanduser("~"))
            
            self.clone_create_folder_check.setChecked(self.settings_manager.get_create_repo_folder())
            self.clone_allow_non_empty_check.setChecked(self.settings_manager.get_allow_non_empty_clone())
        
        self.clone_url_input.clear()
        self.update_clone_helper()
        self.stacked_widget.setCurrentWidget(self.clone_view)
        self.clone_url_input.setFocus()
    
    def update_clone_helper(self):
        if self.clone_create_folder_check.isChecked():
            self.clone_helper_text.setText(tr('clone_helper'))
        else:
            self.clone_helper_text.setText(tr('clone_helper_direct'))
    
    def browse_clone_folder(self):
        current_path = self.clone_path_combo.currentText()
        folder = QFileDialog.getExistingDirectory(
            self,
            tr('select_folder'),
            current_path if os.path.isdir(current_path) else os.path.expanduser("~")
        )
        if folder:
            self.clone_path_combo.setCurrentText(folder)
    
    def get_repo_name_from_url(self, url):
        url = url.strip()
        if url.endswith('.git'):
            url = url[:-4]
        match = re.search(r'/([^/]+)/?$', url)
        if match:
            return match.group(1)
        return None
    
    def start_clone(self):
        url = self.clone_url_input.text().strip()
        path = self.clone_path_combo.currentText().strip()
        
        if not url:
            QMessageBox.warning(self, tr('error'), tr('clone_url_required'))
            self.clone_url_input.setFocus()
            return
        
        if not path:
            QMessageBox.warning(self, tr('error'), tr('clone_path_required'))
            self.clone_path_combo.setFocus()
            return
        
        if not os.path.isdir(path):
            QMessageBox.warning(self, tr('error'), tr('clone_path_invalid'))
            self.clone_path_combo.setFocus()
            return
        
        final_path = path
        if self.clone_create_folder_check.isChecked():
            repo_name = self.get_repo_name_from_url(url)
            if repo_name:
                final_path = os.path.join(path, repo_name)
        
        allow_non_empty = self.clone_allow_non_empty_check.isChecked()
        if os.path.isdir(final_path) and os.listdir(final_path) and not allow_non_empty:
            reply = QMessageBox.question(
                self,
                tr('folder_not_empty'),
                tr('folder_not_empty_msg'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self.show_loading(tr('cloning_repository'), url)
        
        self.clone_thread = CloneThread(self.git_manager, url, final_path)
        self.clone_thread.progress.connect(self.on_clone_progress)
        self.clone_thread.finished.connect(lambda success, msg: self.on_clone_finished(success, msg, final_path))
        self.clone_thread.start()
    
    def on_clone_progress(self, message):
        self.loading_details.setText(message)
    
    def on_clone_finished(self, success, message, path):
        if success:
            self.load_repository(path)
            if self.parent_window:
                self.parent_window.status_bar.showMessage(f"{tr('success_clone')}: {path}", 5000)
        else:
            self.show_home_view()
            QMessageBox.critical(self, tr('error_clone'), message)
        
    def on_home_open_repo(self):
        if self.parent_window:
            self.parent_window.open_repository()
            
    def on_home_clone_repo(self):
        self.show_clone_view()
    
    def load_repository(self, path):
        self.show_loading(tr('loading_repository'), path)
        QApplication.processEvents()
        
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
                tab_widget.setTabIcon(current_index, self.icon_manager.get_icon("folder-open", size=16))
        
        if not self.auto_refresh_timer.isActive():
            self.auto_refresh_timer.start()
        
        self.refresh_status()
        self._start_status_worker()
        self.update_repo_info()
        self.load_history()
        
        QTimer.singleShot(1000, self.show_repo_view)
        self.check_lfs_status()
        self.update_plugin_indicators()
        
    def toggle_ai_sidebar(self):
        """Show AI chat popup."""
        if not self.repo_path:
            QMessageBox.information(self, "AI Assistant", tr('no_repo_loaded'))
            return
        
        # Close existing popup if any
        if hasattr(self, '_ai_popup') and self._ai_popup:
            self._ai_popup.close()
            self._ai_popup = None
            return
        
        self._ai_popup = AIChatPopup(self.plugin_manager, self.repo_path, self)
        
        # Position below the AI button (centered)
        button_pos = self.ai_chat_btn.mapToGlobal(QPoint(self.ai_chat_btn.width() // 2, self.ai_chat_btn.height()))
        self._ai_popup.show_at(button_pos)
    
    def show_repo_info_dialog(self):
        """Show repository information popup."""
        if not self.repo_path:
            QMessageBox.information(self, tr('info_title'), tr('no_repo_loaded'))
            return
        
        # Close existing popup if any
        if hasattr(self, '_info_popup') and self._info_popup:
            self._info_popup.close()
        
        self._info_popup = RepoInfoPopup(self.git_manager, self.repo_path, self)
        
        # Position below the info button
        button_pos = self.info_btn.mapToGlobal(QPoint(self.info_btn.width() // 2, self.info_btn.height()))
        self._info_popup.show_at(button_pos)
        
    def get_action_button_style(self, highlight=False):
        theme = get_current_theme()
        
        bg_color = "transparent"
        border_color = "transparent"
        text_color = theme.colors['primary']
        
        if highlight:
            bg_color = f"{theme.colors['primary']}20" # 20% opacity
            border_color = theme.colors['primary']
            
        return f"""
            QPushButton {{
                color: {text_color};
                background-color: {bg_color};
                border: {theme.borders['width_thin']}px solid {border_color};
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

    def refresh_status(self):
        if not self.repo_path:
            print("[DEBUG] refresh_status: No repo_path")
            return
        self._clear_file_diff_cache()
        if self.status_future and not self.status_future.done():
            print("[DEBUG] refresh_status: Worker running, marking pending")
            self.status_worker_pending = True
            return
        print("[DEBUG] refresh_status: Starting worker")
        self.status_worker_pending = False
        self._start_status_worker()
    
    def _clear_file_diff_cache(self):
        keys_to_remove = [k for k in self.diff_cache if k.startswith("file:")]
        for k in keys_to_remove:
            del self.diff_cache[k]

    def _start_status_worker(self):
        if not self.repo_path:
            print("[DEBUG] _start_status_worker: No repo_path")
            return
        if self.status_future and not self.status_future.done():
            print("[DEBUG] _start_status_worker: Already running")
            self.status_worker_pending = True
            return
        print(f"[DEBUG] _start_status_worker: Submitting task for {self.repo_path}")
        self.status_worker_pending = False
        self.busy_message = "Loading status..."
        self.busy_timer.start()
        def task():
            print("[DEBUG] task: Calling get_status_summary")
            result = self.git_manager.get_status_summary(self.scan_large_files)
            print(f"[DEBUG] task: Got result, entries={len(result.get('entries', []))}")
            return result
        def on_done(future):
            print("[DEBUG] on_done: Future callback triggered")
            try:
                summary = future.result()
                print(f"[DEBUG] on_done: Emitting signal with {len(summary.get('entries', []))} entries")
                self.status_signals.finished.emit(summary)
            except Exception as e:
                print(f"[DEBUG] on_done: Exception {e}")
                self.status_signals.finished.emit({})
        self.status_future = self.executor.submit(task)
        self.status_future.add_done_callback(on_done)
        print("[DEBUG] _start_status_worker: Task submitted")

    def _auto_refresh_tick(self):
        if self.repo_path and self.stacked_widget.currentWidget() == self.repo_view:
            self.refresh_status()
            if not hasattr(self, '_indicator_tick_count'):
                self._indicator_tick_count = 0
            self._indicator_tick_count += 1
            if self._indicator_tick_count >= 3:
                self._indicator_tick_count = 0
                self.update_plugin_indicators()
            if not self.history_future or self.history_future.done():
                if not self.commit_graph.commits:
                    self.load_history()

    def _on_status_future(self, summary):
        print(f"[DEBUG] _on_status_future: Slot triggered with {len(summary.get('entries', []))} entries")
        self.last_status_summary = summary or {}
        self.current_branch_name = self.last_status_summary.get('branch', '')
        print("[DEBUG] _on_status_future: Applying summary")
        self.apply_status_summary()
        self._stop_busy()
        print("[DEBUG] _on_status_future: Done")
        if self.status_worker_pending:
            print("[DEBUG] _on_status_future: Restarting worker (pending=True)")
            self._start_status_worker()

    def apply_status_summary(self):
        summary = self.last_status_summary or {}
        print(f"[DEBUG] apply_status_summary: Processing summary with {len(summary.get('entries', []))} entries")

        # Update conflict section
        self.update_conflict_section()

        error_msg = summary.get('error')
        if error_msg:
            print(f"[DEBUG] apply_status_summary: Error detected: {error_msg}")
            self.changes_list.clear()
            item = QListWidgetItem(tr('error'))
            item.setIcon(self.icon_manager.get_icon("warning", size=16))
            item.setToolTip(error_msg)
            item.setForeground(QColor("#d16969"))
            font = QFont("Segoe UI", 11)
            font.setBold(True)
            item.setFont(font)
            self.changes_list.addItem(item)
            self.branch_button.setText(summary.get('branch', 'unknown'))
            return

        branch = summary.get('branch', 'unknown')
        self.branch_button.setText(branch)
        self.branch_button.setIcon(self.icon_manager.get_icon("git-branch", size=16))

        ahead = summary.get('ahead', 0)
        behind = summary.get('behind', 0)

        if behind > 0:
            self.pull_btn.setText(f"{tr('pull')} ({behind})")
            self.pull_btn.setStyleSheet(self.get_action_button_style(highlight=True))
        else:
            self.pull_btn.setText(tr('pull'))
            self.pull_btn.setStyleSheet(self.get_action_button_style(highlight=False))

        if ahead > 0:
            self.push_btn.setText(f"{tr('push')} ({ahead})")
            self.push_btn.setStyleSheet(self.get_action_button_style(highlight=True))
        else:
            self.push_btn.setText(tr('push'))
            self.push_btn.setStyleSheet(self.get_action_button_style(highlight=False))

        # Preserve selection state (checkboxes) and visual selection
        current_states = {}
        selected_paths = set()
        for i in range(self.changes_list.count()):
            item = self.changes_list.item(i)
            path = item.data(Qt.ItemDataRole.UserRole)
            if path:
                current_states[path] = item.checkState()
                if item.isSelected():
                    selected_paths.add(path)

        self.changes_list.setUpdatesEnabled(False)
        self.changes_list.clear()
        entries = summary.get('entries', [])
        self.large_files = summary.get('large_files', [])
        
        count_str = str(len(entries))
        if hasattr(self, 'changes_counter'):
            self.changes_counter.setText(count_str)
        if hasattr(self, 'changes_tab_counter'):
            self.changes_tab_counter.setText(count_str)

        if not entries:
            theme = get_current_theme()
            item = QListWidgetItem(tr('no_changes'))
            item.setIcon(self.icon_manager.get_icon("check", size=16))
            item.setForeground(QColor(theme.colors['primary']))
            font = QFont("Segoe UI", 11)
            font.setBold(True)
            item.setFont(font)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setData(Qt.ItemDataRole.UserRole, None)
            self.changes_list.addItem(item)
            self.large_files_banner.hide()
            self.changes_list.setUpdatesEnabled(True)
            return

        for entry in entries:
            file_path = entry.get('path', '')
            state = entry.get('state', '??')
            is_large = entry.get('large', False)

            is_modified = 'M' in state
            is_added = 'A' in state
            is_deleted = 'D' in state
            is_renamed = 'R' in state
            is_untracked = '?' in state
            is_conflicted = 'U' in state

            if is_conflicted:
                icon_name = "warning"
                color = "#d16969"
                tooltip = tr('conflicted')
                status_badge = "C"
            elif is_renamed:
                icon_name = "file-plus"
                color = "#569cd6"
                tooltip = tr('renamed')
                status_badge = "R"
            elif is_added:
                icon_name = "file-plus"
                color = "#4ec9b0"
                tooltip = tr('added')
                status_badge = "A"
            elif is_deleted:
                icon_name = "file-x"
                color = "#f48771"
                tooltip = tr('deleted')
                status_badge = "D"
            elif is_modified:
                icon_name = "file-text"
                color = "#dcdcaa"
                tooltip = tr('modified')
                status_badge = "M"
            elif is_untracked:
                icon_name = "file"
                color = "#858585"
                tooltip = tr('untracked')
                status_badge = "?"
            else:
                icon_name = "file"
                color = "#858585"
                tooltip = tr('untracked')
                status_badge = "?"

            if is_large:
                icon_name = "warning"
                tooltip = f"{tooltip} - LARGE FILE (>100MB)"

            # Format display with status badge
            display_text = f"[{status_badge}] {file_path}"
            
            item = QListWidgetItem(display_text)
            item.setIcon(self.icon_manager.get_icon(icon_name, size=16))
            item.setToolTip(f"{tooltip}: {file_path} ({state})")
            item.setForeground(QColor(color))

            font = QFont("Consolas", 11)
            item.setFont(font)
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            item.setData(Qt.ItemDataRole.UserRole + 1, state)  # Store git state
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            
            # Restore checkbox state
            if file_path in current_states:
                item.setCheckState(current_states[file_path])
            else:
                item.setCheckState(Qt.CheckState.Checked)
                
            self.changes_list.addItem(item)

        # Restore visual selection AFTER all items are added
        if selected_paths:
            for i in range(self.changes_list.count()):
                item = self.changes_list.item(i)
                path = item.data(Qt.ItemDataRole.UserRole)
                if path and path in selected_paths:
                    item.setSelected(True)

        # Reactivar actualizaciones
        self.changes_list.setUpdatesEnabled(True)
        
        # Actualizar contador de archivos marcados
        self.update_checked_counter()

        if self.large_files:
            self.large_files_label.setText(tr('large_files_detected', count=len(self.large_files)))
            self.large_files_banner.show()
        else:
            self.large_files_banner.hide()

    def track_large_files(self):
        if not self.large_files:
            return
            
        dialog = LFSTrackingDialog(self.git_manager, self.plugin_manager, self, suggested_files=self.large_files)
        dialog.exec()
        self.refresh_status()
            
    def on_change_double_clicked(self, item):
        pass
    
    def on_change_clicked(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if not file_path:
            return
        diff = self.git_manager.get_file_diff(file_path)
        if diff:
            formatted = self.format_diff(diff)
            self.changes_diff_view.setHtml(formatted)
        else:
            self.changes_diff_view.setPlainText(tr('no_changes'))
        
    def stage_all(self):
        success, message = self.git_manager.stage_all()
        if success:
            self.refresh_status()
            QMessageBox.information(self, tr('success'), tr('success_all_files_added'))
        else:
            QMessageBox.warning(self, tr('error'), message)
    
    def get_checked_items(self):
        checked_items = []
        for i in range(self.changes_list.count()):
            item = self.changes_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked_items.append(item)
        return checked_items

    def stage_selected(self):
        items_to_process = self.get_checked_items()
        if not items_to_process:
            current_item = self.changes_list.currentItem()
            if current_item:
                items_to_process.append(current_item)
        
        if not items_to_process:
            return

        errors = []
        for item in items_to_process:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            success, message = self.git_manager.stage_file(file_path)
            if not success:
                errors.append(f"{file_path}: {message}")
        
        self.refresh_status()
        
        if errors:
            QMessageBox.warning(self, tr('error'), "\n".join(errors))
                
    def unstage_selected(self):
        items_to_process = self.get_checked_items()
        if not items_to_process:
            current_item = self.changes_list.currentItem()
            if current_item:
                items_to_process.append(current_item)
        
        if not items_to_process:
            return

        errors = []
        for item in items_to_process:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            success, message = self.git_manager.unstage_file(file_path)
            if not success:
                errors.append(f"{file_path}: {message}")
        
        self.refresh_status()
        
        if errors:
            QMessageBox.warning(self, tr('error'), "\n".join(errors))

    def show_changes_context_menu(self, position):
        item = self.changes_list.itemAt(position)
        if not item:
            return
            
        file_path = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        theme = get_current_theme()
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                padding: 8px;
                border-radius: 8px;
            }}
            QMenu::item {{
                padding: 10px 20px;
                color: {theme.colors['text']};
                border-radius: 4px;
                margin: 2px 4px;
            }}
            QMenu::item:selected {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['text_inverse']};
            }}
            QMenu::item:disabled {{
                color: {theme.colors['text_secondary']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {theme.colors['border']};
                margin: 8px 10px;
            }}
        """)
        
        file_name = os.path.basename(file_path) if file_path else "archivo"
        header = QAction(file_name, self)
        header.setIcon(self.icon_manager.get_icon('file-doc', size=16))
        header.setEnabled(False)
        menu.addAction(header)
        menu.addSeparator()
        
        # Show in folder
        show_folder_action = QAction(tr('show_in_folder'), self)
        show_folder_action.setIcon(self.icon_manager.get_icon("folder-open", size=16))
        show_folder_action.triggered.connect(lambda: self.show_in_folder(file_path))
        menu.addAction(show_folder_action)
        
        # Copy path submenu
        copy_menu = QMenu(tr('copy'), self)
        copy_menu.setIcon(self.icon_manager.get_icon("copy", size=16))
        copy_menu.setStyleSheet(menu.styleSheet())
        
        copy_abs_action = QAction(tr('copy_absolute_path'), self)
        copy_abs_action.setIcon(self.icon_manager.get_icon("link", size=16))
        copy_abs_action.triggered.connect(lambda: self.copy_file_path(file_path, absolute=True))
        copy_menu.addAction(copy_abs_action)
        
        copy_rel_action = QAction(tr('copy_relative_path'), self)
        copy_rel_action.setIcon(self.icon_manager.get_icon("link-simple", size=16))
        copy_rel_action.triggered.connect(lambda: self.copy_file_path(file_path, absolute=False))
        copy_menu.addAction(copy_rel_action)
        
        menu.addMenu(copy_menu)
        
        menu.addSeparator()
        
        # Single discard option - smart based on selection
        selected_items = self.changes_list.selectedItems()
        selected_files = [item for item in selected_items if item.data(Qt.ItemDataRole.UserRole)]
        selected_count = len(selected_files)
        
        if selected_count > 1:
            # Multiple files selected - discard all selected (files icon)
            discard_action = QAction(tr('discard_n_files', count=selected_count), self)
            discard_action.setIcon(self.icon_manager.get_icon("files", size=16))
            discard_action.triggered.connect(self.discard_selected_items)
        else:
            # Single file or no selection - discard clicked file (single file icon)
            discard_action = QAction(tr('discard_file', file=file_name), self)
            discard_action.setIcon(self.icon_manager.get_icon("file-x", size=16))
            discard_action.triggered.connect(lambda: self.discard_file_context(file_path))
        menu.addAction(discard_action)
        
        menu.addSeparator()
        
        ignore_action = QAction(tr('add_to_gitignore'), self)
        ignore_action.setIcon(self.icon_manager.get_icon("file-x", size=16))
        ignore_action.triggered.connect(lambda: self.add_to_gitignore(file_path))
        menu.addAction(ignore_action)
        
        lfs_action = QAction(tr('add_to_lfs'), self)
        lfs_action.setIcon(self.icon_manager.get_icon("lfs-icon", size=16))
        lfs_action.triggered.connect(lambda: self.add_to_lfs(file_path))
        menu.addAction(lfs_action)
        
        menu.exec(self.changes_list.mapToGlobal(position))

    def show_in_folder(self, file_path):
        """Open the folder containing the file in the system file explorer with the file selected"""
        if not self.repo_path or not file_path:
            return
        full_path = os.path.normpath(os.path.join(self.repo_path, file_path))
        if sys.platform == 'win32':
            # Use explorer.exe /select, to highlight the file
            import subprocess
            explorer_path = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'explorer.exe')
            subprocess.Popen([explorer_path, '/select,', full_path])
        elif sys.platform == 'darwin':
            import subprocess
            subprocess.run(['open', '-R', full_path])
        else:
            # Linux: open folder (file selection not universally supported)
            folder_path = os.path.dirname(full_path)
            if os.path.exists(folder_path):
                import subprocess
                subprocess.run(['xdg-open', folder_path])

    def copy_file_path(self, file_path, absolute=True):
        """Copy the file path to clipboard"""
        if not file_path:
            return
        if absolute and self.repo_path:
            path_to_copy = os.path.join(self.repo_path, file_path)
        else:
            path_to_copy = file_path
        
        clipboard = QApplication.clipboard()
        clipboard.setText(path_to_copy)

    def add_to_gitignore(self, file_path):
        success, message = self.git_manager.add_to_gitignore(file_path)
        if success:
            QMessageBox.information(self, tr('success'), tr('success_gitignore_added', file=file_path))
            self.refresh_status()
        else:
            QMessageBox.warning(self, tr('error'), message)

    def add_to_lfs(self, file_path):
        success, message = self.git_manager.lfs_track_files([file_path])
        if success:
            QMessageBox.information(self, tr('success'), tr('success_lfs_added', file=file_path))
            self.refresh_status()
        else:
            QMessageBox.warning(self, tr('error'), message)

    def on_item_check_changed(self, item):
        # Actualizar contador de archivos marcados
        self.update_checked_counter()
    
    def update_checked_counter(self):
        """Update the counter showing how many files are checked for commit"""
        checked_count = 0
        total_count = 0
        for i in range(self.changes_list.count()):
            item = self.changes_list.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                total_count += 1
                if item.checkState() == Qt.CheckState.Checked:
                    checked_count += 1
        
        if hasattr(self, 'checked_label'):
            self.checked_label.setText(tr('checked_for_commit', checked=checked_count, total=total_count))
        
        # Update toggle button state based on current state
        if hasattr(self, '_all_checked') and hasattr(self, 'toggle_select_btn'):
            if checked_count == total_count and total_count > 0:
                self._all_checked = True
                self.toggle_select_btn.setIcon(self.icon_manager.get_icon("check-square", size=14, color="#ffffff"))
                self.toggle_select_btn.setToolTip(tr('deselect_all'))
            elif checked_count == 0:
                self._all_checked = False
                self.toggle_select_btn.setIcon(self.icon_manager.get_icon("square", size=14, color="#ffffff"))
                self.toggle_select_btn.setToolTip(tr('select_all'))
    
    def discard_selected_items(self):
        """Discard changes for all selected items (multi-select via Ctrl/Shift)"""
        selected_items = self.changes_list.selectedItems()
        file_paths = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items if item.data(Qt.ItemDataRole.UserRole)]
        
        if not file_paths:
            return
        
        file_count = len(file_paths)
        if file_count == 1:
            msg = tr('confirm_discard_text', file=os.path.basename(file_paths[0]))
        else:
            msg = tr('confirm_discard_n_files', count=file_count)
        
        reply = QMessageBox.question(
            self,
            tr('confirm_discard'),
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            errors = []
            for file_path in file_paths:
                success, message = self.git_manager.discard_file(file_path)
                if not success:
                    errors.append(f"{file_path}: {message}")
            
            if errors:
                QMessageBox.warning(self, tr('error'), "\n".join(errors))
            
            self.refresh_status()

    # ==================== CONFLICT METHODS ====================
    
    def update_conflict_section(self):
        """Update the conflict section visibility and content"""
        if not hasattr(self, 'conflict_container'):
            return
            
        conflicted_files = self.git_manager.get_conflicted_files()
        is_merging = self.git_manager.get_merge_status()
        
        if conflicted_files or is_merging:
            self.conflict_container.setVisible(True)
            self.conflict_counter.setText(str(len(conflicted_files)))
            
            self.conflict_list.clear()
            for file_path in conflicted_files:
                item = QListWidgetItem(file_path)
                item.setIcon(self.icon_manager.get_icon("warning", size=16))
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                self.conflict_list.addItem(item)
            
            # Enable/disable continue button based on conflicts
            self.continue_merge_btn.setEnabled(len(conflicted_files) == 0 and is_merging)
        else:
            self.conflict_container.setVisible(False)
    
    def show_conflict_context_menu(self, position):
        """Show context menu for conflict resolution"""
        item = self.conflict_list.itemAt(position)
        if not item:
            return
            
        file_path = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        theme = get_current_theme()
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                padding: 8px;
                border-radius: 8px;
            }}
            QMenu::item {{
                padding: 10px 20px;
                color: {theme.colors['text']};
                border-radius: 4px;
                margin: 2px 4px;
            }}
            QMenu::item:selected {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['text_inverse']};
            }}
        """)
        
        file_name = os.path.basename(file_path)
        header = QAction(f"⚠️ {file_name}", self)
        header.setEnabled(False)
        menu.addAction(header)
        menu.addSeparator()
        
        ours_action = QAction(tr('use_ours'), self)
        ours_action.setIcon(self.icon_manager.get_icon("git-branch", size=16))
        ours_action.triggered.connect(lambda: self.resolve_conflict_ours(file_path))
        menu.addAction(ours_action)
        
        theirs_action = QAction(tr('use_theirs'), self)
        theirs_action.setIcon(self.icon_manager.get_icon("git-merge", size=16))
        theirs_action.triggered.connect(lambda: self.resolve_conflict_theirs(file_path))
        menu.addAction(theirs_action)
        
        menu.addSeparator()
        
        resolved_action = QAction(tr('mark_resolved'), self)
        resolved_action.setIcon(self.icon_manager.get_icon("check-circle", size=16))
        resolved_action.triggered.connect(lambda: self.mark_conflict_resolved(file_path))
        menu.addAction(resolved_action)
        
        menu.exec(self.conflict_list.mapToGlobal(position))
    
    def resolve_conflict_ours(self, file_path):
        """Resolve conflict using our version"""
        success, msg = self.git_manager.resolve_conflict_ours(file_path)
        if success:
            QMessageBox.information(self, tr('success'), tr('conflict_resolved', file=file_path))
            self.refresh_status()
        else:
            QMessageBox.warning(self, tr('error'), msg)
    
    def resolve_conflict_theirs(self, file_path):
        """Resolve conflict using their version"""
        success, msg = self.git_manager.resolve_conflict_theirs(file_path)
        if success:
            QMessageBox.information(self, tr('success'), tr('conflict_resolved', file=file_path))
            self.refresh_status()
        else:
            QMessageBox.warning(self, tr('error'), msg)
    
    def mark_conflict_resolved(self, file_path):
        """Mark a conflict as resolved after manual edit"""
        success, msg = self.git_manager.mark_resolved(file_path)
        if success:
            QMessageBox.information(self, tr('success'), tr('conflict_resolved', file=file_path))
            self.refresh_status()
        else:
            QMessageBox.warning(self, tr('error'), msg)
    
    def abort_merge(self):
        """Abort the current merge"""
        reply = QMessageBox.question(
            self,
            tr('confirm'),
            tr('confirm_discard'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.git_manager.abort_merge()
            if success:
                QMessageBox.information(self, tr('success'), tr('merge_aborted'))
                self.refresh_status()
            else:
                QMessageBox.warning(self, tr('error'), msg)
    
    def continue_merge(self):
        """Continue merge after resolving all conflicts"""
        if self.git_manager.has_conflicts():
            QMessageBox.warning(self, tr('error'), tr('resolve_all_conflicts'))
            return
        
        success, msg = self.git_manager.continue_merge()
        if success:
            QMessageBox.information(self, tr('success'), tr('merge_continued'))
            self.refresh_status()
        else:
            QMessageBox.warning(self, tr('error'), msg)

    def toggle_all_changes(self):
        """Toggle entre seleccionar todos / deseleccionar todos"""
        self.changes_list.setUpdatesEnabled(False)
        try:
            # Determine new state (toggle)
            new_state = Qt.CheckState.Unchecked if self._all_checked else Qt.CheckState.Checked
            
            for i in range(self.changes_list.count()):
                item = self.changes_list.item(i)
                if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                    item.setCheckState(new_state)
            
            # Update toggle state and button icon
            self._all_checked = not self._all_checked
            if self._all_checked:
                self.toggle_select_btn.setIcon(self.icon_manager.get_icon("check-square", size=14, color="#ffffff"))
                self.toggle_select_btn.setToolTip(tr('deselect_all'))
            else:
                self.toggle_select_btn.setIcon(self.icon_manager.get_icon("square", size=14, color="#ffffff"))
                self.toggle_select_btn.setToolTip(tr('select_all'))
        finally:
            self.changes_list.setUpdatesEnabled(True)
            self.update_checked_counter()

    def stage_file_single(self, file_path):
        success, message = self.git_manager.stage_file(file_path)
        if success:
            self.refresh_status()
        else:
            QMessageBox.warning(self, tr('error'), message)

    def unstage_file_single(self, file_path):
        success, message = self.git_manager.unstage_file(file_path)
        if success:
            self.refresh_status()
        else:
            QMessageBox.warning(self, tr('error'), message)

    def discard_file_context(self, file_path):
        reply = QMessageBox.question(
            self,
            tr('confirm_discard'),
            tr('confirm_discard_text', file=file_path),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.git_manager.discard_file(file_path)
            if success:
                self.refresh_status()
            else:
                QMessageBox.warning(self, tr('error'), message)
    
    def discard_selected_changes(self):
        checked_items = self.get_checked_items()
        if not checked_items:
            QMessageBox.warning(self, tr('warning'), tr('no_files_selected'))
            return
        
        file_paths = [item.data(Qt.ItemDataRole.UserRole) for item in checked_items if item.data(Qt.ItemDataRole.UserRole)]
        
        if not file_paths:
            QMessageBox.warning(self, tr('warning'), tr('no_valid_files_selected'))
            return
        
        file_count = len(file_paths)
        reply = QMessageBox.question(
            self,
            tr('confirm_discard'),
            tr('confirm_discard_n_files', count=file_count),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            errors = []
            for file_path in file_paths:
                success, message = self.git_manager.discard_file(file_path)
                if not success:
                    errors.append(f"{file_path}: {message}")
            
            self.refresh_status()
            
            if errors:
                QMessageBox.warning(self, tr('error'), "\n".join(errors))
            else:
                QMessageBox.information(self, tr('success'), tr('files_discarded', count=file_count))

    def show_stash_dialog(self):
        """Show the stash management dialog"""
        if not self.repo_path:
            QMessageBox.warning(self, tr('error'), tr('no_repository'))
            return
        dialog = StashDialog(self.git_manager, self)
        dialog.exec()
        self.refresh_status()
                
    def do_commit(self):
        summary = self.commit_summary.text().strip()
        description = self.commit_message.toPlainText().strip()

        if not summary:
            QMessageBox.warning(self, tr('error'), tr('error_commit_message'))
            return

        # Collect selected files
        files_to_stage = []
        for i in range(self.changes_list.count()):
            item = self.changes_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                file_path = item.data(Qt.ItemDataRole.UserRole)
                if file_path:
                    files_to_stage.append(file_path)
        
        if not files_to_stage:
             QMessageBox.warning(self, tr('error'), tr('error_no_files_selected'))
             return

        if description:
            message = f"{summary}\n\n{description}"
        else:
            message = summary

        # 1. Unstage all (to ensure clean state based on selection)
        self.git_manager.unstage_all()
        
        # 2. Stage selected files
        success, result = self.git_manager.stage_files(files_to_stage)
        if not success:
            QMessageBox.warning(self, tr('error'), tr('error_staging_files', message=result))
            return

        # 3. Commit
        success, result = self.git_manager.commit(message)
        if success:
            self.commit_summary.clear()
            self.commit_message.clear()
            self.refresh_status()
            self.load_history()
        else:
            QMessageBox.warning(self, tr('error'), result)
            
    def handle_git_error(self, title, message):
        if "502" in message and "Bad Gateway" in message:
            QMessageBox.warning(self, title, tr('git_error_502'))
        elif "unable to access" in message or "Could not resolve host" in message:
            QMessageBox.warning(self, title, f"{tr('git_error_connection')}\n\n{message}")
        elif "Authentication failed" in message or "403" in message:
            QMessageBox.warning(self, title, f"{tr('git_error_auth')}\n\n{message}")
        else:
            QMessageBox.warning(self, title, message)

    def do_pull(self):
        self.run_git_operation(self.git_manager.pull, "Pulling changes...")
            
    def do_push(self):
        self.push_dialog = PushProgressDialog(self)
        self.push_dialog.show()
        
        self.push_thread = PushThread(self.git_manager)
        self.push_thread.progress.connect(self.on_push_progress)
        self.push_thread.finished.connect(self.on_push_finished)
        self.push_thread.start()
            
    def do_fetch(self):
        self.run_git_operation(self.git_manager.fetch, "Fetching changes...")

    def run_git_operation(self, operation, status_message):
        if self.git_op_future and not self.git_op_future.done():
            return
        if self.parent_window:
            self.parent_window.status_label.setText(status_message)
            self.parent_window.progress_label.setText("...")
        self.busy_message = status_message
        self.busy_timer.start()
        self.git_op_future = self.executor.submit(operation)
        self.git_op_future.add_done_callback(lambda f: QTimer.singleShot(0, lambda: self._on_git_future(f)))
        
    def on_push_progress(self, line):
        if hasattr(self, 'push_dialog') and self.push_dialog:
            speed_match = re.search(r'([\d.]+\s*[KMG]iB/s)', line)
            percent_match = re.search(r'(\d+)%', line)
            bytes_match = re.search(r'([\d.]+\s*[KMG]iB)(?!/s)', line)
            
            info_parts = []
            if percent_match:
                self.push_dialog.set_percent(int(percent_match.group(1)))
                info_parts.append(f"{percent_match.group(1)}%")
            else:
                self.push_dialog.set_percent(None)
            if bytes_match:
                info_parts.append(f"{bytes_match.group(1)}")
            if speed_match:
                info_parts.append(f"{speed_match.group(1)}")
            
            if info_parts:
                self.push_dialog.set_details(' | '.join(info_parts))
    
    def on_push_finished(self, success, message):
        if hasattr(self, 'push_dialog') and self.push_dialog:
            self.push_dialog.close()
            self.push_dialog = None
        
        if self.parent_window:
            self.parent_window.status_label.setText(tr('ready'))
            self.parent_window.progress_label.setText(message if success else "Failed")
            QTimer.singleShot(5000, self.parent_window.progress_label.clear)
            
        if success:
            self.refresh_status()
            self.load_history()
            QMessageBox.information(self, tr('success'), tr('push_success'))
        else:
            self.handle_git_error(tr('error'), message)
    
    def on_git_operation_finished(self, success, message):
        if self.parent_window:
            self.parent_window.status_label.setText(tr('ready'))
            self.parent_window.progress_label.setText(message if success else "Failed")
            QTimer.singleShot(5000, self.parent_window.progress_label.clear)
            
        if success:
            self.refresh_status()
            self.load_history()
        else:
            self.handle_git_error(tr('error'), message)

    def _on_git_future(self, future):
        try:
            result = future.result()
        except Exception as e:
            result = (False, str(e))
        if isinstance(result, tuple) and len(result) == 2:
            success, message = result
        else:
            success, message = True, "Done"
        self._stop_busy()
        self.on_git_operation_finished(success, message)
            
    def update_repo_info(self):
        if not self.repo_path:
            return
            
        info = self.git_manager.get_repository_info()
        
        info_text = f"""
<b>{tr('path')}:</b> {self.repo_path}<br>
<b>{tr('current_branch_info')}:</b> {info.get('branch', 'N/A')}<br>
<b>{tr('remote')}:</b> {info.get('remote', 'N/A')}<br>
<b>{tr('last_commit')}:</b> {info.get('last_commit', 'N/A')}<br>
        """
        self.repo_info.setText(info_text)
        
    def load_history(self):
        print(f"[DEBUG] load_history: Starting, repo_path={self.repo_path}")
        if not self.repo_path:
            print("[DEBUG] load_history: No repo_path, returning")
            return
        if self.history_future and not self.history_future.done():
            print("[DEBUG] load_history: history_future still running, marking pending")
            self.history_worker_pending = True
            return
        print("[DEBUG] load_history: Submitting history task")
        branch = self.current_branch_name or self.git_manager.get_current_branch()
        self.history_branch_requested = branch
        self.history_worker_pending = False
        self.busy_message = "Loading history..."
        self.busy_timer.start()
        
        signals = HistoryWorkerSignals()
        signals.finished.connect(self._on_history_result)
        
        def task():
            result = self.git_manager.get_commit_history(50)
            print(f"[DEBUG] history task: Got {len(result)} commits")
            return result
        
        def on_done(future):
            try:
                result = future.result()
            except Exception as e:
                print(f"[DEBUG] history on_done: Exception {e}")
                result = []
            print(f"[DEBUG] history on_done: Emitting signal with {len(result)} commits")
            signals.finished.emit(result)
        
        self.history_future = self.executor.submit(task)
        self.history_future.add_done_callback(on_done)

    def _on_history_result(self, history):
        print(f"[DEBUG] _on_history_result: received {len(history)} commits")
        if not history:
            self._stop_busy()
            if self.history_worker_pending:
                self.load_history()
            return

        formatted_commits = []
        for commit in history:
            formatted_commit = {
                'hash': commit['hash'],
                'message': commit['message'],
                'author': commit['author'],
                'email': commit.get('email', ''),
                'date': commit['date'],
                'branch': self.history_branch_requested
            }
            formatted_commits.append(formatted_commit)

            email = commit.get('email', '')
            if email and email not in self.avatar_cache:
                self.download_gravatar(email, commit['author'])

        print(f"[DEBUG] _on_history_result: setting {len(formatted_commits)} commits on graph")
        self.commit_graph.set_commits(formatted_commits)
        self._stop_busy()
        
        self._preload_commit_diffs(formatted_commits[:10])

        if self.history_worker_pending:
            self.load_history()
    
    def _preload_commit_diffs(self, commits):
        for commit in commits:
            commit_hash = commit['hash']
            if commit_hash not in self.diff_cache:
                self.executor.submit(self._preload_single_diff, commit_hash)
    
    def _preload_single_diff(self, commit_hash):
        try:
            if commit_hash in self.diff_cache:
                return
            files = self.git_manager.get_commit_files(commit_hash)
            file_diffs = {}
            for f in files:
                diff = self.git_manager.get_commit_file_diff(commit_hash, f['path'])
                file_diffs[f['path']] = {'status': f['status'], 'diff': diff}
            if len(self.diff_cache) < self.diff_cache_max_size:
                self.diff_cache[commit_hash] = file_diffs
        except Exception:
            pass
            
    def on_graph_commit_clicked(self, commit_hash):
        if commit_hash:
            self._request_commit_diff(commit_hash)
    
    def on_commit_selected(self, item):
        commit_hash = item.data(Qt.ItemDataRole.UserRole)
        if commit_hash:
            self._request_commit_diff(commit_hash)
    
    def _request_commit_diff(self, commit_hash):
        self.pending_diff_commit = commit_hash
        if commit_hash in self.diff_cache:
            cached = self.diff_cache[commit_hash]
            if isinstance(cached, dict):
                self._display_commit_files(commit_hash, cached)
                return
            else:
                del self.diff_cache[commit_hash]
        self.diff_debounce_timer.start()
    
    def _load_pending_diff(self):
        commit_hash = self.pending_diff_commit
        if not commit_hash:
            return
        if commit_hash in self.diff_cache:
            cached = self.diff_cache[commit_hash]
            if isinstance(cached, dict):
                self._display_commit_files(commit_hash, cached)
                return
            else:
                del self.diff_cache[commit_hash]
        self.executor.submit(self._fetch_and_display_diff, commit_hash)
    
    def _fetch_and_display_diff(self, commit_hash):
        try:
            files = self.git_manager.get_commit_files(commit_hash)
            file_diffs = {}
            for f in files:
                diff = self.git_manager.get_commit_file_diff(commit_hash, f['path'])
                file_diffs[f['path']] = {'status': f['status'], 'diff': diff}
            
            if len(self.diff_cache) >= self.diff_cache_max_size:
                try:
                    oldest_key = next(iter(self.diff_cache))
                    del self.diff_cache[oldest_key]
                except StopIteration:
                    pass
            self.diff_cache[commit_hash] = file_diffs
            QTimer.singleShot(0, lambda: self._display_commit_files(commit_hash, file_diffs))
        except Exception:
            pass
    
    def _display_commit_files(self, commit_hash, file_diffs):
        if self.pending_diff_commit != commit_hash:
            return
            
        for item in self.commit_file_items:
            item.setParent(None)
            item.deleteLater()
        self.commit_file_items.clear()
        
        self.diff_placeholder.setVisible(False)
        
        if not file_diffs:
            self.diff_placeholder.setVisible(True)
            return
            
        for file_path, data in file_diffs.items():
            item = CommitFileItem(
                file_path, 
                data['status'], 
                data['diff'], 
                self.icon_manager
            )
            self.commit_file_items.append(item)
            self.diff_files_layout.addWidget(item)
    
    def format_diff(self, diff_text):
        import html
        theme = get_current_theme()
        lines = diff_text.split('\n')
        
        colors = theme.colors
        parts = [f'<div style="font-family: Consolas, Monaco, monospace; font-size: 13px; line-height: 1.5; color: {colors["text"]};">']
        
        style_commit = f'style="color: {colors["warning"]}; font-weight: bold; font-size: 14px; padding: 10px 0 5px 0;"'
        style_author = f'style="color: {colors["text"]}; padding-bottom: 2px;"'
        style_author_span = f'style="color: {colors["text_secondary"]};"'
        style_date = f'style="color: {colors["text"]}; padding-bottom: 15px; border-bottom: 1px solid {colors["border"]}; margin-bottom: 15px;"'
        style_diff_header = f'style="color: {colors["primary"]}; font-weight: bold; margin-top: 20px; padding: 8px; background-color: {colors["surface"]}; border-radius: 5px; border: 1px solid {colors["border"]};"'
        style_meta = f'style="color: {colors["text_secondary"]}; padding-left: 10px; font-size: 11px;"'
        style_file_marker = f'style="color: {colors["text_secondary"]}; padding-left: 10px;"'
        style_hunk = f'style="color: {colors["secondary"]}; background-color: {colors["surface"]}; margin: 5px 0; padding: 4px 8px; border-radius: 3px;"'
        style_add = f'style="background-color: {colors["diff_add_bg"]}; color: {colors["diff_add_text"]}; white-space: pre-wrap;"'
        style_del = f'style="background-color: {colors["diff_del_bg"]}; color: {colors["diff_del_text"]}; white-space: pre-wrap;"'
        style_default = 'style="white-space: pre-wrap;"'
        
        for line in lines:
            line_content = html.escape(line)
            
            if line.startswith('commit '):
                parts.append(f'<div {style_commit}>{line_content}</div>')
            elif line.startswith('Author: '):
                parts.append(f'<div {style_author}><span {style_author_span}>Author: </span>{line_content[8:]}</div>')
            elif line.startswith('Date:   '):
                parts.append(f'<div {style_date}><span {style_author_span}>Date: </span>{line_content[8:]}</div>')
            elif line.startswith('diff --git'):
                parts.append(f'<div {style_diff_header}>{line_content}</div>')
            elif line.startswith('index ') or line.startswith('new file mode') or line.startswith('deleted file mode'):
                parts.append(f'<div {style_meta}>{line_content}</div>')
            elif line.startswith('---') or line.startswith('+++'):
                parts.append(f'<div {style_file_marker}>{line_content}</div>')
            elif line.startswith('@@'):
                parts.append(f'<div {style_hunk}>{line_content}</div>')
            elif line.startswith('+') and not line.startswith('+++'):
                parts.append(f'<div {style_add}>{line_content}</div>')
            elif line.startswith('-') and not line.startswith('---'):
                parts.append(f'<div {style_del}>{line_content}</div>')
            else:
                parts.append(f'<div {style_default}>{line_content}</div>')
        
        parts.append('</div>')
        return ''.join(parts)
    
    def show_commit_context_menu(self, commit_hash):
        if not commit_hash:
            return
            
        menu = QMenu(self)
        theme = get_current_theme()
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                padding: 8px;
                border-radius: 8px;
            }}
            QMenu::item {{
                padding: 10px 20px;
                color: {theme.colors['text']};
                border-radius: 4px;
                margin: 2px 4px;
            }}
            QMenu::item:selected {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['text_inverse']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {theme.colors['border']};
                margin: 8px 10px;
            }}
        """)
        
        hash_short = commit_hash[:7]
        
        header = QAction(f"Commit: {hash_short}", self)
        header.setIcon(self.icon_manager.get_icon('pin', size=16))
        header.setEnabled(False)
        menu.addAction(header)
        menu.addSeparator()
        
        copy_action = QAction(tr('copy_hash'), self)
        copy_action.setIcon(self.icon_manager.get_icon("copy", size=16))
        copy_action.triggered.connect(lambda: self.copy_commit_hash(commit_hash))
        menu.addAction(copy_action)
        
        menu.addSeparator()
        
        branch_action = QAction(tr('create_branch_from_commit'), self)
        branch_action.setIcon(self.icon_manager.get_icon("git-branch", size=16))
        branch_action.triggered.connect(lambda: self.create_branch_from_commit_quick(commit_hash))
        menu.addAction(branch_action)
        
        checkout_action = QAction(tr('checkout_commit'), self)
        checkout_action.setIcon(self.icon_manager.get_icon("git-checkout", size=16))
        checkout_action.triggered.connect(lambda: self.checkout_commit_quick(commit_hash))
        menu.addAction(checkout_action)
        
        menu.addSeparator()
        
        reset_menu = QMenu(tr('reset_to_commit'), self)
        reset_menu.setIcon(self.icon_manager.get_icon("history", size=16))
        reset_menu.setStyleSheet(menu.styleSheet())
        
        soft_action = QAction(f"{tr('reset_soft')} - {tr('reset_soft_desc')}", self)
        soft_action.setIcon(self.icon_manager.get_icon('circle-green', size=16))
        soft_action.triggered.connect(lambda: self.reset_commit_quick(commit_hash, 'soft'))
        reset_menu.addAction(soft_action)
        
        mixed_action = QAction(f"{tr('reset_mixed')} - {tr('reset_mixed_desc')}", self)
        mixed_action.setIcon(self.icon_manager.get_icon('circle-yellow', size=16))
        mixed_action.triggered.connect(lambda: self.reset_commit_quick(commit_hash, 'mixed'))
        reset_menu.addAction(mixed_action)
        
        hard_action = QAction(f"{tr('reset_hard')} - {tr('reset_hard_desc')}", self)
        hard_action.setIcon(self.icon_manager.get_icon('circle-red', size=16))
        hard_action.triggered.connect(lambda: self.reset_commit_quick(commit_hash, 'hard'))
        reset_menu.addAction(hard_action)
        
        menu.addMenu(reset_menu)
        
        revert_action = QAction(tr('revert_commit'), self)
        revert_action.setIcon(self.icon_manager.get_icon("undo", size=16))
        revert_action.triggered.connect(lambda: self.revert_commit_quick(commit_hash))
        menu.addAction(revert_action)
        
        menu.exec(QCursor.pos())
    
    def revert_commit_quick(self, commit_hash):
        reply = QMessageBox.question(
            self,
            tr('confirm_revert'),
            tr('revert_question', hash=commit_hash[:7]),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.git_manager.revert_commit(commit_hash)
            if success:
                QMessageBox.information(self, tr('success'), tr('success_revert', hash=commit_hash[:7]))
                self.refresh_status()
                self.load_history()
            else:
                QMessageBox.warning(self, tr('error'), f"{tr('error_revert')}:\n{message}")
    
    def create_branch_from_commit_quick(self, commit_hash):
        branch_name, ok = QInputDialog.getText(
            self,
            tr('create_branch_from_commit'),
            tr('create_branch_from_commit_text', hash=commit_hash[:7]),
            QLineEdit.EchoMode.Normal,
            ""
        )
        
        if ok and branch_name:
            success, message = self.git_manager.create_branch(branch_name, commit_hash)
            if success:
                QMessageBox.information(
                    self,
                    tr('success'),
                    tr('branch_created_from_commit', branch=commit_hash[:7])
                )
                self.refresh_status()
            else:
                QMessageBox.warning(self, tr('error'), f"{tr('error_create_branch')}:\n{message}")
    
    def reset_commit_quick(self, commit_hash, mode):
        mode_names = {
            'soft': tr('reset_soft'),
            'mixed': tr('reset_mixed'),
            'hard': tr('reset_hard')
        }
        
        warning = ""
        if mode == 'hard':
            warning = tr('reset_warning')
        
        reply = QMessageBox.question(
            self,
            tr('confirm_reset'),
            tr('reset_question', mode=mode_names[mode], hash=commit_hash[:7], warning=warning),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.git_manager.reset_to_commit(commit_hash, mode)
            if success:
                QMessageBox.information(self, tr('success'), tr('success_reset', mode=mode))
                self.refresh_status()
                self.load_history()
                self.update_repo_info()
            else:
                QMessageBox.warning(self, tr('error'), f"{tr('error_reset')}:\n{message}")
    
    def checkout_commit_quick(self, commit_hash):
        reply = QMessageBox.question(
            self,
            tr('confirm_checkout'),
            tr('checkout_question', hash=commit_hash[:7]),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.git_manager.checkout_commit(commit_hash)
            if success:
                QMessageBox.information(
                    self,
                    tr('success'),
                    tr('checkout_success', hash=commit_hash[:7])
                )
                self.refresh_status()
                self.update_repo_info()
            else:
                QMessageBox.warning(self, tr('error'), f"{tr('error')}:\n{message}")
    
    def copy_commit_hash(self, commit_hash):
        clipboard = QApplication.clipboard()
        clipboard.setText(commit_hash)
        if self.parent_window:
            self.parent_window.status_label.setText(tr('hash_copied', hash=commit_hash[:7]))
            QTimer.singleShot(2000, lambda: self.parent_window.status_label.setText(tr('ready')))
    
    def show_branch_menu(self):
        branches = self.git_manager.get_all_branches()
        current_branch = self.git_manager.get_current_branch()
        theme = get_current_theme()
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                padding: 8px;
                border-radius: 8px;
            }}
            QMenu::item {{
                padding: 10px 20px;
                color: {theme.colors['text']};
                border-radius: 4px;
                margin: 2px 4px;
            }}
            QMenu::item:selected {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['text_inverse']};
            }}
            QMenu::item:disabled {{
                color: {theme.colors['text_secondary']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {theme.colors['border']};
                margin: 8px 10px;
            }}
        """)
        
        header = QAction(tr('local_branches'), self)
        header.setIcon(self.icon_manager.get_icon('branch-local', color=theme.colors['primary']))
        header.setEnabled(False)
        menu.addAction(header)
        
        local_branches = [b for b in branches if not b['is_remote']]
        remote_branches = [b for b in branches if b['is_remote']]
        
        for branch in local_branches:
            name = branch['name']
            if branch['is_current']:
                action = QAction(f"{name} (actual)", self)
                action.setIcon(self.icon_manager.get_icon('check', color=theme.colors['primary']))
                action.setEnabled(False)
            else:
                action = QAction(name, self)
                action.setIcon(self.icon_manager.get_icon('git-branch', color=theme.colors['text_secondary']))
                action.triggered.connect(lambda checked, b=name: self.switch_branch_quick(b))
            
            menu.addAction(action)
        
        if remote_branches:
            menu.addSeparator()
            remote_header = QAction(tr('remote_branches'), self)
            remote_header.setIcon(self.icon_manager.get_icon('branch-remote', color='#60a5fa'))
            remote_header.setEnabled(False)
            menu.addAction(remote_header)
            
            for branch in remote_branches[:8]:
                name = branch['name']
                display_name = name.replace('remotes/origin/', '')
                action = QAction(display_name, self)
                action.setIcon(self.icon_manager.get_icon('globe', color=theme.colors['text_secondary']))
                action.triggered.connect(lambda checked, b=name: self.switch_branch_quick(b))
                menu.addAction(action)
            
            if len(remote_branches) > 8:
                more_action = QAction(f"... +{len(remote_branches) - 8} más", self)
                more_action.setEnabled(False)
                menu.addAction(more_action)
        
        menu.addSeparator()
        
        new_branch_action = QAction(tr('new_branch_menu'), self)
        new_branch_action.setIcon(self.icon_manager.get_icon('plus', color=theme.colors['primary']))
        new_branch_action.triggered.connect(self.create_new_branch_quick)
        menu.addAction(new_branch_action)
        
        manage_action = QAction(tr('manage_branches'), self)
        manage_action.setIcon(self.icon_manager.get_icon('settings', color=theme.colors['text_secondary']))
        manage_action.triggered.connect(self.open_branch_manager)
        menu.addAction(manage_action)
        
        menu.exec(QCursor.pos())
    
    def switch_branch_quick(self, branch_name):
        clean_name = branch_name.replace('remotes/origin/', '')
        
        reply = QMessageBox.question(
            self,
            tr('change_branch_dialog'),
            tr('change_branch_question', branch=clean_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.git_manager.switch_branch(branch_name)
            if success:
                self.refresh_status()
                self.load_history()
                self.update_repo_info()
            else:
                QMessageBox.warning(self, tr('error'), f"{tr('error_change_branch')}:\n{message}")
    
    def create_new_branch_quick(self):
        branch_name, ok = QInputDialog.getText(
            self,
            tr('new_branch_dialog'),
            tr('new_branch_name'),
            QLineEdit.EchoMode.Normal,
            ""
        )
        
        if ok and branch_name:
            success, message = self.git_manager.create_branch(branch_name)
            if success:
                reply = QMessageBox.question(
                    self,
                    tr('branch_created'),
                    tr('branch_created_question', branch=branch_name),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.git_manager.switch_branch(branch_name)
                
                self.refresh_status()
                self.load_history()
                self.update_repo_info()
            else:
                QMessageBox.warning(self, tr('error'), f"{tr('error_create_branch')}:\n{message}")
    
    def on_commit_double_clicked(self, item):
        commit_hash = item.data(Qt.ItemDataRole.UserRole)
        if not commit_hash:
            return
        
        from ui.branch_manager import CommitActionsDialog
        # Clean up commit text if needed, but rely on hash
        commit_text = item.text()
        commit_msg = commit_text
        
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
        
        indicators = self.plugin_manager.get_repository_indicators(self.repo_path)
        
        current_state = str([(i.get('text'), i.get('color')) for i in indicators])
        if hasattr(self, '_last_indicator_state') and self._last_indicator_state == current_state:
            return
        self._last_indicator_state = current_state
        
        while self.plugin_indicators_layout.count():
            item = self.plugin_indicators_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        indicators = self.plugin_manager.get_repository_indicators(self.repo_path)
        
        default_style = f"""
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
        
        for indicator in indicators:
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(8)
            
            plugin_name = indicator.get('plugin_name', 'unreal_engine')
            plugin = self.plugin_manager.get_plugin(plugin_name)
            
            text = indicator['text']
            if indicator.get('icon'):
                text = f"{indicator['icon']} {text}"
            
            btn = QPushButton(text)
            btn.setToolTip(indicator['tooltip'])
            btn.setMinimumHeight(36)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            if plugin:
                plugin_icon_path = plugin.get_icon()
                if plugin_icon_path and os.path.exists(plugin_icon_path):
                    btn.setIcon(QIcon(plugin_icon_path))
                    btn.setIconSize(QSize(18, 18))
            
            if indicator.get('color'):
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {indicator['color']};
                        color: {theme.colors['text_inverse']};
                        border: 1px solid {theme.colors['primary']};
                        border-radius: 5px;
                        padding: 4px 12px;
                        font-size: 12px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{
                        background-color: {theme.colors['surface_hover']};
                        border-color: {theme.colors['primary_hover']};
                    }}
                """)
            else:
                btn.setStyleSheet(default_style)
                
            btn.clicked.connect(lambda checked, ind=indicator: self.show_plugin_actions(ind))
            container_layout.addWidget(btn)
            
            self.plugin_indicators_layout.addWidget(container)

        if indicators:
            self.plugin_indicators_container.show()
        else:
            self.plugin_indicators_container.hide()
        
        if hasattr(self, 'lfs_track_btn'):
            # Check if any plugin wants to show LFS track button or similar
            # For now, we keep lfs_track_btn generic or managed by plugins?
            # The original code hid it if not unreal project.
            # Let's make it visible if LFS is installed, or maybe we should let plugins manage this too?
            # For now, I'll just leave it visible or check if LFS is relevant.
            pass
    
    def show_plugin_actions(self, indicator=None):
        if not self.plugin_manager or not self.repo_path:
            return
        
        actions = self.plugin_manager.get_plugin_actions('repository', repo_path=self.repo_path)
        
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
        
        # Filter actions by plugin if indicator is provided
        target_plugin = indicator.get('plugin_name') if indicator else None
        
        visible_actions = 0
        for action_data in actions:
            # Filter actions if a specific plugin indicator was clicked
            if target_plugin and action_data.get('plugin_name') != target_plugin:
                continue
            
            visible_actions += 1
            action = QAction(f"{action_data.get('icon_char', '')} {action_data['name']}", self)
            
            action.triggered.connect(lambda checked, ad=action_data: self.execute_plugin_action(ad))
            menu.addAction(action)
        
        if visible_actions > 0:
            cursor_pos = QCursor.pos()
            menu.exec(cursor_pos)
    
    def show_lfs_menu(self):
        menu = QMenu(self)
        theme = get_current_theme()
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {theme.colors['surface']};
                border: 1px solid {theme.colors['border']};
                padding: 5px;
                border-radius: 6px;
            }}
            QMenu::item {{
                padding: 8px 25px;
                color: {theme.colors['text']};
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['text_inverse']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {theme.colors['border']};
                margin: 5px 0;
            }}
        """)
        
        # Status Action (Disabled, just for info)
        status_text = tr('lfs_not_installed')
        if self.git_manager.is_lfs_installed():
            status_text = tr('lfs_installed')
            
        status_action = QAction(status_text, self)
        status_action.setEnabled(False)
        status_action.setIcon(self.icon_manager.get_icon("info", size=16))
        menu.addAction(status_action)
        
        menu.addSeparator()
        
        # Actions
        install_action = QAction(tr('install'), self)
        install_action.setIcon(self.icon_manager.get_icon("download", size=16))
        install_action.triggered.connect(self.install_lfs)
        menu.addAction(install_action)
        
        track_action = QAction(tr('lfs_tracking'), self)
        track_action.setIcon(self.icon_manager.get_icon("file-code", size=16))
        track_action.triggered.connect(self.show_lfs_tracking)
        menu.addAction(track_action)
        
        pull_action = QAction(tr('download_lfs_files'), self)
        pull_action.setIcon(self.icon_manager.get_icon("download", size=16))
        pull_action.triggered.connect(self.do_lfs_pull)
        menu.addAction(pull_action)
        
        locks_action = QAction(tr('lfs_locks'), self)
        locks_action.setIcon(self.icon_manager.get_icon("lock", size=16))
        locks_action.triggered.connect(self.show_lfs_locks)
        menu.addAction(locks_action)
        
        menu.addSeparator()
        
        prune_action = QAction(tr('lfs_prune'), self)
        prune_action.setIcon(self.icon_manager.get_icon("trash", size=16))
        prune_action.triggered.connect(self.do_lfs_prune)
        menu.addAction(prune_action)
        
        menu.exec(QCursor.pos())

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
            QMessageBox.warning(self, tr('error'), message)
        
    def check_lfs_status(self):
        if not self.repo_path or not hasattr(self, 'lfs_btn'):
            return
            
        theme = get_current_theme()
        if self.git_manager.is_lfs_installed():
            self.lfs_btn.setStyleSheet(f"""
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
            """)
            self.lfs_btn.setToolTip(tr('lfs_installed'))
        else:
            self.lfs_btn.setStyleSheet(f"""
                QPushButton {{
                    color: {theme.colors['text_secondary']};
                    background-color: transparent;
                    border: {theme.borders['width_thin']}px solid transparent;
                    border-radius: {theme.borders['radius_md']}px;
                    padding: {theme.spacing['sm']}px {theme.spacing['md']}px;
                    font-size: {theme.fonts['size_md']}px;
                    font-weight: {theme.fonts['weight_bold']};
                }}
                QPushButton:hover {{
                    background-color: {theme.colors['surface_hover']};
                    border-color: {theme.colors['text_secondary']};
                }}
            """)
            self.lfs_btn.setToolTip(tr('lfs_not_installed'))
            
    def install_lfs(self):
        success, message = self.git_manager.install_lfs()
        if success:
            QMessageBox.information(self, tr('success'), tr('success_lfs_installed'))
            self.check_lfs_status()
        else:
            QMessageBox.warning(self, tr('error'), message)
            
    def show_lfs_tracking(self):
        dialog = LFSTrackingDialog(self.git_manager, self.plugin_manager, self, suggested_files=self.large_files)
        dialog.exec()
        self.check_lfs_status()
            
    def do_lfs_pull(self):
        success, message = self.git_manager.lfs_pull()
        if success:
            QMessageBox.information(self, tr('success'), tr('success_lfs_pull'))
        else:
            QMessageBox.warning(self, tr('error'), message)

    def show_lfs_locks(self):
        dialog = LFSLocksDialog(self.git_manager, self)
        dialog.exec()

    def do_lfs_prune(self):
        success, message = self.git_manager.lfs_prune()
        if success:
            QMessageBox.information(self, tr('success'), tr('lfs_prune_success'))
        else:
            QMessageBox.warning(self, tr('error'), tr('lfs_prune_error', message=message))
            
    def clone_repository(self, url, path):
        self.show_loading(tr('cloning_repository'), f"{url}\n-> {path}")
        
        self.clone_thread = CloneThread(self.git_manager, url, path)
        self.clone_thread.finished.connect(self.on_clone_finished)
        self.clone_thread.progress.connect(self.on_clone_progress)
        self.clone_thread.start()

    def on_clone_progress(self, line):
        self.loading_details.setText(line)
        
    def on_clone_finished(self, success, message):
        if success:
            repo_path = message
            self.load_repository(repo_path)
            
            if self.parent_window:
                tab_widget = self.parent_window.tab_widget
                index = tab_widget.indexOf(self)
                repo_name = os.path.basename(repo_path)
                tab_widget.setTabText(index, repo_name)
        else:
            self.show_home_view()
            QMessageBox.critical(self, tr('error'), f"{tr('clone_failed')}:\n{message}")
            
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
    
    def update_translations(self):
        if hasattr(self, 'branch_title'):
            self.branch_title.setText(tr('current_branch_label'))
        
        if hasattr(self, 'changes_header'):
            self.changes_header.title_label.setText(tr('changes_title'))
            self.changes_header.desc_label.setText(tr('changes_subtitle'))
        if hasattr(self, 'commit_header'):
            self.commit_header.title_label.setText(tr('commit_title'))
            self.commit_header.desc_label.setText(tr('commit_subtitle'))
        if hasattr(self, 'history_header'):
            self.history_header.title_label.setText(tr('history_title'))
            self.history_header.desc_label.setText(tr('history_subtitle'))
        if hasattr(self, 'info_header'):
            self.info_header.title_label.setText(tr('info_title'))
            self.info_header.desc_label.setText(tr('info_subtitle'))
        if hasattr(self, 'diff_header'):
            self.diff_header.title_label.setText(tr('diff_title'))
            self.diff_header.desc_label.setText(tr('diff_subtitle'))
        
        if hasattr(self, 'open_folder_btn'):
            self.open_folder_btn.setText(f" {tr('folder_button')}")
            self.open_folder_btn.setToolTip(tr('folder_tooltip'))
        if hasattr(self, 'open_terminal_btn'):
            self.open_terminal_btn.setText(f" {tr('terminal_button')}")
            self.open_terminal_btn.setToolTip(tr('terminal_tooltip'))
        if hasattr(self, 'open_unreal_btn'):
            self.open_unreal_btn.setText(f" {tr('unreal_button')}")
            self.open_unreal_btn.setToolTip(tr('unreal_tooltip'))
        if hasattr(self, 'pull_btn'):
            self.pull_btn.setText(f" {tr('pull')}")
            self.pull_btn.setToolTip(tr('pull_tooltip'))
        if hasattr(self, 'push_btn'):
            self.push_btn.setText(f" {tr('push')}")
            self.push_btn.setToolTip(tr('push_tooltip'))
        if hasattr(self, 'fetch_btn'):
            self.fetch_btn.setText(f" {tr('fetch')}")
            self.fetch_btn.setToolTip(tr('fetch_tooltip'))
        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.setText(f" {tr('refresh')}")
            self.refresh_btn.setToolTip(tr('refresh_tooltip'))
        if hasattr(self, 'stage_all_btn'):
            self.stage_all_btn.setText(f" {tr('add_all')}")
            self.stage_all_btn.setToolTip(tr('add_all_tooltip'))
        if hasattr(self, 'stage_btn'):
            self.stage_btn.setText(f" {tr('add')}")
            self.stage_btn.setToolTip(tr('add_tooltip'))
        if hasattr(self, 'unstage_btn'):
            self.unstage_btn.setText(f" {tr('remove')}")
            self.unstage_btn.setToolTip(tr('remove_tooltip'))
        if hasattr(self, 'commit_message'):
            self.commit_message.setPlaceholderText(tr('commit_placeholder'))
        if hasattr(self, 'commit_summary'):
            self.commit_summary.setPlaceholderText(tr('commit_summary_placeholder'))
        if hasattr(self, 'commit_btn'):
            self.commit_btn.setText(f" {tr('commit_and_save')}")
            self.commit_btn.setToolTip(tr('commit_and_save_tooltip'))
        if hasattr(self, 'lfs_btn'):
            self.lfs_btn.setText(" LFS")
            self.lfs_btn.setToolTip(tr('lfs_title'))
        if hasattr(self, 'diff_placeholder'):
            self.diff_placeholder.setText(tr('select_file_diff'))
        
        if self.repo_path:
            self.refresh_status()
            self.check_lfs_status()
            self.update_repo_info()
    
    def select_all_changes(self):
        for i in range(self.changes_list.count()):
            item = self.changes_list.item(i)
            item.setCheckState(Qt.CheckState.Checked)
            
    def deselect_all_changes(self):
        for i in range(self.changes_list.count()):
            item = self.changes_list.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)

    def discard_selected(self):
        items_to_process = self.get_checked_items()
        if not items_to_process:
            current_item = self.changes_list.currentItem()
            if current_item:
                items_to_process.append(current_item)
        
        if not items_to_process:
            return

        reply = QMessageBox.question(
            self,
            tr('confirm_discard'),
            tr('confirm_discard_text', file=f"{len(items_to_process)} files"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            errors = []
            for item in items_to_process:
                file_path = item.data(Qt.ItemDataRole.UserRole)
                success, message = self.git_manager.discard_file(file_path)
                if not success:
                    errors.append(f"{file_path}: {message}")
            
            self.refresh_status()
            
            if errors:
                QMessageBox.warning(self, tr('error'), "\n".join(errors))

    def discard_file_context(self, file_path):
        reply = QMessageBox.question(
            self,
            tr('confirm_discard'),
            tr('confirm_discard_text', file=file_path),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.git_manager.discard_file(file_path)
            if success:
                self.refresh_status()
            else:
                QMessageBox.warning(self, tr('error'), message)

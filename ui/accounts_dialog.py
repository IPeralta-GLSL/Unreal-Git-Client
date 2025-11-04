from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QListWidget, QListWidgetItem, QMessageBox,
                             QInputDialog, QLineEdit, QTabWidget, QWidget,
                             QTextEdit, QGroupBox, QFrame, QApplication, QComboBox, QFormLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QPixmap, QPainter, QPainterPath
from PyQt6.QtSvg import QSvgRenderer
from core.translations import tr, get_translation_manager, set_language
from ui.icon_manager import IconManager
import webbrowser
import requests
import secrets
import os
import platform

class AccountsDialog(QDialog):
    accounts_changed = pyqtSignal()
    language_changed = pyqtSignal(str)
    
    def __init__(self, account_manager, plugin_manager=None, parent=None):
        super().__init__(parent)
        self.account_manager = account_manager
        self.plugin_manager = plugin_manager
        self.icon_manager = IconManager()
        self.drag_position = QPoint()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        
        from core.settings_manager import SettingsManager
        self.settings_manager = SettingsManager()
        
        self.setWindowTitle(tr('settings'))
        self.setWindowIcon(self.icon_manager.get_icon("gear-six"))
        self.setModal(True)
        self.setMinimumSize(800, 600)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        title_bar = self.create_title_bar()
        layout.addWidget(title_bar)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        self.title_label = QLabel(tr("settings"))
        self.title_label.setProperty("class", "title")
        content_layout.addWidget(self.title_label)
        
        self.tabs = QTabWidget()
        
        general_tab = self.create_general_section()
        self.tabs.addTab(general_tab, self.icon_manager.get_icon("gear-six"), tr("general"))
        
        accounts_tab = self.create_accounts_section()
        self.tabs.addTab(accounts_tab, self.icon_manager.get_icon("user"), tr("accounts"))
        
        if self.plugin_manager:
            plugins_tab = self.create_plugins_section()
            self.tabs.addTab(plugins_tab, self.icon_manager.get_icon("plugs-connected"), tr("plugins"))
        
        appearance_tab = self.create_appearance_section()
        self.tabs.addTab(appearance_tab, self.icon_manager.get_icon("globe"), tr("appearance"))
        
        content_layout.addWidget(self.tabs)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_button = QPushButton(tr("close"))
        self.close_button.setMinimumWidth(100)
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        content_layout.addLayout(button_layout)
        layout.addWidget(content_widget)
    
    def create_title_bar(self):
        from ui.theme import get_current_theme
        theme = get_current_theme()
        
        title_bar = QFrame()
        title_bar.setFixedHeight(35)
        title_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['surface']};
                border-bottom: 1px solid {theme.colors['border']};
            }}
        """)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(0)
        
        app_icon = QLabel()
        app_icon.setPixmap(self.icon_manager.get_pixmap("gear-six", size=18))
        layout.addWidget(app_icon)
        
        title_label = QLabel(f"  {tr('settings')}")
        title_label.setStyleSheet(f"color: {theme.colors['text']}; font-weight: bold; font-size: 13px;")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        close_button = QPushButton()
        close_button.setIcon(self.icon_manager.get_icon("x-square", size=14))
        close_button.setFixedSize(40, 35)
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(self.accept)
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
        
        title_bar.mousePressEvent = self.title_bar_mouse_press
        
        return title_bar
    
    def title_bar_mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
        super().mouseMoveEvent(event)
        

    def create_general_section(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        header = QLabel(tr("general_config"))
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: palette(link); padding: 10px;")
        layout.addWidget(header)
        
        language_group = QGroupBox(tr("language"))
        language_layout = QFormLayout()
        
        self.language_combo = QComboBox()
        self.language_combo.addItem("Español", "es")
        self.language_combo.addItem("English", "en")
        
        current_lang = self.settings_manager.get_language()
        index = self.language_combo.findData(current_lang)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
            
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        
        language_layout.addRow(tr("language") + ":", self.language_combo)
        
        lang_note = QLabel(tr("language_change_note"))
        lang_note.setWordWrap(True)
        lang_note.setStyleSheet("color: palette(mid); font-size: 11px; padding: 5px; margin-top: 10px;")
        language_layout.addRow("", lang_note)
        
        language_group.setLayout(language_layout)
        layout.addWidget(language_group)
        
        layout.addStretch()
        
        return widget
    
    def on_language_changed(self, index):
        language_code = self.language_combo.itemData(index)
        self.settings_manager.set_language(language_code)
        set_language(language_code)
        self.language_changed.emit(language_code)
        
        self.retranslate_ui()
    
    def create_accounts_section(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        section_tabs = QTabWidget()
        section_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: palette(window);
            }
            QTabBar::tab {
                background-color: palette(base);
                color: palette(text);
                padding: 8px 16px;
                margin-right: 1px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background-color: palette(button);
                color: palette(bright-text);
            }
            QTabBar::tab:hover {
                background-color: palette(button);
            }
        """)
        
        section_tabs.addTab(self.create_accounts_tab(), "📋 Mis Cuentas")
        section_tabs.addTab(self.create_github_tab(), self.icon_manager.get_icon("github-logo"), "GitHub")
        section_tabs.addTab(self.create_gitlab_tab(), self.icon_manager.get_icon("gitlab-logo"), "GitLab")
        section_tabs.addTab(self.create_git_tab(), self.icon_manager.get_icon("git-commit"), "Git Local")
        
        layout.addWidget(section_tabs)
        
        return widget
    
    def create_accounts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info = QLabel("Tus cuentas conectadas:")
        info.setStyleSheet("font-size: 13px; margin: 10px;")
        layout.addWidget(info)
        
        self.accounts_list = QListWidget()
        self.accounts_list.setStyleSheet("""
            QListWidget {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: palette(button);
            }
            QListWidget::item:selected {
                background-color: palette(highlight);
            }
        """)
        layout.addWidget(self.accounts_list)
        
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.setIcon(self.icon_manager.get_icon("arrows-clockwise"))
        refresh_btn.clicked.connect(self.load_accounts)
        btn_layout.addWidget(refresh_btn)
        
        remove_btn = QPushButton("Eliminar")
        remove_btn.setIcon(self.icon_manager.get_icon("trash"))
        remove_btn.clicked.connect(self.remove_selected_account)
        btn_layout.addWidget(remove_btn)
        
        btn_layout.addStretch()
        
        for btn in [refresh_btn, remove_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: palette(button);
                    padding: 8px 16px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: palette(button);
                }
            """)
        
        layout.addLayout(btn_layout)
        
        self.load_accounts()
        
        return widget
    
    def create_github_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        github_icon = QLabel()
        github_icon_path = "ui/Icons/github-logo.svg"
        if os.path.exists(github_icon_path):
            from PyQt6.QtGui import QPixmap
            from PyQt6.QtSvg import QSvgRenderer
            from PyQt6.QtCore import QByteArray
            pixmap = QPixmap(40, 40)
            pixmap.fill(Qt.GlobalColor.transparent)
            renderer = QSvgRenderer(github_icon_path)
            from PyQt6.QtGui import QPainter
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            github_icon.setPixmap(pixmap)
            github_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(github_icon)
        
        info_box = QGroupBox("Conectar con GitHub")
        info_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        info_layout = QVBoxLayout(info_box)
        
        info_text = QLabel(
            "Conecta tu cuenta de GitHub de forma simple y segura.\n\n"
            "Haz click en 'Login con GitHub' y sigue las instrucciones en el navegador."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("font-size: 13px; font-weight: normal; padding: 10px;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_box)
        
        connect_btn_layout = QHBoxLayout()
        
        github_logo_label = QLabel()
        github_logo_path = "ui/Icons/github-logo.svg"
        if os.path.exists(github_logo_path):
            pixmap = QPixmap(24, 24)
            pixmap.fill(Qt.GlobalColor.transparent)
            renderer = QSvgRenderer(github_logo_path)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            github_logo_label.setPixmap(pixmap)
        
        connect_btn = QPushButton(" Login con GitHub")
        connect_btn.setProperty("class", "github")
        connect_btn.setMinimumHeight(55)
        connect_btn.clicked.connect(self.start_github_device_flow)
        connect_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                border-radius: 8px;
                padding-left: 40px;
            }
        """)
        
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addWidget(connect_btn)
        
        github_logo_label.setParent(connect_btn)
        github_logo_label.move(15, 15)
        
        layout.addWidget(btn_container)
        
        self.github_status_label = QLabel("")
        self.github_status_label.setWordWrap(True)
        self.github_status_label.setStyleSheet("""
            QLabel {
                padding: 15px;
                background-color: palette(button);
                border: 1px solid palette(mid);
                border-radius: 6px;
                font-size: 13px;
                margin-top: 10px;
            }
        """)
        self.github_status_label.hide()
        layout.addWidget(self.github_status_label)
        
        separator = QLabel("━" * 80)
        separator.setStyleSheet(" margin-top: 20px; margin-bottom: 10px;")
        layout.addWidget(separator)
        
        advanced_label = QLabel("🔧 Métodos alternativos:")
        advanced_label.setStyleSheet("margin-top: 10px; font-weight: bold; color: palette(text); font-size: 12px;")
        layout.addWidget(advanced_label)
        
        manual_label = QLabel("Agregar un Personal Access Token manualmente:")
        manual_label.setStyleSheet("margin-top: 10px; font-size: 11px; color: palette(text);")
        layout.addWidget(manual_label)
        
        token_layout = QHBoxLayout()
        self.github_token = QLineEdit()
        self.github_token.setPlaceholderText("ghp_...")
        self.github_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.github_token.setStyleSheet("""
            QLineEdit {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 5px;
                padding: 8px;
                color: palette(window-text);
            }
        """)
        token_layout.addWidget(self.github_token)
        
        add_token_btn = QPushButton("➕ Agregar Token")
        add_token_btn.clicked.connect(self.add_github_token)
        add_token_btn.setMinimumHeight(35)
        add_token_btn.setStyleSheet("""
            QPushButton {
                background-color: palette(highlight);
                color: palette(bright-text);
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: palette(highlight);
            }
        """)
        token_layout.addWidget(add_token_btn)
        
        layout.addLayout(token_layout)
        
        layout.addStretch()
        
        return widget
    
    def create_gitlab_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        gitlab_icon = QLabel()
        gitlab_icon_path = "ui/Icons/gitlab-logo.svg"
        if os.path.exists(gitlab_icon_path):
            pixmap = QPixmap(40, 40)
            pixmap.fill(Qt.GlobalColor.transparent)
            renderer = QSvgRenderer(gitlab_icon_path)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            gitlab_icon.setPixmap(pixmap)
            gitlab_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(gitlab_icon)
        
        info_box = QGroupBox("Conectar con GitLab")
        info_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        info_layout = QVBoxLayout(info_box)
        
        info_text = QLabel(
            "Conecta tu cuenta de GitLab de forma simple y segura.\n\n"
            "Haz click en 'Login con GitLab' y sigue las instrucciones en el navegador."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("font-size: 13px; font-weight: normal; padding: 10px;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_box)
        
        url_layout = QHBoxLayout()
        url_label = QLabel("URL de GitLab:")
        url_label.setStyleSheet("font-size: 12px;")
        self.gitlab_url_input = QLineEdit()
        self.gitlab_url_input.setText("https://gitlab.com")
        self.gitlab_url_input.setPlaceholderText("https://gitlab.com")
        self.gitlab_url_input.setStyleSheet("""
            QLineEdit {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 5px;
                padding: 8px;
                color: palette(window-text);
            }
        """)
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.gitlab_url_input)
        layout.addLayout(url_layout)
        
        gitlab_logo_label = QLabel()
        gitlab_logo_path = "ui/Icons/gitlab-logo.svg"
        if os.path.exists(gitlab_logo_path):
            pixmap = QPixmap(24, 24)
            pixmap.fill(Qt.GlobalColor.transparent)
            renderer = QSvgRenderer(gitlab_logo_path)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            gitlab_logo_label.setPixmap(pixmap)
        
        connect_btn = QPushButton(" Login con GitLab")
        connect_btn.setProperty("class", "gitlab")
        connect_btn.setMinimumHeight(55)
        connect_btn.clicked.connect(self.start_gitlab_device_flow)
        connect_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                border-radius: 8px;
                padding-left: 40px;
            }
        """)
        
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addWidget(connect_btn)
        
        gitlab_logo_label.setParent(connect_btn)
        gitlab_logo_label.move(15, 15)
        
        layout.addWidget(btn_container)
        
        self.gitlab_status_label = QLabel("")
        self.gitlab_status_label.setWordWrap(True)
        self.gitlab_status_label.setStyleSheet("""
            QLabel {
                padding: 15px;
                background-color: palette(button);
                border: 1px solid palette(mid);
                border-radius: 6px;
                font-size: 13px;
                margin-top: 10px;
            }
        """)
        self.gitlab_status_label.hide()
        layout.addWidget(self.gitlab_status_label)
        
        separator = QLabel("━" * 80)
        separator.setStyleSheet(" margin-top: 20px; margin-bottom: 10px;")
        layout.addWidget(separator)
        
        advanced_label = QLabel("🔧 Métodos alternativos:")
        advanced_label.setStyleSheet("margin-top: 10px; font-weight: bold; color: palette(text); font-size: 12px;")
        layout.addWidget(advanced_label)
        
        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)
        
        url_label = QLabel("URL de GitLab:")
        self.gitlab_url = QLineEdit()
        self.gitlab_url.setText("https://gitlab.com")
        self.gitlab_url.setStyleSheet("""
            QLineEdit {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 5px;
                padding: 8px;
                color: palette(window-text);
            }
        """)
        form_layout.addWidget(url_label)
        form_layout.addWidget(self.gitlab_url)
        
        app_id_label = QLabel("Application ID:")
        self.gitlab_app_id = QLineEdit()
        self.gitlab_app_id.setPlaceholderText("Ingresa tu GitLab Application ID")
        self.gitlab_app_id.setStyleSheet(self.gitlab_url.styleSheet())
        form_layout.addWidget(app_id_label)
        form_layout.addWidget(self.gitlab_app_id)
        
        app_secret_label = QLabel("Application Secret:")
        self.gitlab_app_secret = QLineEdit()
        self.gitlab_app_secret.setPlaceholderText("Ingresa tu GitLab Application Secret")
        self.gitlab_app_secret.setEchoMode(QLineEdit.EchoMode.Password)
        self.gitlab_app_secret.setStyleSheet(self.gitlab_url.styleSheet())
        form_layout.addWidget(app_secret_label)
        form_layout.addWidget(self.gitlab_app_secret)
        
        layout.addLayout(form_layout)
        
        connect_btn = QPushButton("Conectar con GitLab")
        connect_btn.setIcon(self.icon_manager.get_icon("link"))
        connect_btn.setMinimumHeight(40)
        connect_btn.clicked.connect(self.connect_gitlab)
        connect_btn.setStyleSheet("""
            QPushButton {
                background-color: palette(highlight);
                color: palette(bright-text);
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: palette(highlight);
            }
        """)
        layout.addWidget(connect_btn)
        
        manual_label = QLabel("O agrega manualmente un Personal Access Token:")
        manual_label.setStyleSheet("margin-top: 20px; font-size: 12px;")
        layout.addWidget(manual_label)
        
        token_layout = QHBoxLayout()
        self.gitlab_token = QLineEdit()
        self.gitlab_token.setPlaceholderText("glpat-...")
        self.gitlab_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.gitlab_token.setStyleSheet(self.gitlab_url.styleSheet())
        token_layout.addWidget(self.gitlab_token)
        
        add_token_btn = QPushButton("➕ Agregar Token")
        add_token_btn.clicked.connect(self.add_gitlab_token)
        add_token_btn.setStyleSheet(connect_btn.styleSheet())
        token_layout.addWidget(add_token_btn)
        
        layout.addLayout(token_layout)
        
        layout.addStretch()
        
        return widget
    
    def create_git_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info = QLabel("Configura tu identidad global de Git:")
        info.setStyleSheet("font-size: 13px; font-weight: bold; margin: 10px;")
        layout.addWidget(info)
        
        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)
        
        name_label = QLabel("Nombre:")
        self.git_name = QLineEdit()
        self.git_name.setPlaceholderText("Tu nombre completo")
        self.git_name.setStyleSheet("""
            QLineEdit {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 5px;
                padding: 8px;
                color: palette(window-text);
            }
        """)
        form_layout.addWidget(name_label)
        form_layout.addWidget(self.git_name)
        
        email_label = QLabel("Email:")
        self.git_email = QLineEdit()
        self.git_email.setPlaceholderText("tu@email.com")
        self.git_email.setStyleSheet(self.git_name.styleSheet())
        form_layout.addWidget(email_label)
        form_layout.addWidget(self.git_email)
        
        layout.addLayout(form_layout)
        
        save_btn = QPushButton("Guardar Configuración Global")
        save_btn.setIcon(self.icon_manager.get_icon("check"))
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self.save_git_config)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: palette(highlight);
                color: palette(bright-text);
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: palette(highlight);
            }
        """)
        layout.addWidget(save_btn)
        
        current_group = QGroupBox("Configuración Actual")
        current_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                margin-top: 20px;
                padding-top: 10px;
            }
        """)
        current_layout = QVBoxLayout(current_group)
        
        self.current_config = QTextEdit()
        self.current_config.setReadOnly(True)
        self.current_config.setMaximumHeight(150)
        self.current_config.setStyleSheet("""
            QTextEdit {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 5px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
        """)
        current_layout.addWidget(self.current_config)
        
        layout.addWidget(current_group)
        
        self.load_git_config()
        
        layout.addStretch()
        
        return widget
    
    def load_accounts(self):
        self.accounts_list.clear()
        accounts = self.account_manager.get_accounts()
        
        if not accounts:
            item = QListWidgetItem("No hay cuentas conectadas")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.accounts_list.addItem(item)
            return
        
        for account in accounts:
            platform = account['platform'].lower()
            username = account['username']
            email = account.get('email', '')
            
            widget = QWidget()
            widget.setMinimumHeight(60)
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(10, 8, 10, 8)
            layout.setSpacing(12)
            
            avatar_label = QLabel()
            avatar_label.setFixedSize(44, 44)
            avatar_label.setStyleSheet("border-radius: 22px; background-color: palette(button);")
            
            if email:
                import hashlib
                email_hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
                avatar_url = f"https://www.gravatar.com/avatar/{email_hash}?s=44&d=identicon"
                
                try:
                    import urllib.request
                    data = urllib.request.urlopen(avatar_url, timeout=2).read()
                    pixmap = QPixmap()
                    pixmap.loadFromData(data)
                    
                    rounded_pixmap = QPixmap(44, 44)
                    rounded_pixmap.fill(Qt.GlobalColor.transparent)
                    painter = QPainter(rounded_pixmap)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    path = QPainterPath()
                    path.addEllipse(0, 0, 44, 44)
                    painter.setClipPath(path)
                    painter.drawPixmap(0, 0, 44, 44, pixmap)
                    painter.end()
                    
                    avatar_label.setPixmap(rounded_pixmap)
                except:
                    avatar_label.setPixmap(self.icon_manager.get_pixmap("user", size=24))
                    avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    avatar_label.setStyleSheet("border-radius: 22px; background-color: palette(button);")
            else:
                avatar_label.setPixmap(self.icon_manager.get_pixmap("user", size=24))
                avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                avatar_label.setStyleSheet("border-radius: 20px; background-color: palette(button);")
            
            avatar_container = QWidget()
            avatar_container.setFixedWidth(44)
            avatar_layout = QVBoxLayout(avatar_container)
            avatar_layout.setContentsMargins(0, 0, 0, 0)
            avatar_layout.addStretch()
            avatar_layout.addWidget(avatar_label)
            avatar_layout.addStretch()
            
            layout.addWidget(avatar_container)
            
            info_layout = QVBoxLayout()
            info_layout.setSpacing(4)
            
            status = 'Activo' if account.get('active', True) else 'Inactivo'
            
            name_label = QLabel(f"<b>{platform.upper()}</b>: {username} ({status})")
            name_label.setStyleSheet("font-size: 14px;")
            info_layout.addWidget(name_label)
            
            if email:
                email_label = QLabel(f"📧 {email}")
                email_label.setStyleSheet("font-size: 12px; color: palette(text);")
                info_layout.addWidget(email_label)
            else:
                info_layout.addStretch()
            
            layout.addLayout(info_layout, 1)
            layout.addStretch()
            
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, account)
            item.setSizeHint(widget.sizeHint())
            self.accounts_list.addItem(item)
            self.accounts_list.setItemWidget(item, widget)
    
    def remove_selected_account(self):
        item = self.accounts_list.currentItem()
        if not item:
            return
        
        account = item.data(Qt.ItemDataRole.UserRole)
        if not account:
            return
        
        reply = QMessageBox.question(
            self,
            "Eliminar Cuenta",
            f"¿Eliminar la cuenta {account['username']} de {account['platform']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.account_manager.remove_account(account['platform'], account['username'])
            self.load_accounts()
            self.accounts_changed.emit()
    
    def start_github_device_flow(self):
        self.github_status_label.setText("⏳ Iniciando autenticación...")
        self.github_status_label.show()
        
        flow_data = self.account_manager.start_github_device_flow()
        
        if not flow_data:
            self.github_status_label.setText("❌ Error al iniciar la autenticación. Verifica tu conexión a internet.")
            return
        
        user_code = flow_data['user_code']
        verification_uri = flow_data['verification_uri']
        device_code = flow_data['device_code']
        interval = flow_data['interval']
        
        copy_button = QPushButton("📋")
        copy_button.setFixedSize(30, 30)
        copy_button.setStyleSheet("""
            QPushButton {
                background-color: palette(highlight);
                color: palette(bright-text);
                font-size: 14px;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: palette(highlight);
            }
        """)
        copy_button.clicked.connect(lambda: self.copy_code_to_clipboard(user_code))
        
        code_layout = QHBoxLayout()
        code_label = QLabel(f"<b>📋 Código:</b> <span style='font-size: 20px; font-family: monospace;'>{user_code}</span>")
        code_layout.addWidget(code_label)
        code_layout.addWidget(copy_button)
        code_layout.addStretch()
        
        self.github_status_label.setText(
            f"<br>Abriendo navegador en <b>{verification_uri}</b>...<br><br>"
            f"Ingresa el código cuando se te solicite.<br>"
        )
        
        status_layout = self.github_status_label.parent().layout() if self.github_status_label.parent() else None
        if status_layout:
            for i in range(status_layout.count()):
                item = status_layout.itemAt(i)
                if item and item.widget() == self.github_status_label:
                    status_layout.insertLayout(i, code_layout)
                    break
        
        webbrowser.open(verification_uri)
        
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(lambda: self.poll_github_token(device_code, interval))
        self.poll_timer.start(interval * 1000)
        
        self.poll_attempts = 0
        self.max_poll_attempts = 60
    
    def poll_github_token(self, device_code, interval):
        self.poll_attempts += 1
        
        if self.poll_attempts > self.max_poll_attempts:
            self.poll_timer.stop()
            self.github_status_label.setText("❌ Tiempo de espera agotado. Intenta nuevamente.")
            return
        
        result = self.account_manager.poll_github_device_token(device_code, interval)
        
        if result == 'pending':
            return
        elif result == 'slow_down':
            self.poll_timer.setInterval((interval + 5) * 1000)
            return
        elif result and result != 'pending' and result != 'slow_down':
            self.poll_timer.stop()
            
            user_info = self.account_manager.get_github_user_info(result)
            
            if user_info:
                username = user_info['username']
                email = user_info['email']
                
                self.account_manager.add_account('GitHub', username, result, email)
                
                self.github_status_label.setText(
                    f"<b>Conectado exitosamente como:</b> {username}<br>"
                    f"Email: {email or 'No disponible'}"
                )
                
                self.load_accounts()
                self.accounts_changed.emit()
            else:
                self.github_status_label.setText("❌ Error al obtener información del usuario.")
        else:
            self.poll_timer.stop()
            self.github_status_label.setText("❌ Error en la autenticación. Intenta nuevamente.")
    
    def start_gitlab_device_flow(self):
        gitlab_url = self.gitlab_url_input.text().strip()
        if not gitlab_url:
            gitlab_url = "https://gitlab.com"
        
        self.gitlab_status_label.setText("⏳ Iniciando autenticación con GitLab...")
        self.gitlab_status_label.show()
        
        flow_data = self.account_manager.start_gitlab_device_flow(gitlab_url)
        
        if not flow_data:
            self.gitlab_status_label.setText(
                "GitLab aún no soporta Device Flow públicamente.\n\n"
                "Por favor, usa un Personal Access Token en el método alternativo abajo."
            )
            return
        
        user_code = flow_data['user_code']
        verification_uri = flow_data.get('verification_uri_complete') or flow_data['verification_uri']
        device_code = flow_data['device_code']
        interval = flow_data['interval']
        
        self.gitlab_status_label.setText(
            f"<b>📋 Código de verificación:</b> <span style='font-size: 24px;'>{user_code}</span><br><br>"
            f"Abriendo navegador en <b>{verification_uri}</b>...<br><br>"
            f"Ingresa el código cuando se te solicite."
        )
        
        webbrowser.open(verification_uri)
        
        self.gitlab_poll_timer = QTimer()
        self.gitlab_poll_timer.timeout.connect(lambda: self.poll_gitlab_token(gitlab_url, device_code, interval))
        self.gitlab_poll_timer.start(interval * 1000)
        
        self.gitlab_poll_attempts = 0
        self.gitlab_max_poll_attempts = 60
    
    def poll_gitlab_token(self, gitlab_url, device_code, interval):
        self.gitlab_poll_attempts += 1
        
        if self.gitlab_poll_attempts > self.gitlab_max_poll_attempts:
            self.gitlab_poll_timer.stop()
            self.gitlab_status_label.setText("❌ Tiempo de espera agotado. Intenta nuevamente.")
            return
        
        result = self.account_manager.poll_gitlab_device_token(gitlab_url, device_code, interval)
        
        if result == 'pending':
            return
        elif result == 'slow_down':
            self.gitlab_poll_timer.setInterval((interval + 5) * 1000)
            return
        elif result and result != 'pending' and result != 'slow_down':
            self.gitlab_poll_timer.stop()
            
            user_info = self.account_manager.get_gitlab_user_info(gitlab_url, result)
            
            if user_info:
                username = user_info['username']
                email = user_info['email']
                
                self.account_manager.add_account('GitLab', username, result, email)
                
                self.gitlab_status_label.setText(
                    f"<b>Conectado exitosamente como:</b> {username}<br>"
                    f"Email: {email or 'No disponible'}"
                )
                
                self.load_accounts()
                self.accounts_changed.emit()
            else:
                self.gitlab_status_label.setText("❌ Error al obtener información del usuario.")
        else:
            self.gitlab_poll_timer.stop()
            self.gitlab_status_label.setText("❌ Error en la autenticación. Intenta nuevamente.")
    
    def connect_github(self):
        client_id = self.github_client_id.text().strip()
        client_secret = self.github_client_secret.text().strip()
        
        if not client_id or not client_secret:
            QMessageBox.warning(self, "Error", "Por favor ingresa el Client ID y Client Secret")
            return
        
        state = secrets.token_urlsafe(32)
        self.account_manager.oauth_state = state
        
        auth_url = self.account_manager.github_oauth_url(client_id, state)
        
        self.account_manager.start_oauth_server()
        
        webbrowser.open(auth_url)
        
        QMessageBox.information(
            self,
            "Esperando autorización",
            "Se ha abierto tu navegador.\n\nAutoriza la aplicación y luego regresa aquí."
        )
        
        self.wait_for_oauth('github', client_id, client_secret)
    
    def connect_gitlab(self):
        app_id = self.gitlab_app_id.text().strip()
        app_secret = self.gitlab_app_secret.text().strip()
        gitlab_url = self.gitlab_url.text().strip()
        
        if not app_id or not app_secret:
            QMessageBox.warning(self, "Error", "Ingresa Application ID y Secret")
            return
        
        success, result = self.account_manager.start_oauth_server(8888)
        if not success:
            QMessageBox.warning(self, "Error", f"No se pudo iniciar servidor OAuth:\n{result}")
            return
        
        redirect_uri = "http://localhost:8888/callback"
        auth_url = self.account_manager.gitlab_oauth_url(app_id, redirect_uri, gitlab_url)
        
        webbrowser.open(auth_url)
        
        QMessageBox.information(
            self,
            "Autenticación en progreso",
            "Se abrió tu navegador para autenticar.\n\n"
            "Autoriza la aplicación y espera a que se complete."
        )
        
        self.wait_for_oauth('gitlab', app_id, app_secret, gitlab_url)
    
    def wait_for_oauth(self, platform, client_id, client_secret, gitlab_url=None):
        self.oauth_timer = QTimer()
        self.oauth_attempts = 0
        self.max_attempts = 60
        
        def check_oauth():
            self.oauth_attempts += 1
            code = self.account_manager.get_oauth_code()
            
            if code:
                self.oauth_timer.stop()
                self.account_manager.stop_oauth_server()
                self.exchange_code_for_token(platform, code, client_id, client_secret, gitlab_url)
            elif self.oauth_attempts >= self.max_attempts:
                self.oauth_timer.stop()
                self.account_manager.stop_oauth_server()
                QMessageBox.warning(self, "Timeout", "Tiempo de espera agotado")
        
        self.oauth_timer.timeout.connect(check_oauth)
        self.oauth_timer.start(1000)
    
    def exchange_code_for_token(self, platform, code, client_id, client_secret, gitlab_url=None):
        try:
            if platform == 'github':
                response = requests.post(
                    'https://github.com/login/oauth/access_token',
                    headers={'Accept': 'application/json'},
                    data={
                        'client_id': client_id,
                        'client_secret': client_secret,
                        'code': code
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get('access_token')
                    
                    if token:
                        user_response = requests.get(
                            'https://api.github.com/user',
                            headers={'Authorization': f'token {token}'}
                        )
                        
                        if user_response.status_code == 200:
                            user_data = user_response.json()
                            username = user_data.get('login')
                            email = user_data.get('email')
                            
                            self.account_manager.add_account('github', username, token, email)
                            self.account_manager.configure_git_credentials('github', username, token, email)
                            
                            QMessageBox.information(
                                self,
                                "Éxito",
                                f"Cuenta de GitHub conectada:\n{username}"
                            )
                            
                            self.load_accounts()
                            self.accounts_changed.emit()
                        else:
                            QMessageBox.warning(self, "Error", "No se pudo obtener información del usuario")
                    else:
                        QMessageBox.warning(self, "Error", "No se recibió token de acceso")
                else:
                    QMessageBox.warning(self, "Error", f"Error al intercambiar código: {response.status_code}")
                    
            elif platform == 'gitlab':
                redirect_uri = "http://localhost:8888/callback"
                response = requests.post(
                    f"{gitlab_url}/oauth/token",
                    data={
                        'client_id': client_id,
                        'client_secret': client_secret,
                        'code': code,
                        'grant_type': 'authorization_code',
                        'redirect_uri': redirect_uri
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get('access_token')
                    
                    if token:
                        user_response = requests.get(
                            f"{gitlab_url}/api/v4/user",
                            headers={'Authorization': f'Bearer {token}'}
                        )
                        
                        if user_response.status_code == 200:
                            user_data = user_response.json()
                            username = user_data.get('username')
                            email = user_data.get('email')
                            
                            self.account_manager.add_account('gitlab', username, token, email)
                            self.account_manager.configure_git_credentials('gitlab', username, token, email)
                            
                            QMessageBox.information(
                                self,
                                "Éxito",
                                f"Cuenta de GitLab conectada:\n{username}"
                            )
                            
                            self.load_accounts()
                            self.accounts_changed.emit()
                        else:
                            QMessageBox.warning(self, "Error", "No se pudo obtener información del usuario")
                    else:
                        QMessageBox.warning(self, "Error", "No se recibió token de acceso")
                else:
                    QMessageBox.warning(self, "Error", f"Error al intercambiar código: {response.status_code}")
                    
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error en OAuth:\n{str(e)}")
    
    def add_github_token(self):
        token = self.github_token.text().strip()
        
        if not token:
            QMessageBox.warning(self, "Error", "Ingresa un token válido")
            return
        
        try:
            response = requests.get(
                'https://api.github.com/user',
                headers={'Authorization': f'token {token}'}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                username = user_data.get('login')
                email = user_data.get('email')
                
                self.account_manager.add_account('github', username, token, email)
                self.account_manager.configure_git_credentials('github', username, token, email)
                
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Cuenta de GitHub agregada:\n{username}"
                )
                
                self.github_token.clear()
                self.load_accounts()
                self.accounts_changed.emit()
            else:
                QMessageBox.warning(self, "Error", "Token inválido o sin permisos")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al verificar token:\n{str(e)}")
    
    def add_gitlab_token(self):
        token = self.gitlab_token.text().strip()
        gitlab_url = self.gitlab_url.text().strip()
        
        if not token:
            QMessageBox.warning(self, "Error", "Ingresa un token válido")
            return
        
        try:
            response = requests.get(
                f"{gitlab_url}/api/v4/user",
                headers={'Authorization': f'Bearer {token}'}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                username = user_data.get('username')
                email = user_data.get('email')
                
                self.account_manager.add_account('gitlab', username, token, email)
                self.account_manager.configure_git_credentials('gitlab', username, token, email)
                
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Cuenta de GitLab agregada:\n{username}"
                )
                
                self.gitlab_token.clear()
                self.load_accounts()
                self.accounts_changed.emit()
            else:
                QMessageBox.warning(self, "Error", "Token inválido o sin permisos")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al verificar token:\n{str(e)}")
    
    def copy_code_to_clipboard(self, code):
        clipboard = QApplication.clipboard()
        clipboard.setText(code)
        QMessageBox.information(
            self, 
            "Código copiado", 
            f"El código '{code}' ha sido copiado al portapapeles."
        )
    
    def save_git_config(self):
        name = self.git_name.text().strip()
        email = self.git_email.text().strip()
        
        if not name or not email:
            QMessageBox.warning(self, "Error", "Ingresa nombre y email")
            return
        
        try:
            import subprocess
            subprocess.run(['git', 'config', '--global', 'user.name', name], check=True)
            subprocess.run(['git', 'config', '--global', 'user.email', email], check=True)
            
            QMessageBox.information(
                self,
                "Éxito",
                f"Configuración guardada:\n\nNombre: {name}\nEmail: {email}"
            )
            
            self.load_git_config()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al guardar configuración:\n{str(e)}")
    
    def load_git_config(self):
        try:
            import subprocess
            
            result_name = subprocess.run(
                ['git', 'config', '--global', 'user.name'],
                capture_output=True,
                text=True
            )
            
            result_email = subprocess.run(
                ['git', 'config', '--global', 'user.email'],
                capture_output=True,
                text=True
            )
            
            name = result_name.stdout.strip() if result_name.returncode == 0 else "No configurado"
            email = result_email.stdout.strip() if result_email.returncode == 0 else "No configurado"
            
            self.current_config.setText(
                f"user.name = {name}\n"
                f"user.email = {email}"
            )
            
            self.git_name.setText(name if name != "No configurado" else "")
            self.git_email.setText(email if email != "No configurado" else "")
            
        except Exception as e:
            self.current_config.setText(f"Error al cargar configuración:\n{str(e)}")
    
    def create_plugins_section(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info = QLabel("Plugins instalados:")
        info.setStyleSheet("font-size: 13px; margin: 10px;")
        layout.addWidget(info)
        
        self.plugins_list = QListWidget()
        self.plugins_list.setStyleSheet("""
            QListWidget {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: palette(button);
            }
            QListWidget::item:selected {
                background-color: palette(highlight);
            }
        """)
        layout.addWidget(self.plugins_list)
        
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Actualizar")
        refresh_btn.setIcon(self.icon_manager.get_icon("arrows-clockwise"))
        refresh_btn.clicked.connect(self.load_plugins)
        btn_layout.addWidget(refresh_btn)
        
        btn_layout.addStretch()
        
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: palette(button);
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: palette(button);
            }
        """)
        
        layout.addLayout(btn_layout)
        
        self.load_plugins()
        
        return widget
    
    def load_plugins(self):
        self.plugins_list.clear()
        
        if not self.plugin_manager:
            item = QListWidgetItem("No hay plugin manager disponible")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.plugins_list.addItem(item)
            return
        
        plugins = self.plugin_manager.get_plugins()
        
        if not plugins:
            item = QListWidgetItem("No hay plugins instalados")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.plugins_list.addItem(item)
            return
        
        for plugin in plugins:
            widget = QWidget()
            widget.setMinimumHeight(70)
            plugin_layout = QHBoxLayout(widget)
            plugin_layout.setContentsMargins(10, 8, 10, 8)
            plugin_layout.setSpacing(12)
            
            icon_container = QWidget()
            icon_container.setFixedWidth(48)
            icon_layout = QVBoxLayout(icon_container)
            icon_layout.setContentsMargins(0, 0, 0, 0)
            icon_layout.addStretch()
            
            icon_label = QLabel()
            icon_label.setFixedSize(48, 48)
            
            is_enabled = self.plugin_manager.is_plugin_enabled(plugin['name'])
            icon_path = "ui/Icons/plugs-connected.svg" if is_enabled else "ui/Icons/plugs.svg"
            
            if os.path.exists(icon_path):
                pixmap = QPixmap(48, 48)
                pixmap.fill(Qt.GlobalColor.transparent)
                renderer = QSvgRenderer(icon_path)
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                icon_label.setPixmap(pixmap)
            else:
                icon_label.setPixmap(self.icon_manager.get_pixmap("plugs-connected", size=24))
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            icon_layout.addWidget(icon_label)
            icon_layout.addStretch()
            
            plugin_layout.addWidget(icon_container)
            
            info_layout = QVBoxLayout()
            info_layout.setSpacing(4)
            
            status_text = "Activo" if is_enabled else "Inactivo"
            name_label = QLabel(f"<b>{plugin['name']}</b> ({status_text})")
            name_label.setStyleSheet("font-size: 14px;")
            info_layout.addWidget(name_label)
            
            if plugin.get('description'):
                desc_label = QLabel(plugin['description'])
                desc_label.setStyleSheet("font-size: 12px; color: palette(text);")
                info_layout.addWidget(desc_label)
            
            version_label = QLabel(f"Versión: {plugin.get('version', '1.0.0')}")
            version_label.setStyleSheet("font-size: 11px; color: palette(text);")
            info_layout.addWidget(version_label)
            
            plugin_layout.addLayout(info_layout, 1)
            
            toggle_btn = QPushButton("Desactivar" if is_enabled else "Activar")
            toggle_btn.setFixedWidth(100)
            toggle_btn.clicked.connect(lambda checked, p=plugin['name']: self.toggle_plugin(p))
            toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {'#c42b1c' if is_enabled else '#238636'};
                    color: palette(bright-text);
                    padding: 8px 16px;
                    border-radius: 5px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {'#a52315' if is_enabled else '#2ea043'};
                }}
            """)
            plugin_layout.addWidget(toggle_btn)
            
            plugin_layout.addStretch()
            
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self.plugins_list.addItem(item)
            self.plugins_list.setItemWidget(item, widget)
    
    def toggle_plugin(self, plugin_name):
        if not self.plugin_manager:
            return
        
        is_enabled = self.plugin_manager.is_plugin_enabled(plugin_name)
        
        if is_enabled:
            self.plugin_manager.disable_plugin(plugin_name)
            QMessageBox.information(
                self,
                "Plugin desactivado",
                f"El plugin '{plugin_name}' ha sido desactivado.\nReinicia la aplicación para aplicar los cambios."
            )
        else:
            self.plugin_manager.enable_plugin(plugin_name)
            QMessageBox.information(
                self,
                "Plugin activado",
                f"El plugin '{plugin_name}' ha sido activado.\nReinicia la aplicación para aplicar los cambios."
            )
        
        self.load_plugins()
    
    def create_appearance_section(self):
        """Crea la sección de apariencia"""
        from ui.theme_manager import theme_manager
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        title = QLabel("Personalización de Apariencia")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: palette(link); margin-bottom: 10px;")
        layout.addWidget(title)
        
        theme_group = QGroupBox("Tema de color")
        theme_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
            }
        """)
        theme_layout = QVBoxLayout()
        theme_layout.setSpacing(15)
        
        info_label = QLabel("Selecciona el tema que prefieras para la interfaz:")
        info_label.setStyleSheet("color: palette(text); font-size: 12px; margin: 5px 0;")
        theme_layout.addWidget(info_label)
        
        current_theme = theme_manager.get_theme_name()
        
        themes_container = QWidget()
        themes_layout = QVBoxLayout(themes_container)
        themes_layout.setSpacing(10)
        
        self.theme_buttons = []
        
        for theme_name in theme_manager.get_available_themes():
            theme_widget = QWidget()
            theme_widget.setMinimumHeight(80)
            theme_h_layout = QHBoxLayout(theme_widget)
            theme_h_layout.setContentsMargins(15, 10, 15, 10)
            theme_h_layout.setSpacing(15)
            
            if theme_name == "Dark":
                theme_title = "Oscuro"
                theme_desc = "Tema oscuro ideal para trabajar de noche o en ambientes con poca luz"
            else:  # Light
                theme_title = "Claro"
                theme_desc = "Tema claro y brillante para trabajar durante el día"
            
            info_v_layout = QVBoxLayout()
            info_v_layout.setSpacing(4)
            
            name_label = QLabel(f"<b>{theme_title}</b>")
            name_label.setStyleSheet("font-size: 14px;")
            info_v_layout.addWidget(name_label)
            
            desc_label = QLabel(theme_desc)
            desc_label.setStyleSheet("font-size: 12px; color: palette(text);")
            desc_label.setWordWrap(True)
            info_v_layout.addWidget(desc_label)
            
            theme_h_layout.addLayout(info_v_layout, 1)
            
            select_btn = QPushButton("Seleccionado" if theme_name == current_theme else "Seleccionar")
            select_btn.setFixedWidth(120)
            select_btn.setEnabled(theme_name != current_theme)
            select_btn.clicked.connect(lambda checked, t=theme_name: self.change_theme(t))
            
            if theme_name == current_theme:
                select_btn.setStyleSheet("""
                    QPushButton {
                        background-color: palette(highlight);
                        color: palette(bright-text);
                        padding: 10px 20px;
                        border-radius: 5px;
                        font-weight: bold;
                    }
                """)
            else:
                select_btn.setStyleSheet("""
                    QPushButton {
                        background-color: palette(highlight);
                        color: palette(bright-text);
                        padding: 10px 20px;
                        border-radius: 5px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: palette(highlight);
                    }
                """)
            
            self.theme_buttons.append((theme_name, select_btn))
            theme_h_layout.addWidget(select_btn)
            
            theme_widget.setStyleSheet("""
                QWidget {
                    background-color: palette(button);
                    border-radius: 8px;
                    border: 1px solid palette(mid);
                }
            """)
            
            themes_layout.addWidget(theme_widget)
        
        theme_layout.addWidget(themes_container)
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        restart_info = QLabel("Los cambios de tema se aplican inmediatamente sin necesidad de reiniciar")
        restart_info.setStyleSheet("""
            background-color: palette(highlight);
            color: palette(bright-text);
            padding: 12px;
            border-radius: 5px;
            font-size: 12px;
        """)
        restart_info.setWordWrap(True)
        layout.addWidget(restart_info)
        
        layout.addStretch()
        
        return widget
    
    def change_theme(self, theme_name):
        """Cambia el tema de la aplicación inmediatamente"""
        from ui.theme_manager import theme_manager
        from ui.theme import Theme
        
        theme_manager.set_theme(theme_name)
        
        app = QApplication.instance()
        new_theme = Theme(theme_name)
        new_theme.apply_to_app(app)
        
        for widget in app.allWidgets():
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()
        
        for t_name, btn in self.theme_buttons:
            if t_name == theme_name:
                btn.setText("Seleccionado")
                btn.setEnabled(False)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: palette(highlight);
                        color: palette(bright-text);
                        padding: 10px 20px;
                        border-radius: 5px;
                        font-weight: bold;
                    }
                """)
            else:
                btn.setText("Seleccionar")
                btn.setEnabled(True)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: palette(highlight);
                        color: palette(bright-text);
                        padding: 10px 20px;
                        border-radius: 5px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: palette(highlight);
                    }
                """)
        
    
    def retranslate_ui(self):
        self.setWindowTitle(tr('settings'))
        self.setWindowIcon(self.icon_manager.get_icon("gear-six"))
        
        if hasattr(self, 'title_label'):
            self.title_label.setText(tr("settings"))
        
        if hasattr(self, 'tabs'):
            current_index = self.tabs.currentIndex()
            tab_count = 0
            self.tabs.setTabText(tab_count, tr("general"))
            self.tabs.setTabIcon(tab_count, self.icon_manager.get_icon("gear-six"))
            tab_count += 1
            self.tabs.setTabText(tab_count, tr("accounts"))
            self.tabs.setTabIcon(tab_count, self.icon_manager.get_icon("user"))
            tab_count += 1
            if self.plugin_manager:
                self.tabs.setTabText(tab_count, tr("plugins"))
                self.tabs.setTabIcon(tab_count, self.icon_manager.get_icon("plugs-connected"))
                tab_count += 1
            self.tabs.setTabText(tab_count, tr("appearance"))
            self.tabs.setTabIcon(tab_count, self.icon_manager.get_icon("globe"))
        
        if hasattr(self, 'close_button'):
            self.close_button.setText(tr('close'))
        
        if hasattr(self, 'parent') and callable(self.parent):
            parent_widget = self.parent()
            if parent_widget and hasattr(parent_widget, 'update_translations'):
                parent_widget.update_translations()
            
            if parent_widget and hasattr(parent_widget, 'tab_widget'):
                for i in range(parent_widget.tab_widget.count()):
                    tab = parent_widget.tab_widget.widget(i)
                    if hasattr(tab, 'home_view') and hasattr(tab.home_view, 'update_translations'):
                        tab.home_view.update_translations()
                    if hasattr(tab, 'update_translations'):
                        tab.update_translations()

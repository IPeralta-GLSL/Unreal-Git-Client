from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QWidget, QLabel, QPushButton, QListWidget, QListWidgetItem,
                             QMessageBox, QLineEdit, QComboBox, QTextEdit, QGroupBox,
                             QProgressDialog, QFrame)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon, QFont
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import hashlib

class OAuthThread(QThread):
    finished = pyqtSignal(bool, object)
    
    def __init__(self, account_manager, account_type):
        super().__init__()
        self.account_manager = account_manager
        self.account_type = account_type
    
    def run(self):
        try:
            if self.account_type == 'github':
                result = self.account_manager.login_github()
            elif self.account_type == 'gitlab':
                result = self.account_manager.login_gitlab()
            else:
                result = None
            
            if result:
                self.finished.emit(True, result)
            else:
                self.finished.emit(False, None)
        except Exception as e:
            self.finished.emit(False, str(e))

class SettingsDialog(QDialog):
    def __init__(self, account_manager, parent=None):
        super().__init__(parent)
        self.account_manager = account_manager
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.on_avatar_downloaded)
        self.avatar_cache = {}
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("⚙️ Configuración")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                background-color: #252526;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #cccccc;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #252526;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #3d3d3d;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        tabs = QTabWidget()
        tabs.addTab(self.create_accounts_tab(), "👤 Cuentas")
        tabs.addTab(self.create_general_tab(), "⚙️ General")
        tabs.addTab(self.create_about_tab(), "ℹ️ Acerca de")
        
        layout.addWidget(tabs)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Cerrar")
        close_btn.setMinimumSize(100, 35)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def create_accounts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        header = QLabel("Administración de Cuentas Git")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        layout.addWidget(header)
        
        desc = QLabel("Conecta tus cuentas de GitHub y GitLab para facilitar el acceso a repositorios")
        desc.setStyleSheet("color: #888888; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        layout.addSpacing(10)
        
        accounts_group = QGroupBox("Cuentas Conectadas")
        accounts_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        accounts_layout = QVBoxLayout()
        
        self.accounts_list = QListWidget()
        self.accounts_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 5px;
                margin: 3px;
            }
            QListWidget::item:hover {
                background-color: #2d2d2d;
            }
            QListWidget::item:selected {
                background-color: #094771;
            }
        """)
        self.accounts_list.setIconSize(QSize(48, 48))
        accounts_layout.addWidget(self.accounts_list)
        
        accounts_group.setLayout(accounts_layout)
        layout.addWidget(accounts_group)
        
        buttons_layout = QHBoxLayout()
        
        github_btn = QPushButton("🐙 Conectar GitHub")
        github_btn.setMinimumHeight(40)
        github_btn.setStyleSheet("""
            QPushButton {
                background-color: #24292e;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2f363d;
            }
        """)
        github_btn.clicked.connect(lambda: self.connect_account('github'))
        buttons_layout.addWidget(github_btn)
        
        gitlab_btn = QPushButton("🦊 Conectar GitLab")
        gitlab_btn.setMinimumHeight(40)
        gitlab_btn.setStyleSheet("""
            QPushButton {
                background-color: #fc6d26;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e24329;
            }
        """)
        gitlab_btn.clicked.connect(lambda: self.connect_account('gitlab'))
        buttons_layout.addWidget(gitlab_btn)
        
        manual_btn = QPushButton("🔑 Token Manual")
        manual_btn.setMinimumHeight(40)
        manual_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)
        manual_btn.clicked.connect(self.add_manual_token)
        buttons_layout.addWidget(manual_btn)
        
        layout.addLayout(buttons_layout)
        
        remove_layout = QHBoxLayout()
        remove_layout.addStretch()
        
        remove_btn = QPushButton("🗑️ Eliminar Cuenta")
        remove_btn.setMinimumSize(150, 35)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #f44336;
            }
        """)
        remove_btn.clicked.connect(self.remove_account)
        remove_layout.addWidget(remove_btn)
        
        configure_btn = QPushButton("⚙️ Configurar Git")
        configure_btn.setMinimumSize(150, 35)
        configure_btn.setStyleSheet("""
            QPushButton {
                background-color: #16825d;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1a9d6f;
            }
        """)
        configure_btn.clicked.connect(self.configure_git)
        remove_layout.addWidget(configure_btn)
        
        layout.addLayout(remove_layout)
        
        self.load_accounts()
        
        return widget
    
    def create_general_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QLabel("Configuración General")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        layout.addWidget(header)
        
        layout.addSpacing(20)
        
        info = QLabel("🚧 Más opciones de configuración próximamente...")
        info.setStyleSheet("color: #888888; font-size: 14px;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)
        
        layout.addStretch()
        
        return widget
    
    def create_about_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        logo = QLabel("🎮")
        logo.setStyleSheet("font-size: 64px;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)
        
        title = QLabel("Unreal Git Client")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        version = QLabel("Versión 1.0.0")
        version.setStyleSheet("font-size: 14px; color: #888888;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)
        
        layout.addSpacing(20)
        
        desc = QLabel(
            "Cliente Git intuitivo diseñado específicamente\n"
            "para proyectos de Unreal Engine con soporte\n"
            "completo de Git LFS y gestión de cuentas."
        )
        desc.setStyleSheet("font-size: 13px; color: #cccccc;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)
        
        layout.addSpacing(30)
        
        features = QLabel(
            "✨ Características:\n\n"
            "• Soporte Git LFS para archivos grandes\n"
            "• Gestión de múltiples cuentas (GitHub/GitLab)\n"
            "• Interfaz intuitiva con pestañas\n"
            "• Administración avanzada de ramas\n"
            "• Integración con Unreal Engine\n"
            "• Avatares de colaboradores\n"
            "• Repositorios recientes"
        )
        features.setStyleSheet("font-size: 12px; color: #cccccc;")
        features.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(features)
        
        layout.addStretch()
        
        return widget
    
    def load_accounts(self):
        self.accounts_list.clear()
        accounts = self.account_manager.get_accounts()
        
        for account in accounts:
            account_type = account['type']
            username = account['username']
            email = account.get('email', 'Sin email')
            avatar_url = account.get('avatar_url')
            
            if account_type == 'github':
                icon_text = "🐙"
                type_name = "GitHub"
            elif account_type == 'gitlab':
                icon_text = "🦊"
                type_name = "GitLab"
            else:
                icon_text = "🔑"
                type_name = "Git"
            
            item = QListWidgetItem()
            item.setText(f"{icon_text}  {username}\n    {type_name} • {email}")
            item.setData(Qt.ItemDataRole.UserRole, account)
            
            font = QFont("Segoe UI", 11)
            item.setFont(font)
            
            if avatar_url:
                self.download_avatar(avatar_url, item)
            else:
                item.setIcon(self.create_default_icon(username))
            
            self.accounts_list.addItem(item)
    
    def create_default_icon(self, username):
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        from PyQt6.QtGui import QPainter, QBrush, QColor
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setBrush(QBrush(QColor('#4ec9b0')))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 48, 48)
        
        painter.setPen(QColor('#ffffff'))
        font = QFont('Arial', 16, QFont.Weight.Bold)
        painter.setFont(font)
        
        initials = username[0].upper() if username else "?"
        painter.drawText(0, 0, 48, 48, Qt.AlignmentFlag.AlignCenter, initials)
        painter.end()
        
        return QIcon(pixmap)
    
    def download_avatar(self, url, item):
        from PyQt6.QtCore import QUrl
        request = QNetworkRequest(QUrl(url))
        request.setAttribute(QNetworkRequest.Attribute.User, item)
        self.network_manager.get(request)
    
    def on_avatar_downloaded(self, reply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            item = reply.request().attribute(QNetworkRequest.Attribute.User)
            image_data = reply.readAll()
            
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                pixmap = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
                
                rounded = QPixmap(48, 48)
                rounded.fill(Qt.GlobalColor.transparent)
                
                from PyQt6.QtGui import QPainter, QBrush
                painter = QPainter(rounded)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setBrush(QBrush(pixmap))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(0, 0, 48, 48)
                painter.end()
                
                item.setIcon(QIcon(rounded))
        
        reply.deleteLater()
    
    def connect_account(self, account_type):
        progress = QProgressDialog(
            f"Abriendo navegador para autenticar con {account_type.title()}...\n\n"
            "Por favor, completa la autenticación en tu navegador.",
            "Cancelar",
            0, 0,
            self
        )
        progress.setWindowTitle("Autenticando")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        self.oauth_thread = OAuthThread(self.account_manager, account_type)
        self.oauth_thread.finished.connect(
            lambda success, result: self.on_oauth_finished(success, result, progress, account_type)
        )
        self.oauth_thread.start()
    
    def on_oauth_finished(self, success, result, progress, account_type):
        progress.close()
        
        if success:
            QMessageBox.information(
                self,
                "Éxito",
                f"✅ Cuenta de {account_type.title()} conectada exitosamente!\n\n"
                f"Usuario: {result.get('login') or result.get('username')}"
            )
            self.load_accounts()
        else:
            QMessageBox.warning(
                self,
                "Error",
                f"❌ No se pudo conectar la cuenta de {account_type.title()}.\n\n"
                "Verifica tu conexión a internet e intenta nuevamente."
            )
    
    def add_manual_token(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Agregar Token Manual")
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet("QDialog { background-color: #1e1e1e; }")
        
        layout = QVBoxLayout(dialog)
        
        type_layout = QHBoxLayout()
        type_label = QLabel("Tipo:")
        type_label.setStyleSheet("color: white; font-weight: bold;")
        type_layout.addWidget(type_label)
        
        type_combo = QComboBox()
        type_combo.addItems(["GitHub", "GitLab", "Git"])
        type_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        type_layout.addWidget(type_combo)
        layout.addLayout(type_layout)
        
        username_label = QLabel("Usuario:")
        username_label.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(username_label)
        
        username_input = QLineEdit()
        username_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 8px;
            }
        """)
        layout.addWidget(username_input)
        
        email_label = QLabel("Email:")
        email_label.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(email_label)
        
        email_input = QLineEdit()
        email_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 8px;
            }
        """)
        layout.addWidget(email_input)
        
        token_label = QLabel("Token de Acceso Personal:")
        token_label.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(token_label)
        
        token_input = QLineEdit()
        token_input.setEchoMode(QLineEdit.EchoMode.Password)
        token_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 8px;
            }
        """)
        layout.addWidget(token_input)
        
        help_label = QLabel(
            "💡 Consejo: Puedes generar un token desde:\n"
            "• GitHub: Settings → Developer settings → Personal access tokens\n"
            "• GitLab: User Settings → Access Tokens"
        )
        help_label.setStyleSheet("color: #888888; font-size: 11px;")
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
        buttons = QHBoxLayout()
        buttons.addStretch()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addWidget(cancel_btn)
        
        add_btn = QPushButton("Agregar")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #16825d;
                color: white;
                padding: 8px 20px;
            }
        """)
        add_btn.clicked.connect(lambda: self.save_manual_token(
            dialog, type_combo.currentText().lower(), 
            username_input.text(), email_input.text(), token_input.text()
        ))
        buttons.addWidget(add_btn)
        
        layout.addLayout(buttons)
        
        dialog.exec()
    
    def save_manual_token(self, dialog, account_type, username, email, token):
        if not username or not token:
            QMessageBox.warning(self, "Error", "Usuario y token son obligatorios")
            return
        
        success = self.account_manager.add_manual_account(account_type, username, email, token)
        if success:
            QMessageBox.information(self, "Éxito", "Cuenta agregada correctamente")
            self.load_accounts()
            dialog.accept()
        else:
            QMessageBox.warning(self, "Error", "No se pudo agregar la cuenta")
    
    def remove_account(self):
        current_item = self.accounts_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Selecciona una cuenta para eliminar")
            return
        
        account = current_item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Eliminar la cuenta de {account['username']} ({account['type']})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.account_manager.remove_account(account['type'], account['username'])
            self.load_accounts()
            QMessageBox.information(self, "Éxito", "Cuenta eliminada")
    
    def configure_git(self):
        current_item = self.accounts_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "Selecciona una cuenta para configurar")
            return
        
        account = current_item.data(Qt.ItemDataRole.UserRole)
        success = self.account_manager.configure_git_credential(account)
        
        if success:
            QMessageBox.information(
                self,
                "Éxito",
                f"✅ Git configurado para usar la cuenta de {account['username']}\n\n"
                "Ahora podrás hacer push/pull sin ingresar credenciales."
            )
        else:
            QMessageBox.warning(
                self,
                "Error",
                "No se pudo configurar Git con esta cuenta."
            )

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QListWidget, QListWidgetItem, QMessageBox,
                             QInputDialog, QLineEdit, QTabWidget, QWidget,
                             QTextEdit, QGroupBox, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
import webbrowser
import requests

class AccountsDialog(QDialog):
    accounts_changed = pyqtSignal()
    
    def __init__(self, account_manager, parent=None):
        super().__init__(parent)
        self.account_manager = account_manager
        self.setWindowTitle("Administración de Cuentas")
        self.setModal(True)
        self.setMinimumSize(700, 500)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("🔐 Gestión de Cuentas Git")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #4ec9b0; margin: 10px;")
        layout.addWidget(title)
        
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                background-color: #1e1e1e;
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
                background-color: #1e1e1e;
                color: #4ec9b0;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #3d3d3d;
            }
        """)
        
        tabs.addTab(self.create_accounts_tab(), "📋 Mis Cuentas")
        tabs.addTab(self.create_github_tab(), "🐙 GitHub")
        tabs.addTab(self.create_gitlab_tab(), "🦊 GitLab")
        tabs.addTab(self.create_git_tab(), "📝 Git Local")
        
        layout.addWidget(tabs)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Cerrar")
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #cccccc;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
        """)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #cccccc;
            }
        """)
    
    def create_accounts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info = QLabel("Tus cuentas conectadas:")
        info.setStyleSheet("font-size: 13px; margin: 10px;")
        layout.addWidget(info)
        
        self.accounts_list = QListWidget()
        self.accounts_list.setStyleSheet("""
            QListWidget {
                background-color: #252526;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #2d2d2d;
            }
            QListWidget::item:selected {
                background-color: #094771;
            }
        """)
        layout.addWidget(self.accounts_list)
        
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.clicked.connect(self.load_accounts)
        btn_layout.addWidget(refresh_btn)
        
        remove_btn = QPushButton("🗑️ Eliminar")
        remove_btn.clicked.connect(self.remove_selected_account)
        btn_layout.addWidget(remove_btn)
        
        btn_layout.addStretch()
        
        for btn in [refresh_btn, remove_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2d2d2d;
                    padding: 8px 16px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #3d3d3d;
                }
            """)
        
        layout.addLayout(btn_layout)
        
        self.load_accounts()
        
        return widget
    
    def create_github_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info_box = QGroupBox("ℹ️ Conectar con GitHub")
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
            "Para conectar tu cuenta de GitHub, necesitas crear una OAuth App:\n\n"
            "1. Ve a GitHub → Settings → Developer settings → OAuth Apps\n"
            "2. Click en 'New OAuth App'\n"
            "3. Completa:\n"
            "   • Application name: Unreal Git Client\n"
            "   • Homepage URL: http://localhost\n"
            "   • Authorization callback URL: http://localhost:8888/callback\n"
            "4. Copia el Client ID y genera un Client Secret\n"
            "5. Pégalos abajo y haz click en 'Conectar con GitHub'"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("font-size: 12px; font-weight: normal; padding: 10px;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_box)
        
        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)
        
        client_id_label = QLabel("Client ID:")
        self.github_client_id = QLineEdit()
        self.github_client_id.setPlaceholderText("Ingresa tu GitHub Client ID")
        self.github_client_id.setStyleSheet("""
            QLineEdit {
                background-color: #252526;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 8px;
                color: #cccccc;
            }
        """)
        form_layout.addWidget(client_id_label)
        form_layout.addWidget(self.github_client_id)
        
        client_secret_label = QLabel("Client Secret:")
        self.github_client_secret = QLineEdit()
        self.github_client_secret.setPlaceholderText("Ingresa tu GitHub Client Secret")
        self.github_client_secret.setEchoMode(QLineEdit.EchoMode.Password)
        self.github_client_secret.setStyleSheet(self.github_client_id.styleSheet())
        form_layout.addWidget(client_secret_label)
        form_layout.addWidget(self.github_client_secret)
        
        layout.addLayout(form_layout)
        
        connect_btn = QPushButton("🔗 Conectar con GitHub")
        connect_btn.setMinimumHeight(40)
        connect_btn.clicked.connect(self.connect_github)
        connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)
        layout.addWidget(connect_btn)
        
        manual_label = QLabel("O agrega manualmente un Personal Access Token:")
        manual_label.setStyleSheet("margin-top: 20px; font-size: 12px;")
        layout.addWidget(manual_label)
        
        token_layout = QHBoxLayout()
        self.github_token = QLineEdit()
        self.github_token.setPlaceholderText("ghp_...")
        self.github_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.github_token.setStyleSheet(self.github_client_id.styleSheet())
        token_layout.addWidget(self.github_token)
        
        add_token_btn = QPushButton("➕ Agregar Token")
        add_token_btn.clicked.connect(self.add_github_token)
        add_token_btn.setStyleSheet(connect_btn.styleSheet())
        token_layout.addWidget(add_token_btn)
        
        layout.addLayout(token_layout)
        
        layout.addStretch()
        
        return widget
    
    def create_gitlab_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info_box = QGroupBox("ℹ️ Conectar con GitLab")
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
            "Para conectar tu cuenta de GitLab:\n\n"
            "1. Ve a GitLab → Preferences → Applications\n"
            "2. Click en 'Add new application'\n"
            "3. Completa:\n"
            "   • Name: Unreal Git Client\n"
            "   • Redirect URI: http://localhost:8888/callback\n"
            "   • Scopes: api, read_user, write_repository\n"
            "4. Copia el Application ID y Secret\n"
            "5. Pégalos abajo y haz click en 'Conectar con GitLab'"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("font-size: 12px; font-weight: normal; padding: 10px;")
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_box)
        
        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)
        
        url_label = QLabel("URL de GitLab:")
        self.gitlab_url = QLineEdit()
        self.gitlab_url.setText("https://gitlab.com")
        self.gitlab_url.setStyleSheet("""
            QLineEdit {
                background-color: #252526;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 8px;
                color: #cccccc;
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
        
        connect_btn = QPushButton("🔗 Conectar con GitLab")
        connect_btn.setMinimumHeight(40)
        connect_btn.clicked.connect(self.connect_gitlab)
        connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #fc6d26;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #fd7e3d;
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
                background-color: #252526;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 8px;
                color: #cccccc;
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
        
        save_btn = QPushButton("💾 Guardar Configuración Global")
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self.save_git_config)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #16825d;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1a9d6f;
            }
        """)
        layout.addWidget(save_btn)
        
        current_group = QGroupBox("⚙️ Configuración Actual")
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
                background-color: #252526;
                border: 1px solid #3d3d3d;
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
            platform_icons = {
                'github': '🐙',
                'gitlab': '🦊',
                'git': '📝'
            }
            
            icon = platform_icons.get(account['platform'], '📝')
            status = '✅' if account.get('active', True) else '⭕'
            
            text = f"{icon} {status} {account['platform'].upper()}: {account['username']}"
            if account.get('email'):
                text += f" ({account['email']})"
            
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, account)
            self.accounts_list.addItem(item)
    
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
    
    def connect_github(self):
        client_id = self.github_client_id.text().strip()
        client_secret = self.github_client_secret.text().strip()
        
        if not client_id or not client_secret:
            QMessageBox.warning(self, "Error", "Ingresa Client ID y Client Secret")
            return
        
        success, result = self.account_manager.start_oauth_server(8888)
        if not success:
            QMessageBox.warning(self, "Error", f"No se pudo iniciar servidor OAuth:\n{result}")
            return
        
        redirect_uri = "http://localhost:8888/callback"
        auth_url = self.account_manager.github_oauth_url(client_id, redirect_uri)
        
        webbrowser.open(auth_url)
        
        QMessageBox.information(
            self,
            "Autenticación en progreso",
            "Se abrió tu navegador para autenticar.\n\n"
            "Autoriza la aplicación y espera a que se complete."
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

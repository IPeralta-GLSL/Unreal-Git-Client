from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QListWidget, QListWidgetItem,
                             QTabWidget, QWidget, QMessageBox, QGroupBox,
                             QFormLayout, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from ui.icon_manager import IconManager
from ui.theme import get_current_theme


class SettingsDialog(QDialog):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.icon_manager = IconManager()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Ajustes")
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_github_tab(), "GitHub")
        self.tab_widget.addTab(self.create_gitlab_tab(), "GitLab")
        
        layout.addWidget(self.tab_widget)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.apply_styles()
        
    def create_github_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        header = QLabel("Administrar Cuentas de GitHub")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: palette(link); padding: 10px;")
        layout.addWidget(header)
        
        form_group = QGroupBox("Agregar/Editar Cuenta")
        form_layout = QFormLayout()
        
        self.github_username_input = QLineEdit()
        self.github_username_input.setPlaceholderText("Nombre de usuario")
        form_layout.addRow("Usuario:", self.github_username_input)
        
        self.github_email_input = QLineEdit()
        self.github_email_input.setPlaceholderText("email@example.com (opcional)")
        form_layout.addRow("Email:", self.github_email_input)
        
        self.github_token_input = QLineEdit()
        self.github_token_input.setPlaceholderText("Personal Access Token")
        self.github_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Token:", self.github_token_input)
        
        show_token_btn = QPushButton("Mostrar")
        show_token_btn.setMaximumWidth(80)
        show_token_btn.clicked.connect(lambda: self.toggle_token_visibility(self.github_token_input, show_token_btn))
        token_layout = QHBoxLayout()
        token_layout.addWidget(self.github_token_input)
        token_layout.addWidget(show_token_btn)
        form_layout.addRow("", token_layout)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        button_layout = QHBoxLayout()
        add_btn = QPushButton("Agregar Cuenta")
        add_btn.clicked.connect(self.add_github_account)
        button_layout.addWidget(add_btn)
        
        update_btn = QPushButton("Actualizar Cuenta")
        update_btn.clicked.connect(self.update_github_account)
        button_layout.addWidget(update_btn)
        
        clear_btn = QPushButton("Limpiar Campos")
        clear_btn.clicked.connect(self.clear_github_fields)
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        accounts_group = QGroupBox("Cuentas Guardadas")
        accounts_layout = QVBoxLayout()
        
        self.github_list = QListWidget()
        self.github_list.itemClicked.connect(self.on_github_account_selected)
        accounts_layout.addWidget(self.github_list)
        
        list_button_layout = QHBoxLayout()
        delete_btn = QPushButton("Eliminar Cuenta")
        delete_btn.clicked.connect(self.delete_github_account)
        list_button_layout.addWidget(delete_btn)
        list_button_layout.addStretch()
        
        accounts_layout.addLayout(list_button_layout)
        accounts_group.setLayout(accounts_layout)
        layout.addWidget(accounts_group)
        
        self.load_github_accounts()
        
        return widget
        
    def create_gitlab_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        header = QLabel("Administrar Cuentas de GitLab")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: palette(link); padding: 10px;")
        layout.addWidget(header)
        
        form_group = QGroupBox("Agregar/Editar Cuenta")
        form_layout = QFormLayout()
        
        self.gitlab_username_input = QLineEdit()
        self.gitlab_username_input.setPlaceholderText("Nombre de usuario")
        form_layout.addRow("Usuario:", self.gitlab_username_input)
        
        self.gitlab_email_input = QLineEdit()
        self.gitlab_email_input.setPlaceholderText("email@example.com (opcional)")
        form_layout.addRow("Email:", self.gitlab_email_input)
        
        self.gitlab_server_input = QLineEdit()
        self.gitlab_server_input.setPlaceholderText("https://gitlab.com")
        self.gitlab_server_input.setText("https://gitlab.com")
        form_layout.addRow("Servidor:", self.gitlab_server_input)
        
        self.gitlab_token_input = QLineEdit()
        self.gitlab_token_input.setPlaceholderText("Personal Access Token")
        self.gitlab_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Token:", self.gitlab_token_input)
        
        show_token_btn = QPushButton("Mostrar")
        show_token_btn.setMaximumWidth(80)
        show_token_btn.clicked.connect(lambda: self.toggle_token_visibility(self.gitlab_token_input, show_token_btn))
        token_layout = QHBoxLayout()
        token_layout.addWidget(self.gitlab_token_input)
        token_layout.addWidget(show_token_btn)
        form_layout.addRow("", token_layout)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        button_layout = QHBoxLayout()
        add_btn = QPushButton("Agregar Cuenta")
        add_btn.clicked.connect(self.add_gitlab_account)
        button_layout.addWidget(add_btn)
        
        update_btn = QPushButton("Actualizar Cuenta")
        update_btn.clicked.connect(self.update_gitlab_account)
        button_layout.addWidget(update_btn)
        
        clear_btn = QPushButton("Limpiar Campos")
        clear_btn.clicked.connect(self.clear_gitlab_fields)
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        accounts_group = QGroupBox("Cuentas Guardadas")
        accounts_layout = QVBoxLayout()
        
        self.gitlab_list = QListWidget()
        self.gitlab_list.itemClicked.connect(self.on_gitlab_account_selected)
        accounts_layout.addWidget(self.gitlab_list)
        
        list_button_layout = QHBoxLayout()
        delete_btn = QPushButton("Eliminar Cuenta")
        delete_btn.clicked.connect(self.delete_gitlab_account)
        list_button_layout.addWidget(delete_btn)
        list_button_layout.addStretch()
        
        accounts_layout.addLayout(list_button_layout)
        accounts_group.setLayout(accounts_layout)
        layout.addWidget(accounts_group)
        
        self.load_gitlab_accounts()
        
        return widget
        
    def toggle_token_visibility(self, token_input, button):
        if token_input.echoMode() == QLineEdit.EchoMode.Password:
            token_input.setEchoMode(QLineEdit.EchoMode.Normal)
            button.setText("Ocultar")
        else:
            token_input.setEchoMode(QLineEdit.EchoMode.Password)
            button.setText("Mostrar")
            
    def add_github_account(self):
        username = self.github_username_input.text().strip()
        token = self.github_token_input.text().strip()
        email = self.github_email_input.text().strip()
        
        if not username or not token:
            QMessageBox.warning(self, "Campos requeridos", "Usuario y Token son obligatorios")
            return
            
        self.settings_manager.add_github_account(username, token, email)
        self.load_github_accounts()
        self.clear_github_fields()
        QMessageBox.information(self, "Éxito", f"Cuenta de GitHub '{username}' agregada correctamente")
        
    def add_gitlab_account(self):
        username = self.gitlab_username_input.text().strip()
        token = self.gitlab_token_input.text().strip()
        email = self.gitlab_email_input.text().strip()
        server = self.gitlab_server_input.text().strip()
        
        if not username or not token or not server:
            QMessageBox.warning(self, "Campos requeridos", "Usuario, Token y Servidor son obligatorios")
            return
            
        self.settings_manager.add_gitlab_account(username, token, email, server)
        self.load_gitlab_accounts()
        self.clear_gitlab_fields()
        QMessageBox.information(self, "Éxito", f"Cuenta de GitLab '{username}' agregada correctamente")
        
    def update_github_account(self):
        username = self.github_username_input.text().strip()
        token = self.github_token_input.text().strip()
        email = self.github_email_input.text().strip()
        
        if not username:
            QMessageBox.warning(self, "Campo requerido", "Usuario es obligatorio")
            return
            
        accounts = self.settings_manager.get_github_accounts()
        exists = any(acc['username'] == username for acc in accounts)
        
        if not exists:
            QMessageBox.warning(self, "Cuenta no encontrada", f"No existe una cuenta con el usuario '{username}'")
            return
            
        self.settings_manager.update_github_account(
            username, 
            token if token else None, 
            email if email else None
        )
        self.load_github_accounts()
        QMessageBox.information(self, "Éxito", f"Cuenta de GitHub '{username}' actualizada correctamente")
        
    def update_gitlab_account(self):
        username = self.gitlab_username_input.text().strip()
        token = self.gitlab_token_input.text().strip()
        email = self.gitlab_email_input.text().strip()
        server = self.gitlab_server_input.text().strip()
        
        if not username or not server:
            QMessageBox.warning(self, "Campos requeridos", "Usuario y Servidor son obligatorios")
            return
            
        accounts = self.settings_manager.get_gitlab_accounts()
        exists = any(acc['username'] == username and acc['server_url'] == server for acc in accounts)
        
        if not exists:
            QMessageBox.warning(self, "Cuenta no encontrada", f"No existe una cuenta con el usuario '{username}' en {server}")
            return
            
        self.settings_manager.update_gitlab_account(
            username, 
            server,
            token if token else None, 
            email if email else None
        )
        self.load_gitlab_accounts()
        QMessageBox.information(self, "Éxito", f"Cuenta de GitLab '{username}' actualizada correctamente")
        
    def delete_github_account(self):
        current_item = self.github_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Sin selección", "Selecciona una cuenta para eliminar")
            return
            
        username = current_item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, 
            "Confirmar eliminación",
            f"¿Estás seguro de eliminar la cuenta '{username}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings_manager.remove_github_account(username)
            self.load_github_accounts()
            self.clear_github_fields()
            QMessageBox.information(self, "Éxito", f"Cuenta '{username}' eliminada correctamente")
            
    def delete_gitlab_account(self):
        current_item = self.gitlab_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Sin selección", "Selecciona una cuenta para eliminar")
            return
            
        data = current_item.data(Qt.ItemDataRole.UserRole)
        username = data['username']
        server = data['server']
        
        reply = QMessageBox.question(
            self, 
            "Confirmar eliminación",
            f"¿Estás seguro de eliminar la cuenta '{username}' en {server}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings_manager.remove_gitlab_account(username, server)
            self.load_gitlab_accounts()
            self.clear_gitlab_fields()
            QMessageBox.information(self, "Éxito", f"Cuenta '{username}' eliminada correctamente")
            
    def on_github_account_selected(self, item):
        username = item.data(Qt.ItemDataRole.UserRole)
        accounts = self.settings_manager.get_github_accounts()
        
        for account in accounts:
            if account['username'] == username:
                self.github_username_input.setText(account['username'])
                self.github_email_input.setText(account.get('email', ''))
                self.github_token_input.setText(account['token'])
                break
                
    def on_gitlab_account_selected(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        accounts = self.settings_manager.get_gitlab_accounts()
        
        for account in accounts:
            if account['username'] == data['username'] and account['server_url'] == data['server']:
                self.gitlab_username_input.setText(account['username'])
                self.gitlab_email_input.setText(account.get('email', ''))
                self.gitlab_server_input.setText(account['server_url'])
                self.gitlab_token_input.setText(account['token'])
                break
                
    def load_github_accounts(self):
        self.github_list.clear()
        accounts = self.settings_manager.get_github_accounts()
        
        for account in accounts:
            username = account['username']
            email = account.get('email', 'Sin email')
            item_text = f"{username} ({email})"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, username)
            self.github_list.addItem(item)
            
    def load_gitlab_accounts(self):
        self.gitlab_list.clear()
        accounts = self.settings_manager.get_gitlab_accounts()
        
        for account in accounts:
            username = account['username']
            email = account.get('email', 'Sin email')
            server = account['server_url']
            item_text = f"{username} ({email}) - {server}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, {'username': username, 'server': server})
            self.gitlab_list.addItem(item)
            
    def clear_github_fields(self):
        self.github_username_input.clear()
        self.github_email_input.clear()
        self.github_token_input.clear()
        self.github_list.clearSelection()
        
    def clear_gitlab_fields(self):
        self.gitlab_username_input.clear()
        self.gitlab_email_input.clear()
        self.gitlab_server_input.setText("https://gitlab.com")
        self.gitlab_token_input.clear()
        self.gitlab_list.clearSelection()
        
    def apply_styles(self):
        theme = get_current_theme()
        self.setStyleSheet(f"""
            QDialog {{
                background-color: palette(window);
            }}
            QLabel {{
                color: palette(window-text);
                font-size: 12px;
            }}
            QLineEdit {{
                background-color: {theme.colors['surface']};
                color: palette(bright-text);
                border: 1px solid {theme.colors['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {theme.colors['border_focus']};
            }}
            QPushButton {{
                background-color: palette(link);
                color: palette(bright-text);
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: palette(highlight);
            }}
            QPushButton:pressed {{
                background-color: palette(highlight);
            }}
            QListWidget {{
                background-color: palette(base);
                color: palette(window-text);
                border: 1px solid {theme.colors['border']};
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-radius: 3px;
            }}
            QListWidget::item:selected {{
                background-color: palette(highlight);
                color: palette(bright-text);
            }}
            QListWidget::item:hover {{
                background-color: {theme.colors['surface_hover']};
            }}
            QTabWidget::pane {{
                border: 1px solid {theme.colors['border']};
                background-color: palette(base);
                border-top: 2px solid {theme.colors['primary']};
            }}
            QTabBar::tab {{
                background-color: palette(button);
                color: palette(window-text);
                border: 1px solid {theme.colors['border']};
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: palette(base);
                color: palette(bright-text);
                border-bottom: 2px solid {theme.colors['primary']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: palette(text);
            }}
            QGroupBox {{
                color: palette(window-text);
                border: 1px solid {theme.colors['border']};
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)

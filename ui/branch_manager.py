from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QListWidget, QPushButton, QLineEdit, QMessageBox,
                             QListWidgetItem, QComboBox, QRadioButton, QButtonGroup,
                             QGroupBox, QTextEdit, QWidget, QFrame)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QColor
from ui.icon_manager import IconManager
from ui.theme import get_current_theme

class BranchManagerDialog(QDialog):
    def __init__(self, git_manager, parent=None):
        super().__init__(parent)
        self.git_manager = git_manager
        self.icon_manager = IconManager()
        self.drag_position = QPoint()
        self.border_width = 5
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.init_ui()
        self.load_branches()
        
    def init_ui(self):
        self.setWindowTitle("Administrador de Ramas")
        self.setModal(True)
        self.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        title_bar = self.create_title_bar()
        layout.addWidget(title_bar)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        current_branch_label = QLabel("Rama actual:")
        current_branch_label.setStyleSheet("color: palette(text); font-size: 12px;")
        content_layout.addWidget(current_branch_label)
        
        self.current_branch = QLabel()
        self.current_branch.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: palette(link);
            background-color: palette(button);
            padding: 10px;
            border-radius: 4px;
        """)
        content_layout.addWidget(self.current_branch)
        
        list_label = QLabel("Todas las Ramas:")
        list_label.setStyleSheet("color: palette(window-text); font-weight: bold; margin-top: 10px;")
        content_layout.addWidget(list_label)
        
        self.branches_list = QListWidget()
        self.branches_list.itemDoubleClicked.connect(self.switch_to_branch)
        content_layout.addWidget(self.branches_list)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.new_branch_btn = QPushButton("  Nueva Rama")
        self.new_branch_btn.setIcon(self.icon_manager.get_icon("plus-circle", size=18))
        self.new_branch_btn.clicked.connect(self.create_new_branch)
        buttons_layout.addWidget(self.new_branch_btn)
        
        self.switch_btn = QPushButton("  Cambiar")
        self.switch_btn.setIcon(self.icon_manager.get_icon("arrows-clockwise", size=18))
        self.switch_btn.clicked.connect(self.switch_to_selected_branch)
        buttons_layout.addWidget(self.switch_btn)
        
        self.delete_btn = QPushButton("  Eliminar")
        self.delete_btn.setIcon(self.icon_manager.get_icon("trash", size=18))
        self.delete_btn.clicked.connect(self.delete_selected_branch)
        buttons_layout.addWidget(self.delete_btn)
        
        self.merge_btn = QPushButton("  Merge")
        self.merge_btn.setIcon(self.icon_manager.get_icon("git-merge", size=18))
        self.merge_btn.clicked.connect(self.merge_selected_branch)
        buttons_layout.addWidget(self.merge_btn)
        
        content_layout.addLayout(buttons_layout)
        
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        content_layout.addWidget(close_btn)
        
        layout.addWidget(content_widget)
        self.apply_styles()
    
    def create_title_bar(self):
        theme = get_current_theme()
        
        title_bar = QFrame()
        title_bar.setFixedHeight(35)
        title_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['surface']};
                border-bottom: 1px solid {theme.colors['border']};
            }}
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 0, 0)
        title_layout.setSpacing(0)
        
        title_icon = QLabel()
        title_icon.setPixmap(self.icon_manager.get_pixmap("git-branch", size=18))
        title_layout.addWidget(title_icon)
        
        title = QLabel("  Administrador de Ramas")
        title.setStyleSheet(f"color: {theme.colors['text']}; font-weight: bold; font-size: 13px;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
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
        title_layout.addWidget(close_button)
        
        title_bar.mousePressEvent = self.title_bar_mouse_press
        
        return title_bar
    
    def title_bar_mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.windowHandle().startSystemMove()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            edges = self.get_window_edges(pos)
            
            if edges != Qt.Edge(0):
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
        pos = event.pos()
        edges = self.get_window_edges(pos)
        self.update_cursor_for_edges(edges)
        
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
        
    def load_branches(self):
        current = self.git_manager.get_current_branch()
        self.current_branch.setText(f"  {current}")
        
        self.branches_list.clear()
        branches = self.git_manager.get_all_branches()
        
        theme = get_current_theme()
        
        for branch in branches:
            name = branch['name']
            item = QListWidgetItem()
            
            if branch['is_current']:
                item.setText(f"  {name} (actual)")
                item.setIcon(self.icon_manager.get_icon("check", size=16))
                item.setForeground(QColor(theme.colors['success']))
            elif branch['is_remote']:
                item.setText(f"  {name}")
                item.setIcon(self.icon_manager.get_icon("share-network", size=16))
                item.setForeground(QColor(theme.colors['primary']))
            else:
                item.setText(f"  {name}")
                item.setIcon(self.icon_manager.get_icon("git-branch", size=16))
                item.setForeground(QColor(theme.colors['text']))
            
            item.setData(Qt.ItemDataRole.UserRole, name)
            self.branches_list.addItem(item)
            
    def create_new_branch(self):
        dialog = CreateBranchDialog(self.git_manager, self)
        if dialog.exec():
            self.load_branches()
            
    def switch_to_branch(self, item):
        branch_name = item.data(Qt.ItemDataRole.UserRole)
        self.switch_branch(branch_name)
        
    def switch_to_selected_branch(self):
        current_item = self.branches_list.currentItem()
        if current_item:
            self.switch_to_branch(current_item)
        else:
            QMessageBox.warning(self, "Aviso", "Selecciona una rama primero")
            
    def switch_branch(self, branch_name):
        reply = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Cambiar a la rama '{branch_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.git_manager.switch_branch(branch_name)
            if success:
                QMessageBox.information(self, "Éxito", f"Cambiado a la rama: {branch_name}")
                self.load_branches()
            else:
                QMessageBox.warning(self, "Error", f"No se pudo cambiar de rama:\n{message}")
                
    def delete_selected_branch(self):
        current_item = self.branches_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Aviso", "Selecciona una rama para eliminar")
            return
            
        branch_name = current_item.data(Qt.ItemDataRole.UserRole)
        
        if "actual" in current_item.text():
            QMessageBox.warning(self, "Error", "No puedes eliminar la rama actual")
            return
            
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Eliminar la rama '{branch_name}'?\n\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.git_manager.delete_branch(branch_name)
            if success:
                QMessageBox.information(self, "Éxito", f"Rama eliminada: {branch_name}")
                self.load_branches()
            else:
                QMessageBox.warning(self, "Error", f"No se pudo eliminar:\n{message}")
                
    def merge_selected_branch(self):
        current_item = self.branches_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Aviso", "Selecciona una rama para hacer merge")
            return
            
        branch_name = current_item.data(Qt.ItemDataRole.UserRole)
        current = self.git_manager.get_current_branch()
        
        reply = QMessageBox.question(
            self,
            "Confirmar Merge",
            f"¿Hacer merge de '{branch_name}' en '{current}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.git_manager.merge_branch(branch_name)
            if success:
                QMessageBox.information(self, "Éxito", "Merge completado correctamente")
            else:
                QMessageBox.warning(self, "Error", f"Error en merge:\n{message}")
                
    def apply_styles(self):
        from ui.theme import get_current_theme
        theme = get_current_theme()
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme.colors['background']};
            }}
            QLabel {{
                color: {theme.colors['text']};
            }}
            QListWidget {{
                background-color: {theme.colors['background_secondary']};
                color: {theme.colors['text']};
                border: 1px solid {theme.colors['border']};
                border-radius: 4px;
                padding: 5px;
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-radius: 3px;
                margin: 2px;
            }}
            QListWidget::item:selected {{
                background-color: {theme.colors['surface_selected']};
                color: {theme.colors['text_inverse']};
            }}
            QListWidget::item:hover {{
                background-color: {theme.colors['surface_hover']};
            }}
            QPushButton {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['text_inverse']};
                border: none;
                border-radius: 4px;
                padding: 10px 15px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {theme.colors['primary_pressed']};
            }}
        """)

class CreateBranchDialog(QDialog):
    def __init__(self, git_manager, parent=None):
        super().__init__(parent)
        self.git_manager = git_manager
        self.icon_manager = IconManager()
        self.drag_position = QPoint()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Crear Nueva Rama")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        title_bar = self.create_title_bar()
        layout.addWidget(title_bar)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        name_label = QLabel("Nombre de la rama:")
        name_label.setStyleSheet("color: palette(window-text); font-weight: bold;")
        content_layout.addWidget(name_label)
        
        self.branch_name_input = QLineEdit()
        self.branch_name_input.setPlaceholderText("feature/nueva-funcionalidad")
        content_layout.addWidget(self.branch_name_input)
        
        source_group = QGroupBox("Crear desde:")
        source_layout = QVBoxLayout()
        
        self.from_current_radio = QRadioButton("Rama actual")
        self.from_current_radio.setChecked(True)
        source_layout.addWidget(self.from_current_radio)
        
        self.from_commit_radio = QRadioButton("Commit específico")
        source_layout.addWidget(self.from_commit_radio)
        
        self.commit_input = QLineEdit()
        self.commit_input.setPlaceholderText("Hash del commit (ej: a1b2c3d)")
        self.commit_input.setEnabled(False)
        source_layout.addWidget(self.commit_input)
        
        self.from_commit_radio.toggled.connect(self.commit_input.setEnabled)
        
        source_group.setLayout(source_layout)
        content_layout.addWidget(source_group)
        
        buttons_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("  Crear Rama")
        create_btn.setIcon(self.icon_manager.get_icon("check", size=18))
        create_btn.clicked.connect(self.create_branch)
        create_btn.setDefault(True)
        buttons_layout.addWidget(create_btn)
        
        content_layout.addLayout(buttons_layout)
        layout.addWidget(content_widget)
        
        self.apply_styles()
    
    def create_title_bar(self):
        theme = get_current_theme()
        
        title_bar = QFrame()
        title_bar.setFixedHeight(35)
        title_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.colors['surface']};
                border-bottom: 1px solid {theme.colors['border']};
            }}
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 0, 0)
        title_layout.setSpacing(0)
        
        icon_label = QLabel()
        icon_label.setPixmap(self.icon_manager.get_pixmap("plus-circle", 18))
        title_layout.addWidget(icon_label)
        
        title_text = QLabel("  Crear Nueva Rama")
        title_text.setStyleSheet(f"color: {theme.colors['text']}; font-weight: bold; font-size: 13px;")
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        
        close_button = QPushButton()
        close_button.setIcon(self.icon_manager.get_icon("x-square", size=14))
        close_button.setFixedSize(40, 35)
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(self.reject)
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
        title_layout.addWidget(close_button)
        
        title_bar.mousePressEvent = self.title_bar_mouse_press
        
        return title_bar
    
    def title_bar_mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.windowHandle().startSystemMove()
        
    def create_branch(self):
        branch_name = self.branch_name_input.text().strip()
        
        if not branch_name:
            QMessageBox.warning(self, "Error", "Debes ingresar un nombre para la rama")
            return
            
        from_commit = None
        if self.from_commit_radio.isChecked():
            from_commit = self.commit_input.text().strip()
            if not from_commit:
                QMessageBox.warning(self, "Error", "Debes ingresar un hash de commit")
                return
                
        success, message = self.git_manager.create_branch(branch_name, from_commit)
        
        if success:
            QMessageBox.information(self, "Éxito", f"Rama '{branch_name}' creada correctamente")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", f"No se pudo crear la rama:\n{message}")
            
    def apply_styles(self):
        from ui.theme import get_current_theme
        theme = get_current_theme()
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme.colors['background']};
            }}
            QLabel {{
                color: {theme.colors['text']};
            }}
            QLineEdit {{
                background-color: {theme.colors['input_bg']};
                color: {theme.colors['text']};
                border: 2px solid {theme.colors['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 2px solid {theme.colors['border_focus']};
            }}
            QLineEdit:disabled {{
                background-color: {theme.colors['surface']};
                color: {theme.colors['text_disabled']};
            }}
            QGroupBox {{
                color: {theme.colors['text']};
                border: 2px solid {theme.colors['border']};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QRadioButton {{
                color: {theme.colors['text']};
                font-size: 13px;
            }}
            QRadioButton::indicator {{
                width: 15px;
                height: 15px;
            }}
            QPushButton {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['text_inverse']};
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {theme.colors['primary_pressed']};
            }}
        """)

class CommitActionsDialog(QDialog):
    def __init__(self, git_manager, commit_hash, commit_info, parent=None):
        super().__init__(parent)
        self.git_manager = git_manager
        self.commit_hash = commit_hash
        self.commit_info = commit_info
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Acciones del Commit")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(self.icon_manager.get_pixmap("git-commit", 24))
        title_layout.addWidget(icon_label)
        
        title_text = QLabel("Acciones del Commit")
        title_text.setStyleSheet("font-size: 18px; font-weight: bold; color: palette(bright-text);")
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        info_label = QLabel(f"Commit: {self.commit_hash[:7]}")
        info_label.setStyleSheet("color: palette(link); font-size: 14px; font-weight: bold;")
        layout.addWidget(info_label)
        
        msg_label = QLabel(f"Mensaje: {self.commit_info}")
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet("color: palette(window-text); font-size: 12px; padding: 10px; background-color: palette(button); border-radius: 4px;")
        layout.addWidget(msg_label)
        
        actions_label = QLabel("Selecciona una acción:")
        actions_label.setStyleSheet("color: palette(window-text); font-weight: bold; margin-top: 10px;")
        layout.addWidget(actions_label)
        
        self.reset_soft_btn = QPushButton("  Reset Soft (mantener cambios)")
        self.reset_soft_btn.setIcon(self.icon_manager.get_icon("arrow-clockwise", size=18))
        self.reset_soft_btn.setToolTip("Volver a este commit manteniendo los cambios en el área de trabajo")
        self.reset_soft_btn.clicked.connect(lambda: self.reset_commit('soft'))
        layout.addWidget(self.reset_soft_btn)
        
        self.reset_mixed_btn = QPushButton("  Reset Mixed (descartar staging)")
        self.reset_mixed_btn.setIcon(self.icon_manager.get_icon("arrow-clockwise", size=18))
        self.reset_mixed_btn.setToolTip("Volver a este commit, descartar staging pero mantener archivos")
        self.reset_mixed_btn.clicked.connect(lambda: self.reset_commit('mixed'))
        layout.addWidget(self.reset_mixed_btn)
        
        self.reset_hard_btn = QPushButton("  Reset Hard (descartar todo)")
        self.reset_hard_btn.setIcon(self.icon_manager.get_icon("warning", size=18))
        self.reset_hard_btn.setToolTip("Volver a este commit descartando TODOS los cambios")
        self.reset_hard_btn.setStyleSheet("""
            QPushButton {
                background-color: palette(highlight);
                color: palette(bright-text);
            }
            QPushButton:hover {
                background-color: palette(highlight);
            }
        """)
        self.reset_hard_btn.clicked.connect(lambda: self.reset_commit('hard'))
        layout.addWidget(self.reset_hard_btn)
        
        self.checkout_btn = QPushButton("  Ver este commit (detached HEAD)")
        self.checkout_btn.setIcon(self.icon_manager.get_icon("sign-in", size=18))
        self.checkout_btn.setToolTip("Ver el repositorio como estaba en este commit")
        self.checkout_btn.clicked.connect(self.checkout_commit)
        layout.addWidget(self.checkout_btn)
        
        self.create_branch_btn = QPushButton("  Crear rama desde aquí")
        self.create_branch_btn.setIcon(self.icon_manager.get_icon("git-branch", size=18))
        self.create_branch_btn.setToolTip("Crear una nueva rama a partir de este commit")
        self.create_branch_btn.clicked.connect(self.create_branch_from_commit)
        layout.addWidget(self.create_branch_btn)
        
        layout.addStretch()
        
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)
        
        self.apply_styles()
        
    def reset_commit(self, mode):
        mode_names = {
            'soft': 'Soft (mantener cambios)',
            'mixed': 'Mixed (descartar staging)',
            'hard': 'Hard (descartar todo)'
        }
        
        reply = QMessageBox.question(
            self,
            "Confirmar Reset",
            f"¿Hacer reset {mode_names[mode]} al commit {self.commit_hash[:7]}?\n\n" +
            ("ADVERTENCIA: Perderás todos los cambios no guardados!" if mode == 'hard' else ""),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.git_manager.reset_to_commit(self.commit_hash, mode)
            if success:
                QMessageBox.information(self, "Éxito", f"Reset {mode} completado")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", f"Error en reset:\n{message}")
                
    def checkout_commit(self):
        reply = QMessageBox.question(
            self,
            "Confirmar Checkout",
            f"¿Ver el commit {self.commit_hash[:7]}?\n\n" +
            "Estarás en modo 'detached HEAD'. Para guardar cambios, crea una nueva rama.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.git_manager.checkout_commit(self.commit_hash)
            if success:
                QMessageBox.information(self, "Éxito", f"Ahora estás en el commit {self.commit_hash[:7]}")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", f"Error:\n{message}")
                
    def create_branch_from_commit(self):
        branch_name, ok = QLineEdit().getText(
            self,
            "Crear Rama",
            "Nombre de la nueva rama:",
            QLineEdit.EchoMode.Normal
        )
        
        if ok and branch_name:
            success, message = self.git_manager.create_branch(branch_name, self.commit_hash)
            if success:
                QMessageBox.information(self, "Éxito", f"Rama '{branch_name}' creada desde el commit {self.commit_hash[:7]}")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", f"Error:\n{message}")
                
    def apply_styles(self):
        from ui.theme import get_current_theme
        theme = get_current_theme()
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme.colors['background']};
            }}
            QLabel {{
                color: {theme.colors['text']};
            }}
            QPushButton {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['text_inverse']};
                border: none;
                border-radius: 4px;
                padding: 12px 15px;
                font-weight: bold;
                font-size: 13px;
                text-align: left;
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {theme.colors['primary_pressed']};
            }}
        """)

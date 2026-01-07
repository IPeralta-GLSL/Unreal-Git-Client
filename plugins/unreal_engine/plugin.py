import os
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from core.plugin_interface import PluginInterface

class Plugin(PluginInterface):
    def get_name(self):
        return "Unreal Engine"
    
    def get_version(self):
        return "1.0.0"
    
    def get_description(self):
        return "Integración con Unreal Engine: detecta proyectos, muestra indicadores y proporciona acciones específicas"
    
    def get_icon(self):
        return "ui/Icons/unreal-engine-svgrepo-com.svg"
    
    def is_unreal_project(self, repo_path):
        if not repo_path or not os.path.exists(repo_path):
            return False
        
        for item in os.listdir(repo_path):
            if item.endswith('.uproject'):
                return True
        return False
    
    def get_uproject_file(self, repo_path):
        if not repo_path or not os.path.exists(repo_path):
            return None
        
        for item in os.listdir(repo_path):
            if item.endswith('.uproject'):
                return os.path.join(repo_path, item)
        return None
    
    def get_repository_indicator(self, repo_path):
        if self.is_unreal_project(repo_path):
            uproject = self.get_uproject_file(repo_path)
            project_name = os.path.basename(uproject).replace('.uproject', '') if uproject else 'Unreal'
            
            return {
                'icon': '',
                'text': project_name,
                'tooltip': f'Proyecto de Unreal Engine detectado\n{project_name}',
                'plugin_name': 'unreal_engine'
            }
        return None
    
    def get_actions(self, context='repository'):
        if context != 'repository':
            return []
        
        return [
            {
                'id': 'open_uproject',
                'name': 'Abrir en Unreal Engine',
                'icon': 'unreal-engine-svgrepo-com',
                'callback': self.open_in_unreal,
                'requires_unreal': True
            },
            {
                'id': 'configure_lfs',
                'name': 'Configurar LFS para Unreal',
                'icon': 'file-code',
                'callback': self.track_unreal_files,
                'requires_unreal': True
            },
            {
                'id': 'open_project_folder',
                'name': 'Abrir carpeta del proyecto',
                'icon': 'folder-open',
                'callback': self.open_project_folder,
                'requires_unreal': True
            },
            {
                'id': 'show_engine_info',
                'name': 'Información del Engine',
                'icon': 'info',
                'callback': self.show_engine_info,
                'requires_unreal': True
            }
        ]
    
    def open_in_unreal(self, repo_path):
        uproject = self.get_uproject_file(repo_path)
        if not uproject:
            return False, "No se encontró archivo .uproject"
        
        try:
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                os.startfile(uproject)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', uproject])
            else:
                subprocess.run(['xdg-open', uproject])
            
            return True, f"Abriendo proyecto: {os.path.basename(uproject)}"
        except Exception as e:
            return False, f"Error al abrir proyecto: {str(e)}"
    
    def open_project_folder(self, repo_path):
        try:
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                os.startfile(repo_path)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', repo_path])
            else:
                subprocess.run(['xdg-open', repo_path])
            
            return True, "Carpeta abierta"
        except Exception as e:
            return False, f"Error al abrir carpeta: {str(e)}"
    
    def show_engine_info(self, repo_path):
        uproject = self.get_uproject_file(repo_path)
        if not uproject:
            return False, "No se encontró archivo .uproject"
        
        try:
            import json
            with open(uproject, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            dialog = EngineInfoDialog(data)
            result = dialog.exec()

            if result == QDialog.DialogCode.Accepted:
                updated = dialog.get_data()
                with open(uproject, 'w', encoding='utf-8') as f:
                    json.dump(updated, f, ensure_ascii=False, indent=4)
                return True, "Información del Engine actualizada"
            else:
                return True, "Sin cambios"
        except Exception as e:
            return False, f"Error al leer información: {str(e)}"
    
    def track_unreal_files(self, repo_path):
        if not self.is_unreal_project(repo_path):
            return False, "No es un proyecto de Unreal Engine"
        
        try:
            import subprocess
            
            unreal_extensions = self.get_lfs_patterns()
            
            gitattributes_path = os.path.join(repo_path, ".gitattributes")
            
            with open(gitattributes_path, 'a') as f:
                f.write("\n# Unreal Engine LFS Configuration\n")
                for ext in unreal_extensions:
                    f.write(f"{ext} filter=lfs diff=lfs merge=lfs -text\n")
            
            subprocess.run(['git', 'add', '.gitattributes'], cwd=repo_path, check=True)
            
            return True, f"Configurados {len(unreal_extensions)} tipos de archivos para LFS"
        except Exception as e:
            return False, f"Error al configurar LFS: {str(e)}"
    
    def get_lfs_patterns(self):
        return [
            "*.uasset", "*.umap", "*.ubulk", "*.upk",
            "*.uproject", "*.uplugin", "*.blend", "*.blend1",
            "*.fbx", "*.3ds", "*.obj", "*.dae",
            "*.jpg", "*.jpeg", "*.png", "*.tga", "*.bmp",
            "*.tif", "*.gif", "*.iff", "*.pict", "*.dds",
            "*.xcf", "*.exr", "*.wav", "*.mp3", "*.ogg",
            "*.flac", "*.aiff", "*.aif", "*.mod", "*.it",
            "*.s3m", "*.xm", "*.psd", "*.mov", "*.avi",
            "*.mp4", "*.wmv"
        ]


class EngineInfoDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Información del Engine")
        self.data = data
        self.plugins = data.get('Plugins', [])
        self.plugin_rows = []

        layout = QVBoxLayout(self)

        version_label = QLabel("Versión del Engine")
        self.version_input = QLineEdit(str(data.get('EngineAssociation', '')))
        version_row = QHBoxLayout()
        version_row.addWidget(version_label)
        version_row.addWidget(self.version_input)
        layout.addLayout(version_row)

        buttons_row = QHBoxLayout()
        activate_all = QPushButton("Activar todos")
        deactivate_all = QPushButton("Desactivar todos")
        activate_all.clicked.connect(lambda: self.toggle_all(True))
        deactivate_all.clicked.connect(lambda: self.toggle_all(False))
        buttons_row.addWidget(activate_all)
        buttons_row.addWidget(deactivate_all)
        buttons_row.addStretch(1)
        layout.addLayout(buttons_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)

        if self.plugins:
            for plugin in self.plugins:
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                name = plugin.get('Name', 'Desconocido')
                checkbox = QCheckBox(name)
                checkbox.setChecked(bool(plugin.get('Enabled', False)))
                row_layout.addWidget(checkbox)
                row_layout.addStretch(1)
                content_layout.addWidget(row_widget)
                self.plugin_rows.append((plugin, checkbox))
        else:
            empty_label = QLabel("No se encontraron plugins en el .uproject")
            content_layout.addWidget(empty_label)

        content_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll)

        actions_row = QHBoxLayout()
        actions_row.addStretch(1)
        save_btn = QPushButton("Guardar")
        cancel_btn = QPushButton("Cancelar")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        actions_row.addWidget(cancel_btn)
        actions_row.addWidget(save_btn)
        layout.addLayout(actions_row)

    def toggle_all(self, value):
        for _, checkbox in self.plugin_rows:
            checkbox.setChecked(value)

    def get_data(self):
        self.data['EngineAssociation'] = self.version_input.text().strip()
        for plugin, checkbox in self.plugin_rows:
            plugin['Enabled'] = checkbox.isChecked()
        return self.data

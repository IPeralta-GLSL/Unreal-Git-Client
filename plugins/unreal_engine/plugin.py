import os
from pathlib import Path

class Plugin:
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
                'icon': '🎮',
                'text': f'Unreal Engine: {project_name}',
                'tooltip': f'Proyecto de Unreal Engine detectado\n{project_name}',
                'color': '#0E1128',
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
                'icon': '🎮',
                'callback': self.open_in_unreal,
                'requires_unreal': True
            },
            {
                'id': 'configure_lfs',
                'name': 'Configurar LFS para Unreal',
                'icon': '📦',
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
            
            engine_version = data.get('EngineAssociation', 'Desconocida')
            plugins = data.get('Plugins', [])
            
            info = f"Versión del Engine: {engine_version}\n"
            info += f"Plugins: {len(plugins)}\n\n"
            
            if plugins:
                info += "Plugins instalados:\n"
                for plugin in plugins[:10]:
                    name = plugin.get('Name', 'Unknown')
                    enabled = plugin.get('Enabled', False)
                    status = '✓' if enabled else '✗'
                    info += f"  {status} {name}\n"
            
            return True, info
        except Exception as e:
            return False, f"Error al leer información: {str(e)}"
    
    def track_unreal_files(self, repo_path):
        if not self.is_unreal_project(repo_path):
            return False, "No es un proyecto de Unreal Engine"
        
        try:
            import subprocess
            
            unreal_extensions = [
                "*.uasset", "*.umap", "*.blend", "*.blend1",
                "*.fbx", "*.3ds", "*.obj", "*.dae",
                "*.jpg", "*.jpeg", "*.png", "*.tga", "*.bmp",
                "*.tif", "*.gif", "*.iff", "*.pict", "*.dds",
                "*.xcf", "*.exr", "*.wav", "*.mp3", "*.ogg",
                "*.flac", "*.aiff", "*.aif", "*.mod", "*.it",
                "*.s3m", "*.xm", "*.psd", "*.mov", "*.avi",
                "*.mp4", "*.wmv"
            ]
            
            gitattributes_path = os.path.join(repo_path, ".gitattributes")
            
            with open(gitattributes_path, 'a') as f:
                f.write("\n# Unreal Engine LFS Configuration\n")
                for ext in unreal_extensions:
                    f.write(f"{ext} filter=lfs diff=lfs merge=lfs -text\n")
            
            subprocess.run(['git', 'add', '.gitattributes'], cwd=repo_path, check=True)
            
            return True, f"Configurados {len(unreal_extensions)} tipos de archivos para LFS"
        except Exception as e:
            return False, f"Error al configurar LFS: {str(e)}"

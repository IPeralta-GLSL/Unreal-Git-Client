from core.plugin_interface import PluginInterface
import os

class Plugin(PluginInterface):
    def get_name(self):
        return "Hello World"
    
    def get_version(self):
        return "1.0.0"
    
    def get_description(self):
        return "Un plugin de ejemplo para demostrar la modularidad"
    
    def get_icon(self):
        return "ui/Icons/info.svg" # Usamos un icono existente
    
    def get_repository_indicator(self, repo_path):
        # Este plugin siempre muestra un indicador para propósitos de demostración
        # En un caso real, verificarías si existe un archivo específico, etc.
        return {
            'icon': '👋',
            'text': 'Hello World',
            'tooltip': 'Plugin de ejemplo activo',
            'color': '#6366f1', # Un color índigo
            'plugin_name': 'hello_world'
        }
    
    def get_actions(self, context):
        if context == 'repository':
            return [
                {
                    'id': 'say_hello',
                    'name': 'Saludar',
                    'icon': 'chat',
                    'callback': self.say_hello
                }
            ]
        return []
    
    def say_hello(self, repo_path):
        return True, f"¡Hola desde el repositorio en: {os.path.basename(repo_path)}!"

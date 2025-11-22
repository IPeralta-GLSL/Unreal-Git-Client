from core.plugin_interface import PluginInterface
import os

class Plugin(PluginInterface):
    def get_name(self):
        return "Example Plugin"
    
    def get_version(self):
        return "1.0.0"
    
    def get_description(self):
        return "An example plugin to demonstrate modularity"
    
    def is_enabled_by_default(self):
        return False

    def get_icon(self):
        return "ui/Icons/info.svg" # Using an existing icon
    
    def get_repository_indicator(self, repo_path):
        # This plugin always shows an indicator for demonstration purposes
        # In a real scenario, you would check if a specific file exists, etc.
        return {
            'icon': '👋',
            'text': 'Example',
            'tooltip': 'Example plugin active',
            'color': '#6366f1', # Indigo color
            'plugin_name': 'example'
        }
    
    def get_actions(self, context):
        if context == 'repository':
            return [
                {
                    'id': 'say_hello',
                    'name': 'Say Hello',
                    'icon': 'chat',
                    'callback': self.say_hello
                }
            ]
        return []
    
    def say_hello(self, repo_path):
        return True, f"Hello from the repository at: {os.path.basename(repo_path)}!"

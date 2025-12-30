from core.plugin_interface import PluginInterface
import os
import sys
import importlib.util

# Manually load chat_dialog module to avoid relative import issues with plugin loader
current_dir = os.path.dirname(os.path.abspath(__file__))
chat_dialog_path = os.path.join(current_dir, "chat_dialog.py")

spec = importlib.util.spec_from_file_location("ai_assistant_chat_dialog", chat_dialog_path)
chat_dialog_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chat_dialog_module)
ChatWidget = chat_dialog_module.ChatWidget

class Plugin(PluginInterface):
    def __init__(self):
        self.chat_widget = None

    def get_name(self):
        return "AI Assistant"
    
    def get_version(self):
        return "0.2.0"
    
    def get_description(self):
        return "Local AI Chat Assistant using TinyLlama"
    
    def get_icon(self):
        return "ui/Icons/lightbulb.svg" 
    
    def is_enabled_by_default(self):
        return True
    
    def get_repository_indicator(self, repo_path):
        return None
    
    def get_actions(self, context):
        return []
    
    def get_sidebar_widget(self, repo_path):
        if not self.chat_widget:
            self.chat_widget = ChatWidget(repo_path)
            return self.chat_widget

        if repo_path and getattr(self.chat_widget, 'repo_path', None) != repo_path:
            try:
                self.chat_widget.set_repo_path(repo_path)
            except Exception:
                pass

        return self.chat_widget

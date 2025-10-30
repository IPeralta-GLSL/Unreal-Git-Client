import json
import os
from pathlib import Path

class ThemeManager:
    def __init__(self):
        self.config_dir = Path.home() / ".unreal-git-client"
        self.config_file = self.config_dir / "theme_config.json"
        self.current_theme_name = "Dark"
        self.load_config()
    
    def load_config(self):
        """Carga la configuración del tema"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.current_theme_name = config.get('theme', 'Dark')
            except Exception as e:
                print(f"Error cargando configuración del tema: {e}")
                self.current_theme_name = "Dark"
    
    def save_config(self):
        """Guarda la configuración del tema"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump({'theme': self.current_theme_name}, f, indent=2)
        except Exception as e:
            print(f"Error guardando configuración del tema: {e}")
    
    def set_theme(self, theme_name):
        """Cambia el tema actual"""
        self.current_theme_name = theme_name
        self.save_config()
    
    def get_theme_name(self):
        """Obtiene el nombre del tema actual"""
        return self.current_theme_name
    
    @staticmethod
    def get_available_themes():
        """Obtiene la lista de temas disponibles"""
        return ["Dark", "Light"]

theme_manager = ThemeManager()

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple

class PluginInterface(ABC):
    """
    Interfaz base para todos los plugins.
    Define los métodos que deben implementar los plugins para integrarse con la aplicación.
    """
    
    @abstractmethod
    def get_name(self) -> str:
        """Devuelve el nombre del plugin."""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Devuelve la versión del plugin."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Devuelve una descripción corta del plugin."""
        pass
    
    @abstractmethod
    def get_icon(self) -> str:
        """Devuelve la ruta al icono del plugin."""
        pass
    
    def get_repository_indicator(self, repo_path: str) -> Optional[Dict[str, Any]]:
        """
        Devuelve un indicador para mostrar en la barra superior si el repositorio es relevante para este plugin.
        Debe devolver un diccionario con keys: 'icon', 'text', 'tooltip', 'color', 'plugin_name'.
        O None si no aplica.
        """
        return None
    
    def get_actions(self, context: str) -> List[Dict[str, Any]]:
        """
        Devuelve una lista de acciones disponibles para el contexto dado.
        Contextos: 'repository', 'file_list', 'commit_history', etc.
        Cada acción es un dict con: 'id', 'name', 'icon', 'callback'.
        """
        return []
    
    def get_lfs_patterns(self) -> List[str]:
        """
        Devuelve una lista de patrones de archivo sugeridos para Git LFS.
        """
        return []

    def is_enabled_by_default(self) -> bool:
        """
        Devuelve True si el plugin debe estar activado por defecto.
        """
        return True

    def is_enabled_by_default(self) -> bool:
        """
        Devuelve True si el plugin debe estar activado por defecto.
        """
        return True

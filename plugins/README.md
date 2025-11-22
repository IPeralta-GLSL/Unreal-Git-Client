# Sistema de Plugins

Este cliente Git soporta un sistema de plugins modular basado en Python.
Cada plugin debe residir en su propia carpeta dentro del directorio `plugins/`.

## Estructura de un Plugin

```
plugins/
  mi_plugin/
    __init__.py  (opcional)
    plugin.py    (requerido)
```

## Implementación

El archivo `plugin.py` debe contener una clase llamada `Plugin` que herede de `core.plugin_interface.PluginInterface`.

### Ejemplo Básico

```python
from core.plugin_interface import PluginInterface

class Plugin(PluginInterface):
    def get_name(self):
        return "Mi Plugin"
    
    def get_version(self):
        return "1.0.0"
    
    def get_description(self):
        return "Descripción de mi plugin"
    
    def get_icon(self):
        # Ruta a un icono o nombre de icono del sistema
        return "ui/Icons/mi_icono.svg" 
    
    def get_repository_indicator(self, repo_path):
        # Lógica para detectar si este plugin es relevante para el repo
        if es_mi_tipo_de_proyecto(repo_path):
            return {
                'icon': '🚀',
                'text': 'Mi Proyecto',
                'tooltip': 'Proyecto detectado',
                'color': '#123456',
                'plugin_name': 'mi_plugin'
            }
        return None
        
    def get_actions(self, context):
        if context == 'repository':
            return [
                {
                    'id': 'mi_accion',
                    'name': 'Ejecutar Acción',
                    'icon': 'play',
                    'callback': self.mi_funcion
                }
            ]
        return []

    def mi_funcion(self, repo_path):
        print(f"Ejecutando acción en {repo_path}")
        return True, "Acción completada"
```

## Capacidades

Los plugins pueden:
1.  **Detectar tipos de proyectos**: Mostrar indicadores en la barra superior (ej: Unreal, Unity, Web).
2.  **Agregar acciones**: Añadir botones al menú de acciones del repositorio.
3.  **Configurar LFS**: Sugerir patrones de archivos para Git LFS (`get_lfs_patterns`).

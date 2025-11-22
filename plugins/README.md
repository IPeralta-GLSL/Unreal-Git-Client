# Plugin System

This Git client supports a modular plugin system based on Python.
Each plugin must reside in its own folder within the `plugins/` directory.

## Plugin Structure

```
plugins/
  my_plugin/
    __init__.py  (optional)
    plugin.py    (required)
```

## Implementation

The `plugin.py` file must contain a class named `Plugin` that inherits from `core.plugin_interface.PluginInterface`.

### Basic Example

```python
from core.plugin_interface import PluginInterface

class Plugin(PluginInterface):
    def get_name(self):
        return "My Plugin"
    
    def get_version(self):
        return "1.0.0"
    
    def get_description(self):
        return "Description of my plugin"
    
    def get_icon(self):
        # Path to an icon or system icon name
        return "ui/Icons/my_icon.svg" 
    
    def get_repository_indicator(self, repo_path):
        # Logic to detect if this plugin is relevant for the repo
        if is_my_project_type(repo_path):
            return {
                'icon': '🚀',
                'text': 'My Project',
                'tooltip': 'Project detected',
                'color': '#123456',
                'plugin_name': 'my_plugin'
            }
        return None
        
    def get_actions(self, context):
        if context == 'repository':
            return [
                {
                    'id': 'my_action',
                    'name': 'Execute Action',
                    'icon': 'play',
                    'callback': self.my_function
                }
            ]
        return []

    def my_function(self, repo_path):
        print(f"Executing action in {repo_path}")
        return True, "Action completed"
```

## Capabilities

Plugins can:
1.  **Detect project types**: Show indicators in the top bar (e.g., Unreal, Unity, Web).
2.  **Add actions**: Add buttons to the repository action menu.
3.  **Configure LFS**: Suggest file patterns for Git LFS (`get_lfs_patterns`).

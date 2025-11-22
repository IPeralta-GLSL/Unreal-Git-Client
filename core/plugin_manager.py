import os
import sys
import importlib.util
from pathlib import Path

class PluginManager:
    def __init__(self):
        self.plugins = {}
        self.plugins_dir = Path(__file__).parent.parent / "plugins"
        self.load_plugins()
    
    def load_plugins(self):
        if not self.plugins_dir.exists():
            return
        
        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir() or plugin_dir.name.startswith('_'):
                continue
            
            plugin_file = plugin_dir / "plugin.py"
            if not plugin_file.exists():
                continue
            
            try:
                spec = importlib.util.spec_from_file_location(
                    f"plugins.{plugin_dir.name}",
                    plugin_file
                )
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
                
                if hasattr(module, 'Plugin'):
                    plugin_instance = module.Plugin()
                    
                    # Check if plugin should be enabled by default
                    enabled_by_default = True
                    if hasattr(plugin_instance, 'is_enabled_by_default'):
                        enabled_by_default = plugin_instance.is_enabled_by_default()
                        
                    self.plugins[plugin_dir.name] = {
                        'instance': plugin_instance,
                        'module': module,
                        'enabled': enabled_by_default
                    }
                    status = "cargado" if enabled_by_default else "cargado (desactivado)"
                    print(f"✓ Plugin {status}: {plugin_instance.get_name()}")
            except Exception as e:
                print(f"✗ Error cargando plugin {plugin_dir.name}: {str(e)}")
    
    def get_plugin(self, name):
        plugin_data = self.plugins.get(name)
        if plugin_data and plugin_data['enabled']:
            return plugin_data['instance']
        return None
    
    def get_all_plugins(self):
        return {name: data['instance'] for name, data in self.plugins.items() if data['enabled']}
    
    def get_plugins(self):
        plugins_info = []
        for name, data in self.plugins.items():
            plugin = data['instance']
            plugins_info.append({
                'name': name,
                'display_name': plugin.get_name() if hasattr(plugin, 'get_name') else name,
                'description': plugin.get_description() if hasattr(plugin, 'get_description') else '',
                'version': plugin.get_version() if hasattr(plugin, 'get_version') else '1.0.0',
                'enabled': data['enabled']
            })
        return plugins_info
    
    def is_plugin_enabled(self, name):
        if name in self.plugins:
            return self.plugins[name]['enabled']
        return False
    
    def enable_plugin(self, name):
        if name in self.plugins:
            self.plugins[name]['enabled'] = True
    
    def disable_plugin(self, name):
        if name in self.plugins:
            self.plugins[name]['enabled'] = False
    
    def get_plugin_actions(self, context='repository'):
        actions = []
        for name, data in self.plugins.items():
            if data['enabled']:
                plugin = data['instance']
                if hasattr(plugin, 'get_actions'):
                    plugin_actions = plugin.get_actions(context)
                    if plugin_actions:
                        # Inject plugin name into actions for filtering
                        for action in plugin_actions:
                            action['plugin_name'] = name
                        actions.extend(plugin_actions)
        return actions
    
    def get_all_lfs_patterns(self):
        patterns = []
        for name, data in self.plugins.items():
            if data['enabled']:
                plugin = data['instance']
                if hasattr(plugin, 'get_lfs_patterns'):
                    plugin_patterns = plugin.get_lfs_patterns()
                    if plugin_patterns:
                        patterns.extend(plugin_patterns)
        return list(set(patterns))
    
    def get_repository_indicators(self, repo_path):
        indicators = []
        for name, data in self.plugins.items():
            if data['enabled']:
                plugin = data['instance']
                if hasattr(plugin, 'get_repository_indicator'):
                    indicator = plugin.get_repository_indicator(repo_path)
                    if indicator:
                        indicators.append(indicator)
        return indicators

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow
from ui.theme import Theme
from ui.theme_manager import theme_manager
from core.plugin_manager import PluginManager
from core.settings_manager import SettingsManager
from core.translations import set_language

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Git Client")
    app.setOrganizationName("GitClient")
    
    settings_manager = SettingsManager()
    saved_language = settings_manager.get_language()
    set_language(saved_language)
    
    theme = Theme(theme_manager.get_theme_name())
    theme.apply_to_app(app)
    
    plugin_manager = PluginManager()
    
    window = MainWindow(plugin_manager=plugin_manager)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

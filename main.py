import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow
from ui.theme import Theme
from ui.theme_manager import theme_manager
from core.plugin_manager import PluginManager

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Git Client")
    app.setOrganizationName("GitClient")
    
    # Aplicar tema universal basado en la configuración guardada
    theme = Theme(theme_manager.get_theme_name())
    theme.apply_to_app(app)
    
    plugin_manager = PluginManager()
    
    window = MainWindow(plugin_manager=plugin_manager)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

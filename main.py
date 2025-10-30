import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow
from core.plugin_manager import PluginManager

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Git Client")
    app.setOrganizationName("GitClient")
    
    plugin_manager = PluginManager()
    
    window = MainWindow(plugin_manager=plugin_manager)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

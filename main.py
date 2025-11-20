import sys
import traceback
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow
from ui.theme import Theme
from ui.theme_manager import theme_manager
from core.plugin_manager import PluginManager
from core.settings_manager import SettingsManager
from core.translations import set_language

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('git_client_debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    try:
        print("Starting application...")
        app = QApplication(sys.argv)
        print("QApplication created successfully")
        
        app.setApplicationName("Git Client")
        app.setOrganizationName("GitClient")
        
        print("Loading settings...")
        settings_manager = SettingsManager()
        saved_language = settings_manager.get_language()
        set_language(saved_language)
        print(f"Language set to: {saved_language}")
        
        print("Applying theme...")
        theme = Theme(theme_manager.get_theme_name())
        theme.apply_to_app(app)
        print("Theme applied successfully")
        
        print("Loading plugins...")
        plugin_manager = PluginManager()
        print("Plugins loaded successfully")
        
        print("Creating main window...")
        window = MainWindow(plugin_manager=plugin_manager)
        print("Main window created successfully")
        
        print("Showing window...")
        sys.stdout.flush()
        window.show()
        print("Window shown successfully")
        sys.stdout.flush()
        
        print("Starting event loop...")
        sys.stdout.flush()
        sys.exit(app.exec())
    except SystemExit:
        pass
    except Exception as e:
        print("\n" + "="*60)
        print(f"FATAL ERROR: {e}")
        print("="*60)
        traceback.print_exc()
        print("="*60)
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()

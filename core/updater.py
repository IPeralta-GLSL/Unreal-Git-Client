import requests
import platform
import logging
import webbrowser
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from core.version import CURRENT_VERSION

logger = logging.getLogger(__name__)

class UpdateChecker(QThread):
    update_available = pyqtSignal(str, str, str) # version, url, release_notes
    error_occurred = pyqtSignal(str)
    no_update = pyqtSignal()

    def run(self):
        try:
            logger.info("Checking for updates...")
            response = requests.get(
                "https://api.github.com/repos/IPeralta-GLSL/Unreal-Git-Client/releases/latest",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            latest_version = data["tag_name"]
            logger.info(f"Latest version: {latest_version}, Current version: {CURRENT_VERSION}")
            
            if self.is_newer(latest_version, CURRENT_VERSION):
                download_url = self.get_download_url(data)
                release_notes = data["body"]
                self.update_available.emit(latest_version, download_url, release_notes)
            else:
                self.no_update.emit()
                
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            self.error_occurred.emit(str(e))

    def is_newer(self, latest, current):
        try:
            l = latest.lstrip('v').split('.')
            c = current.lstrip('v').split('.')
            
            # Pad with zeros if lengths differ
            while len(l) < 3: l.append('0')
            while len(c) < 3: c.append('0')
            
            for i in range(3):
                if int(l[i]) > int(c[i]):
                    return True
                elif int(l[i]) < int(c[i]):
                    return False
            return False
        except Exception as e:
            logger.error(f"Error comparing versions: {e}")
            return False

    def get_download_url(self, data):
        system = platform.system().lower()
        assets = data.get("assets", [])
        
        for asset in assets:
            name = asset["name"].lower()
            if system == "windows" and ".exe" in name:
                return asset["browser_download_url"]
            
        return data["html_url"]

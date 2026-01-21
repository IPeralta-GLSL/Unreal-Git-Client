import requests
import platform
import logging
import webbrowser
import os
import sys
import subprocess
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from core.version import CURRENT_VERSION

logger = logging.getLogger(__name__)

class UpdateDownloader(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, dest_path):
        super().__init__()
        self.url = url
        self.dest_path = dest_path

    def run(self):
        try:
            response = requests.get(self.url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0
            
            with open(self.dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            self.progress.emit(percent)
                            
            self.finished.emit(self.dest_path)
        except Exception as e:
            self.error.emit(str(e))

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

def install_update(file_path):
    if platform.system() != "Windows":
        return False, "Auto-update only supported on Windows"
    
    if not getattr(sys, 'frozen', False):
        return False, "Cannot auto-update when running from source"
    
    if not os.path.isfile(file_path):
        return False, "Update file not found"
        
    try:
        current_exe = sys.executable
        
        file_path_safe = file_path.replace('"', '')
        current_exe_safe = current_exe.replace('"', '')
        
        if not os.path.isabs(file_path_safe) or not os.path.isabs(current_exe_safe):
            return False, "Invalid file paths"
        
        batch_script = f'''@echo off
:loop
move /y "{file_path_safe}" "{current_exe_safe}" > nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto loop
)
timeout /t 3 /nobreak >nul
start "" "{current_exe_safe}"
del "%~f0"
'''
        batch_file = "update_installer.bat"
        with open(batch_file, "w") as f:
            f.write(batch_script)
            
        subprocess.Popen([batch_file], shell=True)
        return True, "Update started"
    except Exception as e:
        return False, str(e)

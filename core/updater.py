import requests
import platform
import logging
import webbrowser
import os
import sys
import subprocess
import tempfile
import time
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
        current_dir = os.path.dirname(current_exe)
        
        # Normalize paths
        file_path = os.path.normpath(os.path.abspath(file_path))
        current_exe = os.path.normpath(os.path.abspath(current_exe))
        
        if not os.path.isabs(file_path) or not os.path.isabs(current_exe):
            return False, "Invalid file paths"
        
        # Create a more robust PowerShell script for the update
        ps_script = f'''
$ErrorActionPreference = "Stop"
$newExe = "{file_path}"
$targetExe = "{current_exe}"
$maxRetries = 30
$retryCount = 0

Write-Host "Waiting for application to close..."

# Wait for the process to exit
while ($retryCount -lt $maxRetries) {{
    $processes = Get-Process | Where-Object {{ $_.Path -eq $targetExe }} -ErrorAction SilentlyContinue
    if (-not $processes) {{
        break
    }}
    Start-Sleep -Seconds 1
    $retryCount++
}}

if ($retryCount -ge $maxRetries) {{
    Write-Host "Timeout waiting for app to close. Forcing..."
    Get-Process | Where-Object {{ $_.Path -eq $targetExe }} | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}}

Write-Host "Replacing executable..."

# Try to replace the file
$replaceRetries = 0
$replaced = $false
while ($replaceRetries -lt 10 -and -not $replaced) {{
    try {{
        Copy-Item -Path $newExe -Destination $targetExe -Force
        $replaced = $true
        Write-Host "File replaced successfully"
    }} catch {{
        Write-Host "Retry $replaceRetries..."
        Start-Sleep -Seconds 1
        $replaceRetries++
    }}
}}

if (-not $replaced) {{
    Write-Host "Failed to replace file"
    Read-Host "Press Enter to exit"
    exit 1
}}

# Clean up the downloaded file
try {{
    Remove-Item -Path $newExe -Force -ErrorAction SilentlyContinue
}} catch {{}}

Write-Host "Starting updated application..."
Start-Sleep -Seconds 1

# Start the new version
Start-Process -FilePath $targetExe

Write-Host "Update complete!"
Start-Sleep -Seconds 2
'''
        
        # Write PowerShell script to temp file
        script_path = os.path.join(tempfile.gettempdir(), "ugc_update.ps1")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(ps_script)
        
        # Execute PowerShell script in a new window
        subprocess.Popen(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            cwd=current_dir
        )
        
        return True, "Update started"
    except Exception as e:
        logger.error(f"Error installing update: {e}")
        return False, str(e)

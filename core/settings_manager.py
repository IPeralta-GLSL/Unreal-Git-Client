import json
import os
from pathlib import Path

class SettingsManager:
    def __init__(self):
        self.config_dir = Path.home() / '.unreal-git-client'
        self.config_file = self.config_dir / 'settings.json'
        self.ensure_config_exists()
        
    def ensure_config_exists(self):
        self.config_dir.mkdir(exist_ok=True)
        if not self.config_file.exists():
            self.save_settings({'recent_repos': []})
    
    def load_settings(self):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {'recent_repos': []}
    
    def save_settings(self, settings):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def add_recent_repo(self, repo_path, repo_name=None):
        settings = self.load_settings()
        recent_repos = settings.get('recent_repos', [])
        
        if not repo_name:
            repo_name = os.path.basename(repo_path)
        
        repo_entry = {
            'path': repo_path,
            'name': repo_name,
            'last_accessed': self.get_current_timestamp()
        }
        
        recent_repos = [r for r in recent_repos if r['path'] != repo_path]
        recent_repos.insert(0, repo_entry)
        recent_repos = recent_repos[:10]
        
        settings['recent_repos'] = recent_repos
        self.save_settings(settings)
    
    def get_recent_repos(self):
        settings = self.load_settings()
        recent_repos = settings.get('recent_repos', [])
        return [r for r in recent_repos if os.path.exists(r['path'])]
    
    def remove_recent_repo(self, repo_path):
        settings = self.load_settings()
        recent_repos = settings.get('recent_repos', [])
        recent_repos = [r for r in recent_repos if r['path'] != repo_path]
        settings['recent_repos'] = recent_repos
        self.save_settings(settings)
    
    def clear_recent_repos(self):
        settings = self.load_settings()
        settings['recent_repos'] = []
        self.save_settings(settings)
    
    def get_current_timestamp(self):
        from datetime import datetime
        return datetime.now().isoformat()

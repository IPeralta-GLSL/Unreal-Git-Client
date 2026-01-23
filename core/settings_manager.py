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
            self.save_settings({'recent_repos': [], 'language': 'es'})
    
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
    
    def add_github_account(self, username, token, email=""):
        settings = self.load_settings()
        accounts = settings.get('github_accounts', [])
        
        account = {
            'username': username,
            'token': token,
            'email': email,
            'added': self.get_current_timestamp()
        }
        
        accounts = [a for a in accounts if a['username'] != username]
        accounts.append(account)
        
        settings['github_accounts'] = accounts
        self.save_settings(settings)
    
    def add_gitlab_account(self, username, token, email="", server_url="https://gitlab.com"):
        settings = self.load_settings()
        accounts = settings.get('gitlab_accounts', [])
        
        account = {
            'username': username,
            'token': token,
            'email': email,
            'server_url': server_url,
            'added': self.get_current_timestamp()
        }
        
        accounts = [a for a in accounts if not (a['username'] == username and a['server_url'] == server_url)]
        accounts.append(account)
        
        settings['gitlab_accounts'] = accounts
        self.save_settings(settings)
    
    def get_github_accounts(self):
        settings = self.load_settings()
        return settings.get('github_accounts', [])
    
    def get_gitlab_accounts(self):
        settings = self.load_settings()
        return settings.get('gitlab_accounts', [])
    
    def remove_github_account(self, username):
        settings = self.load_settings()
        accounts = settings.get('github_accounts', [])
        accounts = [a for a in accounts if a['username'] != username]
        settings['github_accounts'] = accounts
        self.save_settings(settings)
    
    def remove_gitlab_account(self, username, server_url):
        settings = self.load_settings()
        accounts = settings.get('gitlab_accounts', [])
        accounts = [a for a in accounts if not (a['username'] == username and a['server_url'] == server_url)]
        settings['gitlab_accounts'] = accounts
        self.save_settings(settings)
    
    def update_github_account(self, username, token=None, email=None):
        settings = self.load_settings()
        accounts = settings.get('github_accounts', [])
        
        for account in accounts:
            if account['username'] == username:
                if token is not None:
                    account['token'] = token
                if email is not None:
                    account['email'] = email
                account['updated'] = self.get_current_timestamp()
                break
        
        settings['github_accounts'] = accounts
        self.save_settings(settings)
    
    def update_gitlab_account(self, username, server_url, token=None, email=None):
        settings = self.load_settings()
        accounts = settings.get('gitlab_accounts', [])
        
        for account in accounts:
            if account['username'] == username and account['server_url'] == server_url:
                if token is not None:
                    account['token'] = token
                if email is not None:
                    account['email'] = email
                account['updated'] = self.get_current_timestamp()
                break
        
        settings['gitlab_accounts'] = accounts
        self.save_settings(settings)
    
    def get_language(self):
        settings = self.load_settings()
        return settings.get('language', 'es')
    
    def set_language(self, language_code):
        settings = self.load_settings()
        settings['language'] = language_code
        self.save_settings(settings)
    
    def get_clone_paths(self):
        settings = self.load_settings()
        return settings.get('clone_paths', [])
    
    def add_clone_path(self, path):
        settings = self.load_settings()
        paths = settings.get('clone_paths', [])
        if path not in paths:
            paths.append(path)
            settings['clone_paths'] = paths
            self.save_settings(settings)
            return True
        return False
    
    def remove_clone_path(self, path):
        settings = self.load_settings()
        paths = settings.get('clone_paths', [])
        if path in paths:
            paths.remove(path)
            settings['clone_paths'] = paths
            self.save_settings(settings)
    
    def get_default_clone_path(self):
        settings = self.load_settings()
        return settings.get('default_clone_path', '')
    
    def set_default_clone_path(self, path):
        settings = self.load_settings()
        settings['default_clone_path'] = path
        self.save_settings(settings)
    
    def get_create_repo_folder(self):
        settings = self.load_settings()
        return settings.get('create_repo_folder', True)
    
    def set_create_repo_folder(self, value):
        settings = self.load_settings()
        settings['create_repo_folder'] = value
        self.save_settings(settings)
    
    def get_allow_non_empty_clone(self):
        settings = self.load_settings()
        return settings.get('allow_non_empty_clone', False)
    
    def set_allow_non_empty_clone(self, value):
        settings = self.load_settings()
        settings['allow_non_empty_clone'] = value
        self.save_settings(settings)

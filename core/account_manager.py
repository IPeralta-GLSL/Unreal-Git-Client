import json
import os
import webbrowser
import secrets
import http.server
import socketserver
import threading
import requests
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

class AccountManager:
    def __init__(self):
        self.config_dir = Path.home() / '.unreal-git-client'
        self.accounts_file = self.config_dir / 'accounts.json'
        self.ensure_config_exists()
        self.oauth_server = None
        self.oauth_code = None
        self.oauth_state = None
        
        self.github_client_id = "Iv1.b507a08c87ecfe98"
        
        self.gitlab_client_id = "23c1e0b5c0b206b1db0f0d5973842d3eff3068280dc7c94ce8e5a2977d410d38"
        self.gitlab_client_secret = "gloas-396983be84a9e14e0519541446f181529aa8dcf66942760d11f5051ccdd9e959"
        
    def ensure_config_exists(self):
        self.config_dir.mkdir(exist_ok=True)
        if not self.accounts_file.exists():
            self.save_accounts({'accounts': []})
    
    def load_accounts(self):
        try:
            with open(self.accounts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {'accounts': []}
    
    def save_accounts(self, data):
        try:
            with open(self.accounts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving accounts: {e}")
    
    def get_accounts(self):
        data = self.load_accounts()
        return data.get('accounts', [])
    
    def add_account(self, platform, username, token, email=None):
        data = self.load_accounts()
        accounts = data.get('accounts', [])
        
        accounts = [a for a in accounts if not (a['platform'] == platform and a['username'] == username)]
        
        account = {
            'platform': platform,
            'username': username,
            'email': email or '',
            'token': token,
            'active': True
        }
        
        accounts.append(account)
        data['accounts'] = accounts
        self.save_accounts(data)
        
        return True
    
    def remove_account(self, platform, username):
        data = self.load_accounts()
        accounts = data.get('accounts', [])
        accounts = [a for a in accounts if not (a['platform'] == platform and a['username'] == username)]
        data['accounts'] = accounts
        self.save_accounts(data)
    
    def get_account(self, platform):
        accounts = self.get_accounts()
        for account in accounts:
            if account['platform'] == platform and account.get('active', True):
                return account
        return None
    
    def set_active_account(self, platform, username):
        data = self.load_accounts()
        accounts = data.get('accounts', [])
        
        for account in accounts:
            if account['platform'] == platform:
                account['active'] = (account['username'] == username)
        
        data['accounts'] = accounts
        self.save_accounts(data)
    
    def start_oauth_server(self, port=8888):
        self.oauth_code = None
        self.oauth_state = secrets.token_urlsafe(32)
        
        class OAuthHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, manager=None, **kwargs):
                self.manager = manager
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                parsed = urlparse(self.path)
                if parsed.path == '/callback':
                    params = parse_qs(parsed.query)
                    code = params.get('code', [None])[0]
                    state = params.get('state', [None])[0]
                    
                    if state == self.manager.oauth_state and code:
                        self.manager.oauth_code = code
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        html = '''
                        <html>
                        <head><title>Autenticación exitosa</title></head>
                        <body style="font-family: Arial; text-align: center; padding: 50px; background: #1e1e1e; color: #fff;">
                            <h1>Autenticación exitosa</h1>
                            <p>Puedes cerrar esta ventana y volver a la aplicación.</p>
                            <script>setTimeout(() => window.close(), 3000);</script>
                        </body>
                        </html>
                        '''
                        self.wfile.write(html.encode())
                    else:
                        self.send_response(400)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        html = '<html><body><h1>Error de autenticación</h1></body></html>'
                        self.wfile.write(html.encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                pass
        
        def create_handler(*args, **kwargs):
            return OAuthHandler(*args, manager=self, **kwargs)
        
        try:
            self.oauth_server = socketserver.TCPServer(("", port), create_handler)
            thread = threading.Thread(target=self.oauth_server.serve_forever, daemon=True)
            thread.start()
            return True, port
        except Exception as e:
            return False, str(e)
    
    def stop_oauth_server(self):
        if self.oauth_server:
            self.oauth_server.shutdown()
            self.oauth_server = None
    
    def get_oauth_state(self):
        return self.oauth_state
    
    def get_oauth_code(self):
        return self.oauth_code
    
    def github_oauth_url(self, client_id, redirect_uri):
        state = self.oauth_state
        scopes = "repo,user,admin:org"
        return f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope={scopes}&state={state}"
    
    def gitlab_oauth_url(self, client_id, redirect_uri, gitlab_url="https://gitlab.com"):
        state = self.oauth_state
        # GitLab usa espacios para separar scopes, no comas. Usamos + para codificar el espacio.
        scopes = "api+read_user+write_repository"
        return f"{gitlab_url}/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scopes}&state={state}"
    
    def configure_git_credentials(self, name, email):
        try:
            import subprocess
            subprocess.run(['git', 'config', '--global', 'user.name', name], check=True)
            subprocess.run(['git', 'config', '--global', 'user.email', email], check=True)
            return True
        except Exception as e:
            print(f"Error configuring git: {e}")
            return False
    
    def start_github_device_flow(self):
        try:
            print(f"Iniciando device flow con client_id: {self.github_client_id}")
            response = requests.post(
                'https://github.com/login/device/code',
                headers={'Accept': 'application/json'},
                data={
                    'client_id': self.github_client_id,
                    'scope': 'repo user'
                },
                timeout=10
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'device_code': data.get('device_code'),
                    'user_code': data.get('user_code'),
                    'verification_uri': data.get('verification_uri'),
                    'expires_in': data.get('expires_in', 900),
                    'interval': data.get('interval', 5)
                }
            else:
                print(f"Error response: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Exception starting device flow: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        return None
    
    def poll_github_device_token(self, device_code, interval=5):
        try:
            response = requests.post(
                'https://github.com/login/oauth/access_token',
                headers={'Accept': 'application/json'},
                data={
                    'client_id': self.github_client_id,
                    'device_code': device_code,
                    'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data:
                    return data['access_token']
                elif data.get('error') == 'authorization_pending':
                    return 'pending'
                elif data.get('error') == 'slow_down':
                    return 'slow_down'
                else:
                    return None
        except Exception as e:
            print(f"Error polling token: {e}")
        return None
    
    def get_github_user_info(self, token):
        try:
            response = requests.get(
                'https://api.github.com/user',
                headers={
                    'Authorization': f'token {token}',
                    'Accept': 'application/json'
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'username': data.get('login'),
                    'email': data.get('email', ''),
                    'name': data.get('name', '')
                }
        except Exception as e:
            print(f"Error getting user info: {e}")
        return None
    
    def start_gitlab_device_flow(self, gitlab_url="https://gitlab.com"):
        try:
            print(f"Iniciando GitLab device flow en: {gitlab_url}")
            
            client_id = "f89f3b90e66063fb3d9e463ccca52797f4c5bfda77dce764e798e26f877c57bd"
            
            response = requests.post(
                f'{gitlab_url}/oauth/token',
                headers={'Accept': 'application/json'},
                data={
                    'client_id': client_id,
                    'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                    'scope': 'read_user write_repository api'
                },
                timeout=10
            )
            
            print(f"GitLab response status: {response.status_code}")
            print(f"GitLab response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'device_code': data.get('device_code'),
                    'user_code': data.get('user_code'),
                    'verification_uri': data.get('verification_uri', f'{gitlab_url}/-/profile/applications'),
                    'verification_uri_complete': data.get('verification_uri_complete'),
                    'expires_in': data.get('expires_in', 900),
                    'interval': data.get('interval', 5)
                }
        except Exception as e:
            print(f"Exception starting GitLab device flow: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        return None
    
    def poll_gitlab_device_token(self, gitlab_url, device_code, interval=5):
        try:
            client_id = "f89f3b90e66063fb3d9e463ccca52797f4c5bfda77dce764e798e26f877c57bd"
            
            response = requests.post(
                f'{gitlab_url}/oauth/token',
                headers={'Accept': 'application/json'},
                data={
                    'client_id': client_id,
                    'device_code': device_code,
                    'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data:
                    return data['access_token']
                elif data.get('error') == 'authorization_pending':
                    return 'pending'
                elif data.get('error') == 'slow_down':
                    return 'slow_down'
                else:
                    return None
        except Exception as e:
            print(f"Error polling GitLab token: {e}")
        return None
    
    def get_gitlab_user_info(self, gitlab_url, token):
        try:
            response = requests.get(
                f'{gitlab_url}/api/v4/user',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Accept': 'application/json'
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'username': data.get('username'),
                    'email': data.get('email', ''),
                    'name': data.get('name', '')
                }
        except Exception as e:
            print(f"Error getting GitLab user info: {e}")
        return None

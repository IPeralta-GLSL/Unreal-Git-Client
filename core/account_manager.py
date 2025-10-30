import json
import os
import webbrowser
import secrets
import http.server
import socketserver
import threading
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
                            <h1>✅ Autenticación exitosa</h1>
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
        scopes = "api,read_user,write_repository"
        return f"{gitlab_url}/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scopes}&state={state}"
    
    def configure_git_credentials(self, platform, username, token, email=None):
        try:
            if platform == 'github':
                os.system(f'git config --global credential.helper store')
                os.system(f'git config --global user.name "{username}"')
                if email:
                    os.system(f'git config --global user.email "{email}"')
            elif platform == 'gitlab':
                os.system(f'git config --global credential.helper store')
                os.system(f'git config --global user.name "{username}"')
                if email:
                    os.system(f'git config --global user.email "{email}"')
            return True
        except Exception as e:
            print(f"Error configuring git: {e}")
            return False

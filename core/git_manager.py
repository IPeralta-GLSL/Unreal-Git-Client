import subprocess
import os
from pathlib import Path

class GitManager:
    def __init__(self):
        self.repo_path = None
        
    def set_repository(self, path):
        self.repo_path = path
        
    def run_command(self, command):
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                shell=True
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                return False, result.stderr.strip()
        except Exception as e:
            return False, str(e)
            
    def is_git_repository(self, path):
        git_dir = os.path.join(path, '.git')
        return os.path.exists(git_dir)
        
    def get_current_branch(self):
        success, output = self.run_command("git branch --show-current")
        return output if success else "unknown"
        
    def get_status(self):
        success, output = self.run_command("git status --porcelain")
        if not success:
            return {}
            
        status_dict = {}
        for line in output.split('\n'):
            if line:
                state = line[:2].strip()
                file_path = line[3:]
                status_dict[file_path] = state if state else "??"
                
        return status_dict
        
    def get_file_diff(self, file_path):
        success, output = self.run_command(f"git diff HEAD -- \"{file_path}\"")
        if success and output:
            return output
            
        success, output = self.run_command(f"git diff --cached -- \"{file_path}\"")
        if success and output:
            return output
            
        return "No hay diferencias para mostrar"
        
    def stage_all(self):
        return self.run_command("git add -A")
    
    def stage_file(self, file_path):
        return self.run_command(f"git add \"{file_path}\"")
        
    def unstage_file(self, file_path):
        return self.run_command(f"git reset HEAD \"{file_path}\"")
        
    def commit(self, message):
        escaped_message = message.replace('"', '\\"')
        return self.run_command(f"git commit -m \"{escaped_message}\"")
        
    def pull(self):
        return self.run_command("git pull")
        
    def push(self):
        return self.run_command("git push")
        
    def fetch(self):
        return self.run_command("git fetch")
        
    def get_repository_info(self):
        info = {}
        
        info['branch'] = self.get_current_branch()
        
        success, remote = self.run_command("git remote get-url origin")
        info['remote'] = remote if success else "No configurado"
        
        success, commit = self.run_command("git log -1 --pretty=format:'%h - %s (%an, %ar)'")
        info['last_commit'] = commit if success else "No hay commits"
        
        return info
        
    def get_commit_history(self, limit=20):
        success, output = self.run_command(
            f"git log -{limit} --pretty=format:'%H|%s|%an|%ar'"
        )
        
        if not success:
            return []
            
        commits = []
        for line in output.split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) == 4:
                    commits.append({
                        'hash': parts[0],
                        'message': parts[1],
                        'author': parts[2],
                        'date': parts[3]
                    })
                    
        return commits
        
    def get_commit_diff(self, commit_hash):
        success, output = self.run_command(f"git show {commit_hash}")
        return output if success else "No se pudo obtener el diff"
        
    def clone_repository(self, url, path):
        try:
            repo_name = url.rstrip('/').split('/')[-1].replace('.git', '')
            target_path = os.path.join(path, repo_name)
            
            result = subprocess.run(
                ['git', 'clone', url, target_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, target_path
            else:
                return False, result.stderr
        except Exception as e:
            return False, str(e)
            
    def is_lfs_installed(self):
        if not self.repo_path:
            return False
            
        success, _ = self.run_command("git lfs version")
        return success
        
    def install_lfs(self):
        if not self.repo_path:
            return False, "No hay repositorio cargado"
            
        success, message = self.run_command("git lfs install")
        return success, message
        
    def track_unreal_files(self):
        if not self.repo_path:
            return False, "No hay repositorio cargado"
            
        extensions = [
            "*.uasset", "*.umap", "*.ubulk", "*.upk",
            "*.uproject", "*.uplugin"
        ]
        
        for ext in extensions:
            success, message = self.run_command(f"git lfs track \"{ext}\"")
            if not success:
                return False, f"Error al trackear {ext}: {message}"
                
        success, message = self.run_command("git add .gitattributes")
        if not success:
            return False, f"Error al agregar .gitattributes: {message}"
            
        return True, "Archivos configurados correctamente"
        
    def lfs_pull(self):
        if not self.repo_path:
            return False, "No hay repositorio cargado"
            
        return self.run_command("git lfs pull")

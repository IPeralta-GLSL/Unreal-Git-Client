import subprocess
import os
from pathlib import Path
import re

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
    
    def get_all_branches(self):
        success, output = self.run_command("git branch -a")
        if not success:
            return []
        
        branches = []
        for line in output.split('\n'):
            if line.strip():
                is_current = line.startswith('*')
                branch_name = line.replace('*', '').strip()
                if not branch_name.startswith('remotes/origin/HEAD'):
                    branches.append({
                        'name': branch_name,
                        'is_current': is_current,
                        'is_remote': branch_name.startswith('remotes/')
                    })
        return branches
    
    def create_branch(self, branch_name, from_commit=None):
        if from_commit:
            return self.run_command(f"git branch \"{branch_name}\" {from_commit}")
        else:
            return self.run_command(f"git branch \"{branch_name}\"")
    
    def switch_branch(self, branch_name):
        clean_name = branch_name.replace('remotes/origin/', '')
        return self.run_command(f"git checkout \"{clean_name}\"")
    
    def delete_branch(self, branch_name, force=False):
        flag = "-D" if force else "-d"
        return self.run_command(f"git branch {flag} \"{branch_name}\"")
    
    def merge_branch(self, branch_name):
        return self.run_command(f"git merge \"{branch_name}\"")
        
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
        
    def translate_relative_date(self, date_str):
        translations = {
            'second': 'segundo',
            'seconds': 'segundos',
            'minute': 'minuto',
            'minutes': 'minutos',
            'hour': 'hora',
            'hours': 'horas',
            'day': 'día',
            'days': 'días',
            'week': 'semana',
            'weeks': 'semanas',
            'month': 'mes',
            'months': 'meses',
            'year': 'año',
            'years': 'años',
            'ago': 'hace',
        }
        
        result = date_str.lower()
        for eng, esp in translations.items():
            result = re.sub(r'\b' + eng + r'\b', esp, result)
        
        result = result.replace(' hace', '')
        result = f'hace {result.strip()}'
        
        return result
    
    def get_commit_history(self, limit=20):
        success, result = self.run_command(
            f'git log --pretty=format:"%H|||%an|||%ae|||%ad|||%s" --date=relative -n {limit}'
        )
        
        if not success:
            return []
        
        commits = []
        for line in result.splitlines():
            if '|||' in line:
                parts = line.split('|||')
                if len(parts) >= 5:
                    date_spanish = self.translate_relative_date(parts[3])
                    commits.append({
                        'hash': parts[0],
                        'author': parts[1],
                        'email': parts[2],
                        'date': date_spanish,
                        'message': parts[4]
                    })
        
        return commits
        
    def get_commit_diff(self, commit_hash):
        success, output = self.run_command(f"git show {commit_hash}")
        return output if success else "No se pudo obtener el diff"
    
    def reset_to_commit(self, commit_hash, mode='soft'):
        modes = {
            'soft': '--soft',
            'mixed': '--mixed',
            'hard': '--hard'
        }
        flag = modes.get(mode, '--soft')
        return self.run_command(f"git reset {flag} {commit_hash}")
    
    def revert_commit(self, commit_hash):
        return self.run_command(f"git revert {commit_hash} --no-edit")
    
    def checkout_commit(self, commit_hash):
        return self.run_command(f"git checkout {commit_hash}")
        
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
        
    def lfs_track_files(self, patterns):
        if not self.repo_path:
            return False, "No hay repositorio cargado"
            
        if isinstance(patterns, str):
            patterns = [patterns]
            
        for pattern in patterns:
            # Escape quotes if necessary, though simple patterns usually don't need it
            success, message = self.run_command(f"git lfs track \"{pattern}\"")
            if not success:
                return False, f"Error al trackear {pattern}: {message}"
                
        success, message = self.run_command("git add .gitattributes")
        if not success:
            return False, f"Error al agregar .gitattributes: {message}"
            
        return True, "Archivos configurados correctamente"
        
    def lfs_pull(self):
        if not self.repo_path:
            return False, "No hay repositorio cargado"
            
        return self.run_command("git lfs pull")

    def get_lfs_tracked_patterns(self):
        if not self.repo_path:
            return []
        
        success, output = self.run_command("git lfs track")
        if not success:
            return []
            
        patterns = []
        for line in output.split('\n'):
            if line.strip() and "Listing tracked patterns" not in line:
                parts = line.strip().split()
                if parts:
                    patterns.append(parts[0])
        return patterns

    def get_lfs_locks(self):
        if not self.repo_path:
            return []
            
        success, output = self.run_command("git lfs locks --json")
        if not success:
            return []
            
        import json
        try:
            locks = json.loads(output)
            return locks
        except:
            return []

    def lfs_lock_file(self, file_path):
        return self.run_command(f"git lfs lock \"{file_path}\"")

    def lfs_unlock_file(self, file_path, force=False):
        cmd = f"git lfs unlock \"{file_path}\""
        if force:
            cmd += " --force"
        return self.run_command(cmd)

    def lfs_prune(self):
        return self.run_command("git lfs prune")
    
    def get_lfs_storage_usage(self):
        if not self.repo_path:
            return 0
            
        lfs_dir = os.path.join(self.repo_path, '.git', 'lfs', 'objects')
        total_size = 0
        if os.path.exists(lfs_dir):
            for dirpath, dirnames, filenames in os.walk(lfs_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        total_size += os.path.getsize(fp)
        return total_size

    def format_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

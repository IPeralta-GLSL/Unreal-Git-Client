import subprocess
import os
import time
import fnmatch
from pathlib import Path
import re

def _is_valid_git_ref(ref):
    if not ref or not isinstance(ref, str):
        return False
    if len(ref) > 256:
        return False
    dangerous_chars = [';', '|', '&', '$', '`', '(', ')', '{', '}', '<', '>', '\n', '\r', '\0']
    for char in dangerous_chars:
        if char in ref:
            return False
    return True

class GitManager:
    def __init__(self):
        self.repo_path = None
        self._lfs_cache = []
        self._lfs_cache_ts = 0.0
        
    def set_repository(self, path):
        self.repo_path = path
        self._lfs_cache = []
        self._lfs_cache_ts = 0.0
    
    def check_and_remove_lock(self):
        if not self.repo_path:
            return False, "No repository path set"
        
        lock_file = os.path.join(self.repo_path, '.git', 'index.lock')
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
                return True, "Lock file removed successfully"
            except Exception as e:
                return False, f"Failed to remove lock file: {str(e)}"
        return False, "No lock file found"
        
    def run_command(self, command, timeout=30):
        try:
            use_shell = isinstance(command, str)
            
            kwargs = {
                'cwd': self.repo_path,
                'capture_output': True,
                'text': True,
                'shell': use_shell,
                'encoding': 'utf-8',
                'errors': 'replace',
                'timeout': timeout
            }
            
            if os.name == 'nt':
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            
            result = subprocess.run(command, **kwargs)

            if result.returncode == 0:
                return True, result.stdout.rstrip()
            else:
                error_msg = result.stderr.strip()
                if 'index.lock' in error_msg or 'unable to create' in error_msg.lower():
                    error_msg += "\n\nSugerencia: Otro proceso de Git está en uso o quedó bloqueado. Puedes intentar cerrar otros programas o usar la opción 'Desbloquear repositorio' del menú."
                return False, error_msg
        except subprocess.TimeoutExpired:
            return False, f"Command timed out after {timeout}s"
        except Exception as e:
            return False, str(e)
            
    def is_git_repository(self, path):
        git_dir = os.path.join(path, '.git')
        return os.path.exists(git_dir)
        
    def get_current_branch(self):
        summary = self.get_status_summary(include_sizes=False)
        if summary.get('branch'):
            return summary['branch']
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
        if not _is_valid_git_ref(branch_name):
            return False, "Invalid branch name"
        if from_commit:
            if not _is_valid_git_ref(from_commit):
                return False, "Invalid commit reference"
            return self.run_command(f"git branch \"{branch_name}\" {from_commit}")
        else:
            return self.run_command(f"git branch \"{branch_name}\"")
    
    def switch_branch(self, branch_name):
        if not _is_valid_git_ref(branch_name):
            return False, "Invalid branch name"
        clean_name = branch_name.replace('remotes/origin/', '')
        return self.run_command(f"git checkout \"{clean_name}\"")
    
    def delete_branch(self, branch_name, force=False):
        if not _is_valid_git_ref(branch_name):
            return False, "Invalid branch name"
        flag = "-D" if force else "-d"
        return self.run_command(f"git branch {flag} \"{branch_name}\"")
    
    def merge_branch(self, branch_name):
        if not _is_valid_git_ref(branch_name):
            return False, "Invalid branch name"
        return self.run_command(f"git merge \"{branch_name}\"")
    
    # ==================== STASH METHODS ====================
    
    def stash_save(self, message=None, include_untracked=True):
        """Save current changes to stash"""
        cmd = ['git', 'stash', 'push']
        if include_untracked:
            cmd.append('-u')
        if message:
            cmd.extend(['-m', message])
        return self.run_command(cmd)
    
    def stash_list(self):
        """Get list of all stashes"""
        success, output = self.run_command(['git', 'stash', 'list', '--format=%gd|%s|%ci'])
        if not success or not output:
            return []
        
        stashes = []
        for line in output.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|', 2)
            if len(parts) >= 3:
                stashes.append({
                    'index': parts[0],  # stash@{0}
                    'message': parts[1],
                    'date': parts[2]
                })
            elif len(parts) >= 2:
                stashes.append({
                    'index': parts[0],
                    'message': parts[1],
                    'date': ''
                })
        return stashes
    
    def stash_apply(self, stash_index='stash@{0}'):
        """Apply a stash without removing it"""
        return self.run_command(['git', 'stash', 'apply', stash_index])
    
    def stash_pop(self, stash_index='stash@{0}'):
        """Apply and remove a stash"""
        return self.run_command(['git', 'stash', 'pop', stash_index])
    
    def stash_drop(self, stash_index='stash@{0}'):
        """Remove a stash"""
        return self.run_command(['git', 'stash', 'drop', stash_index])
    
    def stash_clear(self):
        """Remove all stashes"""
        return self.run_command(['git', 'stash', 'clear'])
    
    def stash_show(self, stash_index='stash@{0}'):
        """Show stash diff"""
        success, output = self.run_command(['git', 'stash', 'show', '-p', stash_index])
        return output if success else "No se puede mostrar el stash"
    
    # ==================== CONFLICT METHODS ====================
    
    def get_conflicted_files(self):
        """Get list of files with merge conflicts"""
        success, output = self.run_command(['git', 'diff', '--name-only', '--diff-filter=U'])
        if not success or not output:
            return []
        return [f.strip() for f in output.strip().split('\n') if f.strip()]
    
    def has_conflicts(self):
        """Check if there are any merge conflicts"""
        return len(self.get_conflicted_files()) > 0
    
    def resolve_conflict_ours(self, file_path):
        """Resolve conflict using our version (current branch)"""
        success, msg = self.run_command(['git', 'checkout', '--ours', file_path])
        if success:
            return self.run_command(['git', 'add', file_path])
        return success, msg
    
    def resolve_conflict_theirs(self, file_path):
        """Resolve conflict using their version (incoming branch)"""
        success, msg = self.run_command(['git', 'checkout', '--theirs', file_path])
        if success:
            return self.run_command(['git', 'add', file_path])
        return success, msg
    
    def mark_resolved(self, file_path):
        """Mark a file as resolved after manual edit"""
        return self.run_command(['git', 'add', file_path])
    
    def abort_merge(self):
        """Abort the current merge"""
        return self.run_command(['git', 'merge', '--abort'])
    
    def continue_merge(self):
        """Continue merge after resolving conflicts (commit)"""
        return self.run_command(['git', 'commit', '--no-edit'])
    
    def get_merge_status(self):
        """Check if we're in a merge state"""
        merge_head = os.path.join(self.repo_path, '.git', 'MERGE_HEAD')
        return os.path.exists(merge_head)
        
    def get_status(self):
        summary = self.get_status_summary(include_sizes=False)
        result = {}
        for entry in summary.get('entries', []):
            result[entry['path']] = entry['state']
        return result
    
    def get_status_summary(self, include_sizes=False, size_threshold=100 * 1024 * 1024):
        if not self.repo_path:
            return {
                'branch': 'unknown',
                'ahead': 0,
                'behind': 0,
                'entries': [],
                'large_files': [],
                'error': 'repository path not set'
            }
        
        success, output = self.run_command([
            "git",
            "-c",
            "core.quotepath=false",
            "status",
            "--branch",
            "--porcelain=v1",
            "-uall"
        ], timeout=10)
        
        if not success or output is None:
            return {
                'branch': 'unknown',
                'ahead': 0,
                'behind': 0,
                'entries': [],
                'large_files': [],
                'error': output or 'git status failed'
            }

        branch = 'unknown'
        ahead = 0
        behind = 0
        entries = []
        large_files = []
        lfs_patterns = []

        if include_sizes:
            lfs_patterns = self.get_lfs_tracked_patterns()

        lines = output.split('\n')
        for line in lines:
            if not line:
                continue
            if line.startswith('##'):
                status_line = line[2:].strip()
                branch_part = status_line
                if '...' in status_line:
                    branch_part = status_line.split('...')[0]
                if branch_part:
                    branch = branch_part.split()[0]

                meta_start = status_line.find('[')
                meta_end = status_line.find(']')
                if meta_start != -1 and meta_end != -1 and meta_end > meta_start:
                    meta = status_line[meta_start + 1:meta_end]
                    ahead_match = re.search(r'ahead (\d+)', meta)
                    behind_match = re.search(r'behind (\d+)', meta)
                    if ahead_match:
                        ahead = int(ahead_match.group(1))
                    if behind_match:
                        behind = int(behind_match.group(1))
                continue

            if len(line) <= 3:
                continue

            state = line[:2].strip()
            file_path = line[3:]

            if file_path.startswith('"') and file_path.endswith('"'):
                file_path = file_path[1:-1]
                file_path = file_path.replace('\\"', '"').replace('\\\\', '\\')

            if '->' in file_path:
                parts = file_path.split(' -> ')
                if len(parts) == 2:
                    file_path = parts[1]

            is_large = False
            if include_sizes and not state.startswith('D'):
                full_path = os.path.join(self.repo_path, file_path)
                if os.path.exists(full_path) and not os.path.isdir(full_path):
                    try:
                        size = os.path.getsize(full_path)
                        if size > size_threshold:
                            tracked = False
                            for pattern in lfs_patterns:
                                if fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(os.path.basename(file_path), pattern):
                                    tracked = True
                                    break
                            if not tracked:
                                is_large = True
                    except Exception:
                        pass

            entries.append({
                'path': file_path,
                'state': state or '??',
                'large': is_large
            })

            if is_large:
                large_files.append(file_path)

        return {
            'branch': branch,
            'ahead': ahead,
            'behind': behind,
            'entries': entries,
            'large_files': large_files,
            'error': None
        }
        
    def get_file_diff(self, file_path):
        success, output = self.run_command(f"git diff HEAD -- \"{file_path}\"")
        if success and output:
            return output
            
        success, output = self.run_command(f"git diff --cached -- \"{file_path}\"")
        if success and output:
            return output
            
        return "No hay diferencias para mostrar"
        
    def stage_all(self):
        return self.run_command(['git', 'add', '.'])
        
    def pull(self):
        return self.run_command(['git', 'pull'])
        
    def push(self, progress_callback=None):
        if progress_callback:
            try:
                kwargs = {
                    'cwd': self.repo_path,
                    'stdout': subprocess.PIPE,
                    'stderr': subprocess.STDOUT,
                    'text': True,
                    'encoding': 'utf-8',
                    'errors': 'replace',
                    'bufsize': 1
                }
                
                if os.name == 'nt':
                    kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

                process = subprocess.Popen(
                    ['git', 'push', '--progress'],
                    **kwargs
                )
                
                output_lines = []
                while True:
                    line = process.stdout.readline() if process.stdout else ''
                    if not line and process.poll() is not None:
                        break
                    if line:
                        output_lines.append(line)
                        progress_callback(line.strip())
                
                process.wait()
                full_output = ''.join(output_lines)
                
                if process.returncode == 0:
                    return True, full_output or "Push completed successfully"
                else:
                    return False, full_output or "Push failed"
            except Exception as e:
                return False, str(e)
        else:
            return self.run_command(['git', 'push'])
        
    def fetch(self):
        return self.run_command(['git', 'fetch'])
        
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
        success, result = self.run_command([
            'git',
            'log',
            '--no-color',
            '--pretty=format:%H|||%an|||%ae|||%ad|||%s',
            '--date=relative',
            '-n',
            str(limit)
        ])
        
        if not success:
            return []
        if not result:
            return []
        
        commits = []
        for line in result.splitlines():
            if '|||' not in line:
                continue
            parts = line.split('|||')
            if len(parts) < 5:
                continue
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
        if not _is_valid_git_ref(commit_hash):
            return "Invalid commit hash"
        success, output = self.run_command(f"git show {commit_hash}")
        return output if success else "No se pudo obtener el diff"
    
    def get_commit_files(self, commit_hash):
        if not _is_valid_git_ref(commit_hash):
            return []
        success, output = self.run_command(f"git show --name-status --format= {commit_hash}")
        if not success:
            return []
        files = []
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.split('\t', 1)
            if len(parts) == 2:
                status, path = parts
                files.append({'status': status[0], 'path': path})
        return files
    
    def get_commit_file_diff(self, commit_hash, file_path):
        if not _is_valid_git_ref(commit_hash):
            return ""
        success, output = self.run_command(f"git show {commit_hash} -- \"{file_path}\"")
        if not success:
            return ""
        lines = output.split('\n')
        diff_lines = []
        in_diff = False
        for line in lines:
            if line.startswith('diff --git'):
                in_diff = True
            if in_diff:
                diff_lines.append(line)
        return '\n'.join(diff_lines)
    
    def reset_to_commit(self, commit_hash, mode='soft'):
        if not _is_valid_git_ref(commit_hash):
            return False, "Invalid commit hash"
        modes = {
            'soft': '--soft',
            'mixed': '--mixed',
            'hard': '--hard'
        }
        flag = modes.get(mode, '--soft')
        return self.run_command(f"git reset {flag} {commit_hash}")
    
    def revert_commit(self, commit_hash):
        if not _is_valid_git_ref(commit_hash):
            return False, "Invalid commit hash"
        return self.run_command(f"git revert {commit_hash} --no-edit")
    
    def checkout_commit(self, commit_hash):
        if not _is_valid_git_ref(commit_hash):
            return False, "Invalid commit hash"
        return self.run_command(f"git checkout {commit_hash}")
        
    def clone_repository(self, url, path, progress_callback=None):
        try:
            repo_name = url.rstrip('/').split('/')[-1].replace('.git', '')
            target_path = os.path.join(path, repo_name)
            
            if progress_callback:
                if progress_callback: progress_callback(f"Cloning into {target_path}...")
                
                kwargs = {
                    'stdout': subprocess.PIPE,
                    'stderr': subprocess.STDOUT,
                    'text': True,
                    'encoding': 'utf-8',
                    'errors': 'replace',
                    'bufsize': 1
                }
                if os.name == 'nt':
                    kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                    
                process = subprocess.Popen(
                    ['git', 'clone', '--progress', url, target_path],
                    **kwargs
                )
                
                output_lines = []
                while True:
                    line = process.stdout.readline() if process.stdout else ''
                    if not line and process.poll() is not None:
                        break
                    if line:
                        output_lines.append(line)
                        if progress_callback:
                            progress_callback(line.strip())
                
                process.wait()
                
                if process.returncode == 0:
                    return True, target_path
                else:
                    return False, ''.join(output_lines)
            else:
                kwargs = {
                    'capture_output': True,
                    'text': True,
                    'encoding': 'utf-8',
                    'errors': 'replace'
                }
                if os.name == 'nt':
                    kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                    
                result = subprocess.run(
                    ['git', 'clone', url, target_path],
                    **kwargs
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

        def _normalize_pattern(value: str) -> str:
            value = (value or "").strip()
            value = value.replace('[[space]]', ' ')
            if not value:
                return value

            repo_root = os.path.abspath(self.repo_path)
            candidate = value
            try:
                if os.path.isabs(candidate):
                    abs_candidate = os.path.abspath(candidate)
                    if os.path.commonpath([repo_root, abs_candidate]) == repo_root:
                        candidate = os.path.relpath(abs_candidate, repo_root)
                    else:
                        return ""
            except Exception:
                pass

            candidate = candidate.replace('\\', '/')
            while candidate.startswith('./'):
                candidate = candidate[2:]
            return candidate
            
        def _looks_like_glob(value: str) -> bool:
            return any(ch in value for ch in ['*', '?', '[', ']'])

        normalized = []
        for raw in patterns:
            p = _normalize_pattern(raw)
            if p:
                normalized.append(p)

        if not normalized:
            return False, "No se encontraron patrones/archivos válidos para LFS en este repositorio"

        gitattributes_path = os.path.join(self.repo_path, '.gitattributes')
        
        existing_patterns = set()
        if os.path.exists(gitattributes_path):
            try:
                with open(gitattributes_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and 'filter=lfs' in line:
                            pattern = line.split()[0]
                            existing_patterns.add(pattern)
            except Exception:
                pass

        new_entries = []
        for pattern in normalized:
            if pattern not in existing_patterns:
                # Wrap in quotes if it contains spaces or special chars
                pattern_str = pattern
                if ' ' in pattern_str or any(c in pattern_str for c in '()[]{}'):
                    if not pattern_str.startswith('"'):
                        pattern_str = f'"{pattern_str}"'
                
                new_entries.append(f"{pattern_str} filter=lfs diff=lfs merge=lfs -text\n")

        if new_entries:
            try:
                with open(gitattributes_path, 'a', encoding='utf-8') as f:
                    f.writelines(new_entries)
            except Exception as e:
                return False, f"Error al escribir .gitattributes: {str(e)}"

        if os.path.exists(gitattributes_path):
            success, message = self.run_command(['git', 'add', '.gitattributes'])
            if not success:
                return False, f"Error al agregar .gitattributes: {message}"

        files_to_readd = []
        for pattern in normalized:
            if _looks_like_glob(pattern):
                continue

            abs_path = os.path.join(self.repo_path, pattern)
            if not os.path.exists(abs_path) or os.path.isdir(abs_path):
                continue

            tracked, _ = self.run_command(['git', 'ls-files', '--error-unmatch', '--', pattern])
            if tracked:
                success, message = self.run_command(['git', 'rm', '--cached', '--', pattern])
                if not success:
                    return False, f"Error al preparar {pattern} para LFS: {message}"

            files_to_readd.append(pattern)

        if files_to_readd:
            success, message = self.stage_files(files_to_readd)
            if not success:
                return False, message

        self._lfs_cache = []
        self._lfs_cache_ts = 0.0
        return True, "Archivos configurados correctamente"
        
    def lfs_pull(self):
        if not self.repo_path:
            return False, "No hay repositorio cargado"
            
        return self.run_command("git lfs pull")

    def get_lfs_tracked_patterns(self):
        if not self.repo_path:
            return []

        now = time.time()
        if self._lfs_cache and now - self._lfs_cache_ts < 10.0:
            return list(self._lfs_cache)
        
        success, output = self.run_command("git lfs track")
        if not success:
            return []
            
        patterns = []
        for line in output.split('\n'):
            line = line.strip()
            if not line or "Listing tracked patterns" in line:
                continue
                
            # Format is: pattern (File: .gitattributes)
            # Find the last occurrence of " (File: " to separate pattern from source
            r_index = line.rfind(" (File: ")
            if r_index != -1:
                pattern = line[:r_index]
                # Remove surrounding quotes if present
                if pattern.startswith('"') and pattern.endswith('"'):
                    pattern = pattern[1:-1]
                patterns.append(pattern)
            else:
                # Fallback
                parts = line.split()
                if parts:
                    patterns.append(parts[0])
        self._lfs_cache = patterns
        self._lfs_cache_ts = now
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
        except json.JSONDecodeError:
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

    def add_to_gitignore(self, file_path):
        if not self.repo_path:
            return False, "No repository loaded"
        
        gitignore_path = os.path.join(self.repo_path, '.gitignore')
        try:
            prefix = ""
            if os.path.exists(gitignore_path) and os.path.getsize(gitignore_path) > 0:
                prefix = "\n"
                
            with open(gitignore_path, 'a', encoding='utf-8') as f:
                f.write(f"{prefix}{file_path}")
            return True, "Added to .gitignore"
        except Exception as e:
            return False, str(e)

    def stage_files(self, files):
        if not files:
            return True, "No files to stage"
        
        if isinstance(files, list):
            chunk_size = 50
            for i in range(0, len(files), chunk_size):
                chunk = files[i:i + chunk_size]
                cmd = ['git', 'add', '--'] + chunk
                success, message = self.run_command(cmd)
                if not success:
                    return False, message
            return True, "Files staged"
        else:
            return self.run_command(['git', 'add', '--', files])
            
    def unstage_all(self):
        return self.run_command(['git', 'reset'])
    
    def unstage_file(self, file_path):
        return self.run_command(['git', 'reset', 'HEAD', '--', file_path])
        
    def commit(self, message):
        return self.run_command(['git', 'commit', '-m', message])

    def discard_file(self, file_path):
        success, output = self.run_command(["git", "ls-files", "--error-unmatch", file_path])
        is_tracked = success
        
        if is_tracked:
            return self.run_command(["git", "checkout", "HEAD", "--", file_path])
        else:
            try:
                full_path = os.path.join(self.repo_path, file_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    return True, "File deleted"
                else:
                    return True, "File already removed"
            except Exception as e:
                return False, str(e)

    def stage_file(self, file_path):
        return self.stage_files(file_path)

    def get_ahead_behind_count(self):
        summary = self.get_status_summary(include_sizes=False)
        return summary.get('ahead', 0), summary.get('behind', 0)

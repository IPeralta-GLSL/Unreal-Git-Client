import json
from pathlib import Path

class TranslationManager:
    def __init__(self):
        self.current_language = 'es'
        self.translations = {
            'es': {
                'app_name': 'Cliente Git',
                'ready': 'Listo',
                'home': 'Inicio',
                'repository': 'Repositorio',
                
                'file': 'Archivo',
                'edit': 'Editar',
                'view': 'Ver',
                'help': 'Ayuda',
                
                'open_repository': 'Abrir Repositorio',
                'clone_repository': 'Clonar Repositorio',
                'settings': 'Ajustes',
                'exit': 'Salir',
                'close': 'Cerrar',
                
                'new_tab': 'Nueva pestaña',
                'close_tab': 'Cerrar pestaña',
                
                'changes': 'CAMBIOS',
                'changes_desc': 'Archivos modificados en el área de trabajo',
                'staged': 'PREPARADOS',
                'staged_desc': 'Archivos listos para commit',
                'branches': 'RAMAS',
                'branches_desc': 'Gestión de ramas del repositorio',
                'history': 'HISTORIAL',
                'history_desc': 'Gráfico de commits del repositorio',
                
                'commit_message': 'Mensaje del commit',
                'commit_message_placeholder': 'Escribe un mensaje descriptivo del commit...',
                'commit': 'Commit',
                'stage_all': 'Preparar Todo',
                'unstage_all': 'Quitar Todo',
                'discard_changes': 'Descartar Cambios',
                
                'current_branch': 'Rama actual',
                'new_branch': 'Nueva Rama',
                'merge_branch': 'Fusionar Rama',
                'delete_branch': 'Eliminar Rama',
                'checkout_branch': 'Cambiar a Rama',
                
                'pull': 'Pull',
                'push': 'Push',
                'fetch': 'Fetch',
                
                'stage': 'Preparar',
                'unstage': 'Quitar',
                'discard': 'Descartar',
                
                'modified': 'Modificado',
                'added': 'Agregado',
                'deleted': 'Eliminado',
                'renamed': 'Renombrado',
                'untracked': 'Sin seguimiento',
                
                'author': 'Autor',
                'date': 'Fecha',
                'hash': 'Hash',
                'message': 'Mensaje',
                
                'select_repository': 'Seleccionar Repositorio Git',
                'not_git_repository': 'No es un repositorio Git',
                'not_git_repository_msg': 'La carpeta seleccionada no contiene un repositorio Git.',
                'repository_loaded': 'Repositorio cargado',
                
                'github_accounts': 'Administrar Cuentas de GitHub',
                'gitlab_accounts': 'Administrar Cuentas de GitLab',
                'add_edit_account': 'Agregar/Editar Cuenta',
                'saved_accounts': 'Cuentas Guardadas',
                
                'username': 'Usuario',
                'email': 'Email',
                'token': 'Token',
                'server': 'Servidor',
                'show': 'Mostrar',
                'hide': 'Ocultar',
                
                'add_account': 'Agregar Cuenta',
                'update_account': 'Actualizar Cuenta',
                'delete_account': 'Eliminar Cuenta',
                'clear_fields': 'Limpiar Campos',
                
                'required_fields': 'Campos requeridos',
                'username_token_required': 'Usuario y Token son obligatorios',
                'username_token_server_required': 'Usuario, Token y Servidor son obligatorios',
                'username_required': 'Usuario es obligatorio',
                'username_server_required': 'Usuario y Servidor son obligatorios',
                
                'account_not_found': 'Cuenta no encontrada',
                'account_not_found_msg': 'No existe una cuenta con el usuario',
                
                'success': 'Éxito',
                'github_account_added': 'Cuenta de GitHub agregada correctamente',
                'gitlab_account_added': 'Cuenta de GitLab agregada correctamente',
                'github_account_updated': 'Cuenta de GitHub actualizada correctamente',
                'gitlab_account_updated': 'Cuenta de GitLab actualizada correctamente',
                
                'confirm_delete': 'Confirmar eliminación',
                'confirm_delete_account': '¿Estás seguro de eliminar la cuenta',
                'no_selection': 'Sin selección',
                'select_account_to_delete': 'Selecciona una cuenta para eliminar',
                'account_deleted': 'Cuenta eliminada correctamente',
                
                'welcome': 'Bienvenido a Git Client',
                'welcome_desc': 'Comienza abriendo un repositorio existente o clonando uno nuevo',
                'recent_repositories': 'Repositorios Recientes',
                'no_recent_repos': 'No hay repositorios recientes',
                'quick_actions': 'Acciones Rápidas',
                
                'optional': 'opcional',
                'no_email': 'Sin email',
                'no_message': 'Sin mensaje',
                'unknown': 'Desconocido',
            },
            'en': {
                'app_name': 'Git Client',
                'ready': 'Ready',
                'home': 'Home',
                'repository': 'Repository',
                
                'file': 'File',
                'edit': 'Edit',
                'view': 'View',
                'help': 'Help',
                
                'open_repository': 'Open Repository',
                'clone_repository': 'Clone Repository',
                'settings': 'Settings',
                'exit': 'Exit',
                'close': 'Close',
                
                'new_tab': 'New tab',
                'close_tab': 'Close tab',
                
                'changes': 'CHANGES',
                'changes_desc': 'Modified files in the working directory',
                'staged': 'STAGED',
                'staged_desc': 'Files ready to commit',
                'branches': 'BRANCHES',
                'branches_desc': 'Repository branch management',
                'history': 'HISTORY',
                'history_desc': 'Repository commit graph',
                
                'commit_message': 'Commit message',
                'commit_message_placeholder': 'Write a descriptive commit message...',
                'commit': 'Commit',
                'stage_all': 'Stage All',
                'unstage_all': 'Unstage All',
                'discard_changes': 'Discard Changes',
                
                'current_branch': 'Current branch',
                'new_branch': 'New Branch',
                'merge_branch': 'Merge Branch',
                'delete_branch': 'Delete Branch',
                'checkout_branch': 'Checkout Branch',
                
                'pull': 'Pull',
                'push': 'Push',
                'fetch': 'Fetch',
                
                'stage': 'Stage',
                'unstage': 'Unstage',
                'discard': 'Discard',
                
                'modified': 'Modified',
                'added': 'Added',
                'deleted': 'Deleted',
                'renamed': 'Renamed',
                'untracked': 'Untracked',
                
                'author': 'Author',
                'date': 'Date',
                'hash': 'Hash',
                'message': 'Message',
                
                'select_repository': 'Select Git Repository',
                'not_git_repository': 'Not a Git repository',
                'not_git_repository_msg': 'The selected folder does not contain a Git repository.',
                'repository_loaded': 'Repository loaded',
                
                'github_accounts': 'Manage GitHub Accounts',
                'gitlab_accounts': 'Manage GitLab Accounts',
                'add_edit_account': 'Add/Edit Account',
                'saved_accounts': 'Saved Accounts',
                
                'username': 'Username',
                'email': 'Email',
                'token': 'Token',
                'server': 'Server',
                'show': 'Show',
                'hide': 'Hide',
                
                'add_account': 'Add Account',
                'update_account': 'Update Account',
                'delete_account': 'Delete Account',
                'clear_fields': 'Clear Fields',
                
                'required_fields': 'Required fields',
                'username_token_required': 'Username and Token are required',
                'username_token_server_required': 'Username, Token and Server are required',
                'username_required': 'Username is required',
                'username_server_required': 'Username and Server are required',
                
                'account_not_found': 'Account not found',
                'account_not_found_msg': 'There is no account with username',
                
                'success': 'Success',
                'github_account_added': 'GitHub account added successfully',
                'gitlab_account_added': 'GitLab account added successfully',
                'github_account_updated': 'GitHub account updated successfully',
                'gitlab_account_updated': 'GitLab account updated successfully',
                
                'confirm_delete': 'Confirm deletion',
                'confirm_delete_account': 'Are you sure you want to delete the account',
                'no_selection': 'No selection',
                'select_account_to_delete': 'Select an account to delete',
                'account_deleted': 'Account deleted successfully',
                
                'welcome': 'Welcome to Git Client',
                'welcome_desc': 'Start by opening an existing repository or cloning a new one',
                'recent_repositories': 'Recent Repositories',
                'no_recent_repos': 'No recent repositories',
                'quick_actions': 'Quick Actions',
                
                'optional': 'optional',
                'no_email': 'No email',
                'no_message': 'No message',
                'unknown': 'Unknown',
            }
        }
        
    def set_language(self, language_code):
        if language_code in self.translations:
            self.current_language = language_code
            return True
        return False
    
    def get(self, key, **kwargs):
        translation = self.translations.get(self.current_language, {}).get(key, key)
        if kwargs:
            try:
                return translation.format(**kwargs)
            except KeyError:
                return translation
        return translation
    
    def get_current_language(self):
        return self.current_language
    
    def get_available_languages(self):
        return list(self.translations.keys())

_translation_manager = None

def get_translation_manager():
    global _translation_manager
    if _translation_manager is None:
        _translation_manager = TranslationManager()
    return _translation_manager

def set_language(language_code):
    tm = get_translation_manager()
    return tm.set_language(language_code)

def tr(key, **kwargs):
    tm = get_translation_manager()
    return tm.get(key, **kwargs)

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
                
                'git_client': 'Git Client',
                'open_repository_btn': 'Abrir Repositorio',
                'open_repository_desc': 'Abre un repositorio Git existente',
                'clone_repository_btn': 'Clonar Repositorio',
                'clone_repository_desc': 'Descarga un repositorio remoto',
                'quick_tips': 'Consejos Rápidos',
                'tip_new_tab': 'Ctrl+T para nueva pestaña, Ctrl+W para cerrar',
                'tip_git_lfs': 'Git LFS es esencial para proyectos de Unreal Engine',
                'tip_commit_messages': 'Escribe mensajes de commit descriptivos y claros',
                'tip_pull_before_push': 'Usa Pull antes de Push para evitar conflictos',
                'tip_create_branches': 'Crea ramas para nuevas características',
                'shortcuts_text': 'Atajos: Ctrl+T nueva pestaña • Ctrl+W cerrar • Ctrl+Tab cambiar',
                'version_text': 'v1.0.0 • Soporte para Git LFS y Unreal Engine',
                
                'optional': 'opcional',
                'no_email': 'Sin email',
                'no_message': 'Sin mensaje',
                'unknown': 'Desconocido',
                
                'general': 'General',
                'general_config': 'Configuración General',
                'general_settings': 'Configuración General',
                'language': 'Idioma',
                'language_settings': 'Idioma / Language',
                'language_change_note': 'El cambio de idioma se aplicará en el siguiente inicio de la aplicación.',
                'language_changed_restart': 'Idioma cambiado. Reinicia la aplicación para ver los cambios.',
                'configuration': 'Configuración',
                'configuration_accounts': 'Configuración y cuentas',
                
                'clone': 'Clonar',
                'clone_repository': 'Clonar Repositorio',
                'clone_git_repository': 'Clonar Repositorio Git',
                'clone_description': 'Descarga una copia de un repositorio remoto a tu computadora',
                'repository_url': 'URL del Repositorio',
                'destination_folder': 'Carpeta de Destino',
                'browse': 'Explorar',
                'cancel': 'Cancelar',
                'clone_helper': 'El repositorio se clonará en una nueva carpeta dentro de la ubicación seleccionada',
                'select_folder': 'Seleccionar Carpeta',
                
                'accounts': 'Cuentas',
                'plugins': 'Plugins',
                'appearance': 'Apariencia',
                'my_accounts': 'Mis Cuentas',
                'git_local': 'Git Local',
                'connected_accounts': 'Tus cuentas conectadas:',
                'refresh': 'Actualizar',
                'remove': 'Eliminar',
                'delete': 'Eliminar',
                
                'login_with_github': 'Login con GitHub',
                'login_with_gitlab': 'Login con GitLab',
                'alternative_methods': 'Métodos alternativos:',
                'add_token_manually': 'Agregar un Personal Access Token manualmente:',
                'add_token': 'Agregar Token',
                'gitlab_url': 'URL de GitLab:',
                'application_id': 'Application ID:',
                'application_secret': 'Application Secret:',
                'connect_gitlab': 'Conectar con GitLab',
                'add_pat_manually': 'O agrega manualmente un Personal Access Token:',
                
                'git_global_config': 'Configura tu identidad global de Git:',
                'name': 'Nombre',
                'email': 'Email',
                'full_name_placeholder': 'Tu nombre completo',
                'email_placeholder': 'tu@email.com',
                'save_global_config': 'Guardar Configuración Global',
                
                'starting_auth': 'Iniciando autenticación...',
                'auth_error_connection': 'Error al iniciar la autenticación. Verifica tu conexión a internet.',
                'auth_timeout': 'Tiempo de espera agotado. Intenta nuevamente.',
                'error_user_info': 'Error al obtener información del usuario.',
                'auth_error': 'Error en la autenticación. Intenta nuevamente.',
                'starting_gitlab_auth': 'Iniciando autenticación con GitLab...',
                
                'installed_plugins': 'Plugins instalados:',
                'enable': 'Activar',
                'disable': 'Desactivar',
                
                'appearance_customization': 'Personalización de Apariencia',
                'select_theme': 'Selecciona el tema que prefieras para la interfaz:',
                'selected': 'Seleccionado',
                'select': 'Seleccionar',
                'theme_changes_instant': 'Los cambios de tema se aplican inmediatamente sin necesidad de reiniciar',
                
                'enter_gitlab_app_id': 'Ingresa tu GitLab Application ID',
                'enter_gitlab_app_secret': 'Ingresa tu GitLab Application Secret',
                
                'error': 'Error',
                'timeout': 'Timeout',
                'enter_client_id_secret': 'Por favor ingresa el Client ID y Client Secret',
                'enter_app_id_secret': 'Ingresa Application ID y Secret',
                'oauth_server_error': 'No se pudo iniciar servidor OAuth',
                'timeout_expired': 'Tiempo de espera agotado',
                'error_get_user_info': 'No se pudo obtener información del usuario',
                'no_access_token': 'No se recibió token de acceso',
                'error_exchange_code': 'Error al intercambiar código',
                'oauth_error': 'Error en OAuth',
                'enter_valid_token': 'Ingresa un token válido',
                'invalid_token': 'Token inválido o sin permisos',
                'error_verify_token': 'Error al verificar token',
                'enter_name_email': 'Ingresa nombre y email',
                'error_save_config': 'Error al guardar configuración',
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
                
                'git_client': 'Git Client',
                'open_repository_btn': 'Open Repository',
                'open_repository_desc': 'Open an existing Git repository',
                'clone_repository_btn': 'Clone Repository',
                'clone_repository_desc': 'Download a remote repository',
                'quick_tips': 'Quick Tips',
                'tip_new_tab': 'Ctrl+T for new tab, Ctrl+W to close',
                'tip_git_lfs': 'Git LFS is essential for Unreal Engine projects',
                'tip_commit_messages': 'Write descriptive and clear commit messages',
                'tip_pull_before_push': 'Use Pull before Push to avoid conflicts',
                'tip_create_branches': 'Create branches for new features',
                'shortcuts_text': 'Shortcuts: Ctrl+T new tab • Ctrl+W close • Ctrl+Tab switch',
                'version_text': 'v1.0.0 • Support for Git LFS and Unreal Engine',
                
                'optional': 'optional',
                'no_email': 'No email',
                'no_message': 'No message',
                'unknown': 'Unknown',
                
                'general': 'General',
                'general_config': 'General Configuration',
                'general_settings': 'General Settings',
                'language': 'Language',
                'language_settings': 'Language / Idioma',
                'language_change_note': 'Language changes will take effect on the next application start.',
                'language_changed_restart': 'Language changed. Restart the application to see the changes.',
                'configuration': 'Configuration',
                'configuration_accounts': 'Configuration and accounts',
                
                'clone': 'Clone',
                'clone_repository': 'Clone Repository',
                'clone_git_repository': 'Clone Git Repository',
                'clone_description': 'Download a copy of a remote repository to your computer',
                'repository_url': 'Repository URL',
                'destination_folder': 'Destination Folder',
                'browse': 'Browse',
                'cancel': 'Cancel',
                'clone_helper': 'The repository will be cloned into a new folder within the selected location',
                'select_folder': 'Select Folder',
                
                'accounts': 'Accounts',
                'plugins': 'Plugins',
                'appearance': 'Appearance',
                'my_accounts': 'My Accounts',
                'git_local': 'Git Local',
                'connected_accounts': 'Your connected accounts:',
                'refresh': 'Refresh',
                'remove': 'Remove',
                'delete': 'Delete',
                
                'login_with_github': 'Login with GitHub',
                'login_with_gitlab': 'Login with GitLab',
                'alternative_methods': 'Alternative methods:',
                'add_token_manually': 'Add a Personal Access Token manually:',
                'add_token': 'Add Token',
                'gitlab_url': 'GitLab URL:',
                'application_id': 'Application ID:',
                'application_secret': 'Application Secret:',
                'connect_gitlab': 'Connect with GitLab',
                'add_pat_manually': 'Or add a Personal Access Token manually:',
                
                'git_global_config': 'Configure your global Git identity:',
                'name': 'Name',
                'email': 'Email',
                'full_name_placeholder': 'Your full name',
                'email_placeholder': 'your@email.com',
                'save_global_config': 'Save Global Configuration',
                
                'starting_auth': 'Starting authentication...',
                'auth_error_connection': 'Error starting authentication. Check your internet connection.',
                'auth_timeout': 'Timeout expired. Try again.',
                'error_user_info': 'Error getting user information.',
                'auth_error': 'Authentication error. Try again.',
                'starting_gitlab_auth': 'Starting GitLab authentication...',
                
                'installed_plugins': 'Installed plugins:',
                'enable': 'Enable',
                'disable': 'Disable',
                
                'appearance_customization': 'Appearance Customization',
                'select_theme': 'Select your preferred theme for the interface:',
                'selected': 'Selected',
                'select': 'Select',
                'theme_changes_instant': 'Theme changes are applied immediately without restarting',
                
                'enter_gitlab_app_id': 'Enter your GitLab Application ID',
                'enter_gitlab_app_secret': 'Enter your GitLab Application Secret',
                
                'error': 'Error',
                'timeout': 'Timeout',
                'enter_client_id_secret': 'Please enter Client ID and Client Secret',
                'enter_app_id_secret': 'Enter Application ID and Secret',
                'oauth_server_error': 'Could not start OAuth server',
                'timeout_expired': 'Timeout expired',
                'error_get_user_info': 'Could not get user information',
                'no_access_token': 'No access token received',
                'error_exchange_code': 'Error exchanging code',
                'oauth_error': 'OAuth error',
                'enter_valid_token': 'Enter a valid token',
                'invalid_token': 'Invalid token or no permissions',
                'error_verify_token': 'Error verifying token',
                'enter_name_email': 'Enter name and email',
                'error_save_config': 'Error saving configuration',
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

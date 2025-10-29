# Repositorios Recientes y Avatares de Usuario

## 📚 Nueva funcionalidad: Repositorios Recientes

### Características implementadas:

1. **Persistencia de repositorios**:
   - Los repositorios abiertos se guardan automáticamente en `~/.unreal-git-client/settings.json`
   - Se mantienen hasta 10 repositorios recientes
   - Solo se muestran repositorios que aún existen en el sistema

2. **Visualización en Home**:
   - Lista de últimos 8 repositorios usados
   - Icono diferenciado para proyectos de Unreal Engine (🎮) vs repositorios normales (📁)
   - Información del nombre y ruta completa
   - Diseño con scroll si hay muchos repositorios
   - Botones interactivos con hover effects

3. **Gestión automática**:
   - Al abrir un repositorio, se agrega automáticamente a recientes
   - Los duplicados se eliminan (solo mantiene el más reciente)
   - Ordenados por última fecha de acceso

### Archivos creados:

- **`core/settings_manager.py`**: Maneja la persistencia de configuración
  - `add_recent_repo()`: Agrega repositorio a la lista
  - `get_recent_repos()`: Obtiene lista filtrada de repos existentes
  - `remove_recent_repo()`: Elimina un repositorio
  - `clear_recent_repos()`: Limpia toda la lista

### Integración:

```python
# En HomeView
recent_section = self.create_recent_repos_section()
if recent_section:
    layout.addWidget(recent_section)

# En RepositoryTab
if self.settings_manager:
    self.settings_manager.add_recent_repo(path, repo_name)
    self.home_view.refresh_recent_repos()
```

---

## 👤 Avatares de Perfil en el Historial

### Características implementadas:

1. **Avatares con Gravatar**:
   - Descarga automática de avatares desde Gravatar usando el email del commit
   - Avatares circulares de 48x48 píxeles
   - Cache local para evitar descargas repetidas
   - Descarga asíncrona sin bloquear la UI

2. **Avatares con iniciales (fallback)**:
   - Si no hay Gravatar disponible, genera avatar con iniciales
   - Colores automáticos basados en el nombre del autor
   - 7 colores diferentes para variedad visual
   - Iniciales extraídas del nombre (primera letra del nombre + primera letra del apellido)

3. **Visualización mejorada del historial**:
   - Avatar a la izquierda de cada commit
   - Formato de 2 líneas:
     - Línea 1: Hash corto + mensaje del commit
     - Línea 2: Autor + fecha relativa
   - Tooltip con información completa
   - Items de 70px de altura para mejor visualización

### Implementación técnica:

```python
# Avatar con iniciales
def create_initial_avatar(self, author_name):
    pixmap = QPixmap(48, 48)
    painter = QPainter(pixmap)
    # Dibuja círculo de color
    # Dibuja iniciales centradas
    return QIcon(pixmap)

# Descarga de Gravatar
def download_gravatar(self, email, author_name):
    email_hash = hashlib.md5(email.lower().encode()).hexdigest()
    url = f"https://www.gravatar.com/avatar/{email_hash}?s=48&d=404"
    request = QNetworkRequest(QUrl(url))
    self.network_manager.get(request)

# Callback asíncrono
def on_avatar_downloaded(self, reply):
    # Procesa la imagen
    # Crea avatar circular
    # Actualiza el cache
    # Actualiza los items del historial
```

### Mejoras en git_manager.py:

```python
# Incluye email en el formato de log
def get_commit_history(self, limit=20):
    success, result = self.run_command(
        f'git log --pretty=format:"%H|||%an|||%ae|||%ad|||%s" --date=relative -n {limit}'
    )
```

---

## 🎨 Mejoras visuales adicionales

### Home View:
- Sección de repositorios recientes con scroll
- Detección automática de proyectos Unreal
- Diseño responsive
- Hover effects en botones

### Historial:
- Items más grandes (70px)
- Iconos de avatar prominentes
- Mejor legibilidad con formato de 2 líneas
- Colores consistentes con el tema

---

## 📝 Archivos modificados:

1. **`core/settings_manager.py`** (nuevo):
   - Gestión de configuración persistente
   - Sistema de repositorios recientes

2. **`core/git_manager.py`**:
   - Agregado email a `get_commit_history()`
   - Formato: `%H|||%an|||%ae|||%ad|||%s`

3. **`ui/home_view.py`**:
   - `create_recent_repos_section()`: Nueva sección
   - `create_recent_repo_item()`: Botones de repo
   - `refresh_recent_repos()`: Actualizar vista
   - Nueva señal: `open_recent_repo`

4. **`ui/repository_tab.py`**:
   - Gestión de avatares con QNetworkAccessManager
   - `get_avatar_icon()`: Obtiene o crea avatar
   - `create_initial_avatar()`: Avatar con iniciales
   - `download_gravatar()`: Descarga asíncrona
   - `on_avatar_downloaded()`: Procesa respuesta
   - Integración con settings_manager

5. **`ui/main_window.py`**:
   - Importa y usa SettingsManager
   - Pasa settings_manager a RepositoryTab

6. **`requirements.txt`**:
   - Actualizado con dependencias de Qt Network

---

## 🚀 Uso:

1. **Repositorios recientes**:
   - Aparecen automáticamente en la pantalla de inicio
   - Click para abrir el repositorio
   - Los proyectos de Unreal se marcan con 🎮

2. **Avatares**:
   - Se muestran automáticamente en el historial
   - Iniciales si no hay Gravatar
   - Cache local para rendimiento

---

## 💾 Ubicación de datos:

```
~/.unreal-git-client/
└── settings.json
    ├── recent_repos[]
    │   ├── path
    │   ├── name
    │   └── last_accessed
```

---

## 🎯 Beneficios:

1. **Productividad**: Acceso rápido a repositorios frecuentes
2. **UX mejorada**: Identificación visual de colaboradores
3. **Profesional**: Apariencia similar a GitHub/GitLab
4. **Performance**: Cache local y descarga asíncrona
5. **Personalización**: Colores únicos por usuario

---

## 🔧 Configuración:

No requiere configuración adicional. Todo funciona automáticamente:
- Repositorios se guardan al abrirlos
- Avatares se descargan automáticamente
- Fallback a iniciales sin configuración

---

## 📊 Estadísticas:

- **Límite de repos recientes**: 10 (muestra 8)
- **Tamaño de avatar**: 48x48 píxeles
- **Colores disponibles**: 7 variaciones
- **Cache**: Permanente durante la sesión

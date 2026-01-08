# Unreal Git Client - Documentación

## Descripción General

Unreal Git Client es una aplicación de escritorio para gestionar repositorios Git, especialmente optimizada para proyectos de Unreal Engine. Proporciona una interfaz gráfica intuitiva para las operaciones más comunes de Git.

---

## Funcionalidades Principales

### 1. Gestión de Repositorios

| Función | Descripción |
|---------|-------------|
| **Abrir Repositorio** | Cargar un repositorio Git existente |
| **Clonar Repositorio** | Clonar un repositorio remoto |
| **Refrescar** | Actualizar el estado del repositorio |

### 2. Cambios y Commits

| Función | Descripción |
|---------|-------------|
| **Ver Cambios** | Lista de archivos modificados, añadidos o eliminados |
| **Seleccionar Archivos** | Marcar/desmarcar archivos para incluir en el commit |
| **Stage/Unstage** | Añadir o quitar archivos del área de staging |
| **Commit** | Guardar cambios con un mensaje descriptivo |
| **Descartar Cambios** | Revertir cambios en archivos específicos |

### 3. Sincronización

| Función | Descripción |
|---------|-------------|
| **Pull** | Descargar cambios del repositorio remoto |
| **Push** | Subir commits locales al repositorio remoto |
| **Fetch** | Obtener información del remoto sin aplicar cambios |

### 4. Ramas (Branches)

| Función | Descripción |
|---------|-------------|
| **Ver Ramas** | Lista de ramas locales y remotas |
| **Cambiar Rama** | Moverse a otra rama existente |
| **Crear Rama** | Crear una nueva rama desde el commit actual |
| **Eliminar Rama** | Borrar una rama local |
| **Gestionar Ramas** | Herramienta avanzada de gestión de ramas |

### 5. Historial de Commits

| Función | Descripción |
|---------|-------------|
| **Ver Historial** | Gráfico visual de commits |
| **Ver Diff** | Ver cambios de un commit específico |
| **Copiar Hash** | Copiar el identificador del commit |
| **Crear Rama desde Commit** | Nueva rama desde un punto específico |
| **Ir a Commit (Checkout)** | Navegar a un commit específico (detached HEAD) |
| **Reset** | Volver el repositorio a un commit anterior |
| **Revert** | Crear un nuevo commit que deshace cambios |

---

## Menú Contextual de Commits (Clic Derecho)

Al hacer clic derecho sobre un commit en el historial:

| Opción | Descripción |
|--------|-------------|
| **📌 Commit: abc1234** | Muestra el hash corto del commit seleccionado |
| **Copiar hash** | Copia el hash completo al portapapeles |
| **Crear Rama** | Crea una nueva rama desde este commit |
| **Ir a este commit** | Checkout al commit (modo detached HEAD) |
| **Volver a este commit** | Submenú con opciones de reset |
| **Revertir commit** | Crea un commit que deshace los cambios |

### Tipos de Reset

| Tipo | Efecto |
|------|--------|
| **🟢 Soft** | Vuelve al commit pero mantiene los cambios en staging |
| **🟡 Mixed** | Vuelve al commit y quita cambios del staging (pero los mantiene) |
| **🔴 Hard** | Vuelve al commit y descarta TODOS los cambios |

⚠️ **Advertencia**: Reset Hard es destructivo y no se puede deshacer fácilmente.

---

## Git LFS (Large File Storage)

### Funciones LFS

| Función | Descripción |
|---------|-------------|
| **Instalar LFS** | Inicializa Git LFS en el repositorio |
| **Rastreo LFS** | Configurar qué archivos usar con LFS |
| **Descargar archivos LFS** | Obtener archivos grandes del remoto |
| **Locks LFS** | Gestionar bloqueos de archivos |
| **Prune LFS** | Limpiar archivos LFS obsoletos |

### Detección de Archivos Grandes

- Los archivos mayores a **100MB** se detectan automáticamente
- Aparece un banner de advertencia sugiriendo añadirlos a LFS
- GitHub rechaza archivos > 100MB sin LFS

---

## Menú Contextual de Archivos (Clic Derecho)

| Opción | Descripción |
|--------|-------------|
| **Stage archivo** | Añadir archivo al área de staging |
| **Unstage archivo** | Quitar archivo del staging |
| **Descartar cambios** | Revertir cambios en el archivo |
| **Descartar seleccionados** | Descartar todos los archivos marcados |
| **Añadir a .gitignore** | Ignorar el archivo en futuros commits |
| **Añadir a LFS** | Configurar el archivo para Git LFS |

---

## Plugin de Unreal Engine

Cuando el repositorio contiene un proyecto de Unreal Engine:

| Función | Descripción |
|---------|-------------|
| **Abrir en Unreal Engine** | Abre el proyecto .uproject |
| **Cerrar Unreal Engine** | Cierra el editor si está abierto |
| **Reiniciar Unreal Engine** | Cierra y vuelve a abrir el proyecto |
| **Configurar LFS para Unreal** | Añade patrones LFS recomendados |
| **Abrir carpeta del proyecto** | Abre el explorador de archivos |
| **Información del Engine** | Ver/editar configuración del proyecto |

---

## Atajos y Consejos

### Selección de Archivos
- **Seleccionar Todo**: Marca todos los archivos para commit
- **Deseleccionar Todo**: Desmarca todos los archivos
- Los estados de selección se mantienen al refrescar

### Flujo de Trabajo Típico

1. **Ver cambios** en el panel izquierdo
2. **Seleccionar archivos** que quieres incluir
3. **Escribir mensaje** de commit (título obligatorio)
4. **Hacer commit** para guardar localmente
5. **Push** para subir al servidor

### Resolución de Problemas

| Problema | Solución |
|----------|----------|
| Repositorio bloqueado | Usar "Desbloquear repositorio" del menú |
| Push rechazado | Hacer Pull primero para sincronizar |
| Archivos > 100MB | Configurar Git LFS antes de commit |
| Terminal parpadea | Ya corregido en versión actual |

---

## Estructura del Proyecto

```
Unreal-Git-Client/
├── main.py              # Punto de entrada
├── core/
│   ├── git_manager.py   # Operaciones Git
│   ├── translations.py  # Idiomas (ES/EN)
│   ├── settings_manager.py
│   └── plugin_manager.py
├── ui/
│   ├── main_window.py   # Ventana principal
│   ├── repository_tab.py # Vista de repositorio
│   ├── commit_graph_widget.py # Gráfico de commits
│   └── ...
└── plugins/
    └── unreal_engine/   # Plugin de Unreal
```

---

## Requisitos

- **Python 3.10+**
- **Git** instalado y en PATH
- **Git LFS** (opcional, para archivos grandes)
- **PyQt6** para la interfaz gráfica

---

## Compilación

```batch
# Windows
build.bat

# O manualmente
pyinstaller UnrealGitClient.spec
```

El ejecutable se genera en `dist/GitClient.exe`

---

## Licencia

Este proyecto es de código abierto. Ver archivo LICENSE para más detalles.

# Unreal Git Client

Cliente Git visual e intuitivo diseñado para usuarios de Unreal Engine, con soporte completo para Git LFS y sistema de pestañas.

## Características

- 🎯 **Interfaz intuitiva** - Diseñado para usuarios sin experiencia en Git
- 📑 **Sistema de pestañas** - Trabaja con múltiples repositorios simultáneamente
- 🎮 **Soporte Unreal Engine** - Configuración automática para proyectos de Unreal
- 📦 **Git LFS integrado** - Manejo de archivos grandes (.uasset, .umap, etc.)
- 🌳 **Gestión de ramas** - Visualización clara de la rama actual
- 📝 **Cambios visuales** - Ver diferencias en tiempo real
- 📜 **Historial de commits** - Navega por el historial del proyecto
- 🔄 **Sincronización fácil** - Pull, Push y Fetch con un clic

## Requisitos

- Python 3.8+
- Git instalado en el sistema
- Git LFS (opcional, puede instalarse desde la aplicación)

## Instalación

1. Clonar o descargar este repositorio

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecutar la aplicación:
```bash
python main.py
```

## Uso

### Abrir un repositorio existente
1. Click en "📁 Abrir Repositorio" en la barra de herramientas
2. Selecciona la carpeta del repositorio Git
3. El repositorio se cargará en la pestaña actual

### Clonar un repositorio
1. Click en "⬇️ Clonar Repositorio"
2. Ingresa la URL del repositorio
3. Selecciona la carpeta de destino
4. Click en "Clonar"

### Hacer cambios
1. Los archivos modificados aparecerán en la lista "📝 Cambios"
2. Selecciona un archivo para ver sus diferencias
3. Click en "➕ Agregar" para preparar el archivo para commit
4. Escribe un mensaje descriptivo en "💬 Commit"
5. Click en "✅ Hacer Commit"

### Sincronizar con el servidor
- **⬇️ Pull**: Descarga los cambios del servidor
- **⬆️ Push**: Sube tus commits al servidor
- **🔍 Fetch**: Actualiza la información sin descargar archivos

### Configurar Git LFS para Unreal Engine
1. En el panel "📦 Git LFS", click en "Instalar LFS"
2. Click en "Trackear .uasset" para configurar automáticamente los tipos de archivo de Unreal
3. Usa "⬇️ LFS Pull" para descargar archivos grandes

### Trabajar con pestañas
- **➕ Nueva Pestaña**: Abre una nueva pestaña vacía
- **❌ Cerrar Pestaña**: Cierra la pestaña actual
- Las pestañas se pueden reordenar arrastrándolas
- Click en la X de cada pestaña para cerrarla

## Estructura del Proyecto

```
Unreal Git Client/
├── main.py                    # Punto de entrada
├── requirements.txt           # Dependencias
├── ui/
│   ├── __init__.py
│   ├── main_window.py        # Ventana principal con pestañas
│   ├── repository_tab.py     # Pestaña de repositorio
│   └── clone_dialog.py       # Diálogo de clonación
└── core/
    ├── __init__.py
    └── git_manager.py        # Lógica de Git
```

## Tipos de archivo de Unreal Engine soportados

El cliente configura automáticamente Git LFS para:
- `.uasset` - Assets de Unreal
- `.umap` - Mapas/Niveles
- `.ubulk` - Datos de bulk
- `.upk` - Paquetes
- `.uproject` - Archivos de proyecto
- `.uplugin` - Plugins

## Licencia

MIT License

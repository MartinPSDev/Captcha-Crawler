#!/bin/bash

echo "🚀 Instalando CAPTCHA Crawler (Versión Segura)..."
echo "================================================"

# Función para limpiar con timeout
safe_cleanup() {
    echo "🧹 Limpiando entorno virtual..."
    
    # Verificar si existe
    if [ ! -d "venv" ]; then
        echo "✅ No hay entorno virtual previo"
        return 0
    fi
    
    # Intentar matar procesos que puedan estar usando el directorio
    echo "🔧 Cerrando procesos Python..."
    killall python3 2>/dev/null || true
    sleep 2
    
    # Intentar eliminar con timeout
    echo "🗑️  Eliminando directorio venv..."
    timeout 30 rm -rf venv 2>/dev/null || {
        echo "⚠️  Limpieza normal falló, intentando método alternativo..."
        
        # Método alternativo: renombrar y eliminar en background
        if [ -d "venv" ]; then
            mv venv "venv_old_$(date +%s)" 2>/dev/null || true
            rm -rf venv_old_* &
        fi
    }
    
    # Verificar que se eliminó
    if [ -d "venv" ]; then
        echo "❌ No se pudo eliminar completamente el entorno virtual"
        echo "💡 Prueba: sudo rm -rf venv"
        return 1
    fi
    
    echo "✅ Limpieza completada"
    return 0
}

# Ejecutar limpieza segura
if ! safe_cleanup; then
    echo "❌ Error en la limpieza. Saliendo..."
    exit 1
fi

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado"
    echo "💡 Ejecuta: sudo apt update && sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# Verificar versión de Python
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
echo "✅ Python $PYTHON_VERSION detectado"

# Instalar dependencias del sistema si es necesario
if command -v apt-get &> /dev/null; then
    echo "📦 Instalando dependencias del sistema..."
    sudo apt-get update -qq
    sudo apt-get install -y python3-pip python3-venv python3-dev build-essential
fi

# Crear entorno virtual con validación
echo "📦 Creando entorno virtual..."
if ! python3 -m venv venv --prompt="captcha-crawler"; then
    echo "❌ Error creando entorno virtual"
    exit 1
fi

# Verificar creación
if [ ! -f "venv/bin/activate" ]; then
    echo "❌ Entorno virtual no se creó correctamente"
    exit 1
fi

echo "✅ Entorno virtual creado"

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Verificar activación
if [ "$VIRTUAL_ENV" = "" ]; then
    echo "❌ No se pudo activar el entorno virtual"
    exit 1
fi

echo "✅ Entorno virtual activado"

# Actualizar pip
echo "⬆️  Actualizando pip..."
pip install --upgrade pip -q

# Verificar requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt no encontrado"
    exit 1
fi

# Instalar dependencias
echo "📚 Instalando dependencias..."
pip install -r requirements.txt

# Instalar navegadores de Playwright
echo "🌐 Instalando navegadores..."
python -m playwright install chromium

# Verificación final
echo "🔍 Verificando instalación..."
python -c "
import playwright
print('✅ Playwright OK')
import httpx
print('✅ httpx OK')
print('🎉 Instalación completada exitosamente')
"

echo ""
echo "🎉 ¡Listo para usar!"
echo "==================="
echo ""
echo "Para activar el entorno:"
echo "source venv/bin/activate"
echo ""
echo "Para desactivar:"
echo "deactivate"
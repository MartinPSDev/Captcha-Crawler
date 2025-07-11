#!/bin/bash

# Instalador corregido para problemas de ensurepip
echo "🚀 Instalando CAPTCHA Crawler (Versión Corregida)..."
echo "==================================================="

# Función para limpiar con timeout
safe_cleanup() {
    echo "🧹 Limpiando entorno virtual..."
    
    if [ ! -d "venv" ]; then
        echo "✅ No hay entorno virtual previo"
        return 0
    fi
    
    killall python3 2>/dev/null || true
    sleep 1
    
    timeout 30 rm -rf venv 2>/dev/null || {
        echo "⚠️  Limpieza normal falló, usando método alternativo..."
        if [ -d "venv" ]; then
            mv venv "venv_old_$(date +%s)" 2>/dev/null || true
            rm -rf venv_old_* &
        fi
    }
    
    if [ -d "venv" ]; then
        echo "❌ No se pudo eliminar completamente el entorno virtual"
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
    exit 1
fi

# Verificar versión de Python
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
echo "✅ Python $PYTHON_VERSION detectado"

# Instalar dependencias específicas para el problema de ensurepip
if command -v apt-get &> /dev/null; then
    echo "📦 Instalando dependencias del sistema..."
    sudo apt-get update -qq
    
    # Instalar paquetes necesarios para resolver el problema de ensurepip
    sudo apt-get install -y \
        python3-pip \
        python3-venv \
        python3-dev \
        python3-setuptools \
        python3-wheel \
        build-essential \
        curl \
        wget
    
    echo "✅ Dependencias del sistema instaladas"
fi

# Crear entorno virtual SIN pip automático (evita el error de ensurepip)
echo "📦 Creando entorno virtual sin pip..."
if ! python3 -m venv venv --without-pip --prompt="captcha-crawler"; then
    echo "❌ Error creando entorno virtual sin pip"
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

# Instalar pip manualmente en el entorno virtual
echo "🔧 Instalando pip manualmente..."
curl -sS https://bootstrap.pypa.io/get-pip.py | python

# Verificar que pip esté disponible
if ! command -v pip &> /dev/null; then
    echo "❌ Pip no está disponible después de la instalación"
    exit 1
fi

echo "✅ Pip instalado correctamente"

# Actualizar pip
echo "⬆️  Actualizando pip..."
pip install --upgrade pip

# Verificar requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt no encontrado"
    exit 1
fi

# Instalar dependencias de Python
echo "📚 Instalando dependencias de Python..."
pip install -r requirements.txt

# Instalar dependencias específicas de Playwright para el sistema
echo "🔧 Instalando dependencias de Playwright..."
if command -v apt-get &> /dev/null; then
    sudo apt-get install -y \
        libnss3-dev \
        libatk-bridge2.0-dev \
        libdrm2 \
        libxkbcommon0 \
        libgtk-3-dev \
        libgbm1 \
        libasound2-dev \
        libxss1 \
        libgconf-2-4 \
        xvfb
fi

# Instalar navegadores de Playwright
echo "🌐 Instalando navegadores de Playwright..."
python -m playwright install chromium

# Verificación final
echo "🔍 Verificando instalación..."
python -c "
try:
    import playwright
    print('✅ Playwright OK')
    import httpx
    print('✅ httpx OK')
    import aiofiles
    print('✅ aiofiles OK')
    from bs4 import BeautifulSoup
    print('✅ BeautifulSoup OK')
    print('🎉 Todas las dependencias instaladas correctamente')
except ImportError as e:
    print(f'❌ Error: {e}')
    exit(1)
"

echo ""
echo "🎉 ¡Instalación completada exitosamente!"
echo "======================================="
echo ""
echo "Para usar el crawler:"
echo "1. Activa el entorno virtual:"
echo "   source venv/bin/activate"
echo ""
echo "2. Ejecuta el crawler:"
echo "   python3 captcha_crawler.py <URL>"
echo ""
echo "3. Para desactivar el entorno:"
echo "   deactivate"
echo ""
echo "📝 Ejemplos de uso:"
echo "   python3 captcha_crawler.py https://example.com"
echo "   python3 captcha_crawler.py https://example.com --visible"
echo ""
echo "🔧 En caso de problemas:"
echo "   - Reactiva el entorno: source venv/bin/activate"
echo "   - Verifica pip: pip --version"
echo "   - Lista paquetes: pip list"
#!/bin/bash

# Script de instalación mejorado para CAPTCHA Crawler
# Configuración automática en entorno Linux

set -e  # Salir si hay errores

echo "🚀 Instalando CAPTCHA Crawler..."
echo "================================="

# Función para manejar errores
handle_error() {
    echo "❌ Error: $1"
    echo "💡 Solución sugerida: $2"
    exit 1
}

# Función para verificar comando
check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

# Limpiar entorno virtual anterior si existe
if [ -d "venv" ]; then
    echo "🧹 Limpiando entorno virtual anterior..."
    rm -rf venv
fi

# Verificar si Python 3.8+ está instalado
if ! check_command python3; then
    handle_error "Python 3 no está instalado" "Ejecuta: sudo apt update && sudo apt install python3 python3-pip python3-venv"
fi

# Verificar versión de Python
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
if [ $? -ne 0 ]; then
    handle_error "No se pudo verificar la versión de Python" "Reinstala Python 3"
fi

# Verificar que la versión es compatible (3.8+)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    handle_error "Python $PYTHON_VERSION no es compatible (requiere 3.8+)" "Instala Python 3.8 o superior"
fi

echo "✅ Python $PYTHON_VERSION detectado"

# Verificar e instalar dependencias del sistema
echo "🔧 Verificando dependencias del sistema..."
if check_command apt-get; then
    echo "📦 Detectado sistema basado en Debian/Ubuntu"
    
    # Actualizar lista de paquetes
    echo "📦 Actualizando lista de paquetes..."
    sudo apt-get update
    
    # Instalar dependencias básicas de Python
    echo "📦 Instalando dependencias básicas..."
    sudo apt-get install -y python3-pip python3-venv python3-dev
    
    # Instalar dependencias del sistema para Playwright
    echo "📦 Instalando dependencias del sistema..."
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
        libxrandr2 \
        libasound2 \
        libpangocairo-1.0-0 \
        libatk1.0-0 \
        libcairo-gobject2 \
        libgtk-3-0 \
        libgdk-pixbuf2.0-0 \
        wget \
        ca-certificates \
        fonts-liberation \
        libappindicator3-1 \
        xdg-utils || echo "⚠️  Algunas dependencias opcionales no se pudieron instalar"
fi

# Verificar que python3-venv esté disponible
if ! python3 -m venv --help &> /dev/null; then
    handle_error "python3-venv no está disponible" "Instala python3-venv: sudo apt install python3-venv"
fi

# Crear entorno virtual con validación mejorada
echo "📦 Creando entorno virtual..."
if ! python3 -m venv venv --prompt="captcha-crawler"; then
    handle_error "No se pudo crear el entorno virtual" "Verifica permisos y espacio en disco"
fi

# Verificar que el entorno virtual se creó correctamente
if [ ! -f "venv/bin/activate" ]; then
    handle_error "El entorno virtual no se creó correctamente" "Elimina la carpeta venv y ejecuta el script nuevamente"
fi

echo "✅ Entorno virtual creado correctamente"

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Verificar que estamos en el entorno virtual
if [ "$VIRTUAL_ENV" = "" ]; then
    handle_error "No se pudo activar el entorno virtual" "Ejecuta manualmente: source venv/bin/activate"
fi

echo "✅ Entorno virtual activado: $VIRTUAL_ENV"

# Verificar que pip esté disponible
if ! check_command pip; then
    echo "🔧 Instalando pip en el entorno virtual..."
    python -m ensurepip --upgrade || handle_error "No se pudo instalar pip" "Reinstala Python con pip incluido"
fi

# Actualizar pip, setuptools y wheel
echo "⬆️  Actualizando herramientas de Python..."
pip install --upgrade pip setuptools wheel || echo "⚠️  No se pudieron actualizar todas las herramientas"

# Verificar que requirements.txt existe
if [ ! -f "requirements.txt" ]; then
    handle_error "requirements.txt no encontrado" "Asegúrate de que requirements.txt esté en el directorio actual"
fi

# Instalar dependencias de Python
echo "📚 Instalando dependencias de Python..."
if ! pip install -r requirements.txt; then
    echo "❌ Error instalando dependencias de Python"
    echo "💡 Intentando instalación individual de paquetes críticos..."
    
    # Instalar paquetes críticos individualmente
    pip install playwright>=1.40.0 || handle_error "No se pudo instalar Playwright" "Verifica conexión a internet"
    pip install httpx>=0.25.0 || echo "⚠️  Error instalando httpx"
    pip install aiofiles>=23.0.0 || echo "⚠️  Error instalando aiofiles"
    pip install beautifulsoup4>=4.12.0 || echo "⚠️  Error instalando beautifulsoup4"
    pip install lxml>=4.9.0 || echo "⚠️  Error instalando lxml"
    pip install Pillow>=10.0.0 || echo "⚠️  Error instalando Pillow"
    pip install coloredlogs>=15.0.0 || echo "⚠️  Error instalando coloredlogs"
    pip install requests>=2.31.0 || echo "⚠️  Error instalando requests"
fi

# Instalar dependencias específicas de Playwright
echo "🔧 Instalando dependencias específicas de Playwright..."
if check_command apt-get; then
    if ! python -m playwright install-deps; then
        echo "⚠️  Algunas dependencias del sistema no se pudieron instalar automáticamente"
        echo "💡 Continuando con la instalación..."
    fi
fi

# Instalar navegadores de Playwright
echo "🌐 Instalando navegadores de Playwright..."
if ! python -m playwright install; then
    echo "⚠️  Hubo problemas instalando algunos navegadores"
    echo "💡 Intentando instalar solo Chromium..."
    python -m playwright install chromium || echo "⚠️  No se pudo instalar Chromium"
fi

# Verificar instalación
echo "🔍 Verificando instalación..."
python -c "
import sys
print(f'✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')

try:
    import playwright
    print('✅ Playwright instalado correctamente')
except ImportError as e:
    print(f'❌ Error con Playwright: {e}')
    sys.exit(1)

try:
    import httpx
    print('✅ httpx instalado correctamente')
except ImportError:
    print('⚠️  httpx no está disponible')

try:
    import aiofiles
    print('✅ aiofiles instalado correctamente')
except ImportError:
    print('⚠️  aiofiles no está disponible')

try:
    from bs4 import BeautifulSoup
    print('✅ BeautifulSoup instalado correctamente')
except ImportError:
    print('⚠️  BeautifulSoup no está disponible')
"

# Hacer ejecutable el script principal si existe
if [ -f "captcha_crawler.py" ]; then
    chmod +x captcha_crawler.py
    echo "✅ Script principal configurado"
else
    echo "ℹ️  captcha_crawler.py no encontrado (se configurará cuando esté disponible)"
fi

echo ""
echo "🎉 ¡Instalación completada!"
echo "========================="
echo ""
echo "Para usar el crawler:"
echo "1. Activa el entorno virtual: source venv/bin/activate"
echo "2. Ejecuta: python3 captcha_crawler.py <URL>"
echo ""
echo "Ejemplos:"
echo "  python3 captcha_crawler.py https://example.com"
echo "  python3 captcha_crawler.py https://example.com --visible"
echo "  python3 captcha_crawler.py https://example.com --output results.json"
echo ""
echo "Para ver todas las opciones: python3 captcha_crawler.py --help"
echo ""
echo "📝 Los logs se guardan en: captcha_crawler.log"
echo ""
echo "🔧 Solución de problemas:"
echo "- Si hay errores de dependencias del sistema:"
echo "  sudo apt-get install -y python3-dev build-essential"
echo "- Si Playwright no funciona:"
echo "  source venv/bin/activate && python -m playwright install-deps && python -m playwright install chromium"
echo "- Para ver el estado del entorno virtual:"
echo "  source venv/bin/activate && pip list"
echo ""
echo "🔍 Diagnóstico rápido:"
echo "source venv/bin/activate && python -c 'import playwright; print(\"Todo OK\")'"
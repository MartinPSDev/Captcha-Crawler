#!/bin/bash

# Script de instalación para CAPTCHA Crawler
# Configuración automática en entorno Linux

echo "🚀 Instalando CAPTCHA Crawler..."
echo "================================="

# Verificar si Python 3.8+ está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado"
    echo "Instala Python 3.8 o superior antes de continuar"
    exit 1
fi

# Verificar versión de Python
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION detectado"

# Crear entorno virtual
echo "📦 Creando entorno virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Entorno virtual creado"
else
    echo "ℹ️  Entorno virtual ya existe"
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
echo "⬆️  Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
echo "📚 Instalando dependencias de Python..."
pip install -r requirements.txt

# Instalar navegadores de Playwright
echo "🌐 Instalando navegadores de Playwright..."
playwright install

# Instalar dependencias del sistema para Playwright (Ubuntu/Debian)
echo "🔧 Instalando dependencias del sistema..."
if command -v apt-get &> /dev/null; then
    echo "📦 Detectado sistema basado en Debian/Ubuntu"
    sudo playwright install-deps
elif command -v yum &> /dev/null; then
    echo "📦 Detectado sistema basado en RedHat/CentOS"
    echo "⚠️  Instala manualmente las dependencias del sistema para Playwright"
    echo "Consulta: https://playwright.dev/python/docs/browsers#system-requirements"
elif command -v pacman &> /dev/null; then
    echo "📦 Detectado Arch Linux"
    echo "⚠️  Instala manualmente las dependencias del sistema para Playwright"
    echo "Consulta: https://playwright.dev/python/docs/browsers#system-requirements"
else
    echo "⚠️  Sistema no reconocido. Instala manualmente las dependencias de Playwright"
fi

# Hacer ejecutable el script principal
chmod +x captcha_crawler.py

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
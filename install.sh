#!/bin/bash

# Script de instalación para CAPTCHA Crawler
# Configuración automática en entorno Linux

echo "🚀 Instalando CAPTCHA Crawler..."
echo "================================="

# Función para manejar errores
handle_error() {
    echo "❌ Error: $1"
    echo "💡 Solución sugerida: $2"
    exit 1
}

# Verificar si Python 3.8+ está instalado
if ! command -v python3 &> /dev/null; then
    handle_error "Python 3 no está instalado" "Ejecuta: sudo apt update && sudo apt install python3 python3-pip python3-venv"
fi

# Verificar versión de Python
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
if [ $? -ne 0 ]; then
    handle_error "No se pudo verificar la versión de Python" "Reinstala Python 3"
fi
echo "✅ Python $PYTHON_VERSION detectado"

# Verificar que python3-venv esté instalado
if ! python3 -m venv --help &> /dev/null; then
    echo "⚠️  python3-venv no está instalado. Instalando..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y python3-venv python3-pip
    else
        handle_error "python3-venv no está disponible" "Instala python3-venv manualmente para tu distribución"
    fi
fi

# Limpiar entorno virtual anterior si está corrupto
if [ -d "venv" ] && [ ! -f "venv/bin/activate" ]; then
    echo "🧹 Limpiando entorno virtual corrupto..."
    rm -rf venv
fi

# Crear entorno virtual
echo "📦 Creando entorno virtual..."
if [ ! -d "venv" ]; then
    if ! python3 -m venv venv; then
        handle_error "No se pudo crear el entorno virtual" "Verifica que python3-venv esté instalado: sudo apt install python3-venv"
    fi
    echo "✅ Entorno virtual creado"
else
    echo "ℹ️  Entorno virtual ya existe"
fi

# Verificar que el entorno virtual se creó correctamente
if [ ! -f "venv/bin/activate" ]; then
    handle_error "El entorno virtual no se creó correctamente" "Elimina la carpeta venv y ejecuta el script nuevamente"
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Verificar que pip esté disponible en el entorno virtual
if ! command -v pip &> /dev/null; then
    echo "🔧 Instalando pip en el entorno virtual..."
    python -m ensurepip --upgrade || handle_error "No se pudo instalar pip" "Reinstala Python con pip incluido"
fi

# Actualizar pip
echo "⬆️  Actualizando pip..."
if ! pip install --upgrade pip; then
    echo "⚠️  No se pudo actualizar pip, continuando con la versión actual..."
fi

# Instalar dependencias
echo "📚 Instalando dependencias de Python..."
if ! pip install -r requirements.txt; then
    handle_error "No se pudieron instalar las dependencias de Python" "Verifica que requirements.txt existe y es válido"
fi

# Instalar dependencias del sistema para Playwright ANTES de instalar navegadores
echo "🔧 Instalando dependencias del sistema..."
if command -v apt-get &> /dev/null; then
    echo "📦 Detectado sistema basado en Debian/Ubuntu"
    echo "📦 Instalando dependencias del sistema necesarias..."
    
    # Instalar dependencias básicas primero
    sudo apt-get update
    sudo apt-get install -y \
        libnss3-dev \
        libatk-bridge2.0-dev \
        libdrm2 \
        libxkbcommon0 \
        libgtk-3-dev \
        libgbm1 \
        libasound2-dev
    
    # Intentar instalar dependencias específicas de Playwright
    if ! sudo playwright install-deps; then
        echo "⚠️  Algunas dependencias del sistema no se pudieron instalar automáticamente"
        echo "💡 Esto es normal en algunas distribuciones. Continuando..."
    fi
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

# Instalar navegadores de Playwright
echo "🌐 Instalando navegadores de Playwright..."
if ! playwright install; then
    echo "⚠️  Hubo problemas instalando algunos navegadores de Playwright"
    echo "💡 Esto puede ser normal en sistemas no oficialmente soportados"
    echo "💡 Intentando instalar solo Chromium..."
    playwright install chromium || echo "⚠️  No se pudo instalar Chromium, pero el script puede funcionar"
fi

# Hacer ejecutable el script principal
chmod +x captcha_crawler.py

# Verificar que todo esté instalado correctamente
echo "🔍 Verificando instalación..."
if python -c "import playwright; print('✅ Playwright instalado correctamente')" 2>/dev/null; then
    echo "✅ Verificación exitosa"
else
    echo "⚠️  Advertencia: Playwright puede no estar completamente funcional"
    echo "💡 Esto puede deberse a dependencias del sistema faltantes"
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
echo "- Si hay errores de dependencias del sistema, ejecuta:"
echo "  sudo apt-get install -y libnss3-dev libatk-bridge2.0-dev libdrm2 libxkbcommon0 libgtk-3-dev libgbm1"
echo "- Si Playwright no funciona, intenta:"
echo "  source venv/bin/activate && playwright install-deps && playwright install chromium"
echo "- Para sistemas no soportados oficialmente, usa modo headless (sin --visible)"
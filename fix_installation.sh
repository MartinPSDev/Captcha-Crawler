#!/bin/bash

# Script de reparación para problemas comunes de instalación
# Ejecutar cuando install.sh falla

echo "🔧 Script de reparación para CAPTCHA Crawler"
echo "============================================"

# Función para manejar errores
handle_error() {
    echo "❌ Error: $1"
    echo "💡 Solución sugerida: $2"
    exit 1
}

# Limpiar instalación anterior
echo "🧹 Limpiando instalación anterior..."
rm -rf venv
rm -rf ~/.cache/ms-playwright

# Actualizar sistema
echo "📦 Actualizando sistema..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get upgrade -y
fi

# Instalar Python y dependencias básicas
echo "🐍 Instalando Python y dependencias básicas..."
if command -v apt-get &> /dev/null; then
    sudo apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        curl \
        wget
fi

# Verificar Python
if ! command -v python3 &> /dev/null; then
    handle_error "Python 3 no está disponible después de la instalación" "Instala Python manualmente"
fi

# Crear entorno virtual con método alternativo
echo "📦 Creando entorno virtual (método alternativo)..."
if ! python3 -m venv venv --system-site-packages; then
    echo "⚠️  Método estándar falló, intentando con virtualenv..."
    pip3 install --user virtualenv
    ~/.local/bin/virtualenv venv || handle_error "No se pudo crear entorno virtual" "Instala virtualenv manualmente"
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Instalar pip en el entorno virtual
echo "📦 Configurando pip..."
python -m ensurepip --upgrade
python -m pip install --upgrade pip setuptools wheel

# Instalar dependencias una por una
echo "📚 Instalando dependencias individualmente..."
dependencies=(
    "playwright>=1.40.0"
    "httpx>=0.25.0"
    "aiofiles>=23.0.0"
    "beautifulsoup4>=4.12.0"
    "lxml>=4.9.0"
    "Pillow>=10.0.0"
    "coloredlogs>=15.0.0"
    "requests>=2.31.0"
)

for dep in "${dependencies[@]}"; do
    echo "📦 Instalando $dep..."
    if ! pip install "$dep"; then
        echo "⚠️  No se pudo instalar $dep, continuando..."
    fi
done

# Instalar dependencias del sistema para Playwright
echo "🔧 Instalando dependencias del sistema..."
if command -v apt-get &> /dev/null; then
    # Instalar dependencias básicas del sistema
    sudo apt-get install -y \
        libnss3 \
        libnspr4 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libgtk-3-0 \
        libgbm1 \
        libasound2 \
        libxss1 \
        libgconf-2-4 \
        libxrandr2 \
        libasound2 \
        libpangocairo-1.0-0 \
        libatk1.0-0 \
        libcairo-gobject2 \
        libgtk-3-0 \
        libgdk-pixbuf2.0-0
        
    # Instalar dependencias específicas mencionadas en el error
    sudo apt-get install -y \
        libicu66 \
        libwoff1 \
        libevent-2.1-7 \
        libopus0 \
        libharfbuzz-icu0 \
        libjpeg8 \
        libwebp6 \
        libenchant-2-2 \
        libsecret-1-0 \
        libhyphen0 \
        libegl1 \
        libgudev-1.0-0 \
        libffi7 \
        libevdev2 \
        libjson-glib-1.0-0 \
        libgles2 \
        libx264-155 || echo "⚠️  Algunas dependencias específicas no están disponibles en esta distribución"
fi

# Instalar navegadores de Playwright con reintentos
echo "🌐 Instalando navegadores de Playwright..."
for attempt in 1 2 3; do
    echo "🔄 Intento $attempt de 3..."
    if playwright install chromium; then
        echo "✅ Chromium instalado exitosamente"
        break
    elif [ $attempt -eq 3 ]; then
        echo "⚠️  No se pudo instalar Chromium después de 3 intentos"
        echo "💡 El script puede funcionar en modo headless con navegadores del sistema"
    else
        echo "⚠️  Intento $attempt falló, reintentando..."
        sleep 5
    fi
done

# Verificar instalación
echo "🔍 Verificando instalación..."
if python -c "import playwright; print('✅ Playwright importado correctamente')"; then
    echo "✅ Instalación verificada exitosamente"
else
    echo "⚠️  Playwright no se pudo importar correctamente"
fi

echo ""
echo "🎉 ¡Reparación completada!"
echo "========================"
echo ""
echo "Para probar la instalación:"
echo "1. source venv/bin/activate"
echo "2. python3 captcha_crawler.py --help"
echo ""
echo "Si aún hay problemas:"
echo "- Usa modo headless: python3 captcha_crawler.py <URL> (sin --visible)"
echo "- Verifica logs en: captcha_crawler.log"
echo "- Considera usar Docker para un entorno más controlado"
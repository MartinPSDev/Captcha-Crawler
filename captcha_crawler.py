#!/usr/bin/env python3
"""
CAPTCHA Crawler - Navegador web inteligente con capacidad de superar CAPTCHAs by @M4rt1n_0x1337
"""

import asyncio
import random
import re
import time
import logging
import json
import string
import os
from typing import Optional, Dict, List, Any
from urllib.parse import urljoin, urlparse
from datetime import datetime

try:
    from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
except ImportError:
    print("Error: playwright no está instalado. Ejecuta: pip install playwright")
    print("Luego ejecuta: playwright install")
    exit(1)

try:
    import httpx
except ImportError:
    print("Error: httpx no está instalado. Ejecuta: pip install httpx")
    exit(1)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('captcha_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CaptchaCrawler:
    """Crawler inteligente con capacidad de superar CAPTCHAs
    by @M4rt1n_0x1337"""
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        self.headless = headless
        self.timeout = timeout * 1000  # Convertir a milisegundos
        self.browser = None
        self.context = None
        self.page = None
        self.visited_urls = set()
        
        # Patrones de CAPTCHA comunes
        self.captcha_patterns = [
            r'captcha',
            r'recaptcha',
            r'hcaptcha',
            r'cloudflare',
            r'bot.?detection',
            r'security.?check',
            r'verify.?human',
            r'prove.?you.?are.?human',
            r'anti.?bot',
            r'challenge'
        ]
        
        # Selectores comunes de CAPTCHA
        self.captcha_selectors = [
            'iframe[src*="recaptcha"]',
            'iframe[src*="hcaptcha"]',
            '.g-recaptcha',
            '.h-captcha',
            '#captcha',
            '.captcha',
            '[data-sitekey]',
            '.cf-challenge-form',
            '#challenge-form'
        ]
        
        logger.info("CaptchaCrawler inicializado")
    
    async def start_browser(self):
        """Inicializar el navegador Playwright"""
        try:
            self.playwright = await async_playwright().start()
            
            # Configuración del navegador para simular comportamiento humano
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                    '--disable-web-security',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-gpu'
                ]
            )
            
            # Crear contexto con configuración realista
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='es-ES',
                timezone_id='Europe/Madrid',
                geolocation={'latitude': 40.4168, 'longitude': -3.7038},  # Madrid
                permissions=['geolocation']
            )
            
            # Configurar headers adicionales
            await self.context.set_extra_http_headers({
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            
            self.page = await self.context.new_page()
            
            # Inyectar script para ocultar automatización
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['es-ES', 'es', 'en'],
                });
                
                window.chrome = {
                    runtime: {},
                };
            """)
            
            logger.info("Navegador iniciado correctamente")
            
        except Exception as e:
            logger.error(f"Error iniciando navegador: {e}")
            raise
    
    async def close_browser(self):
        """Cerrar el navegador"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            logger.info("Navegador cerrado")
        except Exception as e:
            logger.error(f"Error cerrando navegador: {e}")
    
    async def detect_captcha(self, page_content: str = None) -> bool:
        """Detectar si hay un CAPTCHA en la página"""
        try:
            if not page_content:
                page_content = await self.page.content()
            
            # Buscar patrones de texto
            content_lower = page_content.lower()
            for pattern in self.captcha_patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    logger.info(f"CAPTCHA detectado por patrón: {pattern}")
                    return True
            
            # Buscar elementos de CAPTCHA
            for selector in self.captcha_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        logger.info(f"CAPTCHA detectado por selector: {selector}")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error detectando CAPTCHA: {e}")
            return False
    
    async def handle_captcha(self, url: str) -> bool:
        """Intentar superar el CAPTCHA detectado"""
        try:
            logger.info(f"Intentando superar CAPTCHA en {url}")
            
            # Estrategia 1: Esperar y simular comportamiento humano
            await self.simulate_human_behavior()
            
            # Estrategia 2: Buscar y hacer clic en checkbox de reCAPTCHA
            recaptcha_checkbox = await self.page.query_selector('iframe[src*="recaptcha"]')
            if recaptcha_checkbox:
                logger.info("Intentando resolver reCAPTCHA")
                try:
                    # Cambiar al iframe del reCAPTCHA
                    frame = await recaptcha_checkbox.content_frame()
                    if frame:
                        checkbox = await frame.query_selector('.recaptcha-checkbox-border')
                        if checkbox:
                            await checkbox.click()
                            await asyncio.sleep(random.uniform(2, 4))
                            logger.info("Checkbox de reCAPTCHA clickeado")
                except Exception as e:
                    logger.warning(f"Error con reCAPTCHA: {e}")
            
            # Estrategia 3: Buscar hCaptcha
            hcaptcha_element = await self.page.query_selector('iframe[src*="hcaptcha"]')
            if hcaptcha_element:
                logger.info("hCaptcha detectado - requiere intervención manual")
                # hCaptcha es más difícil de automatizar
                await asyncio.sleep(5)
            
            # Estrategia 4: Cloudflare challenge
            cf_challenge = await self.page.query_selector('.cf-challenge-form')
            if cf_challenge:
                logger.info("Cloudflare challenge detectado")
                # Esperar a que Cloudflare complete automáticamente
                await asyncio.sleep(10)
                
                # Buscar botón de verificación
                verify_button = await self.page.query_selector('input[type="submit"]')
                if verify_button:
                    await verify_button.click()
                    await asyncio.sleep(5)
            
            # Verificar si el CAPTCHA fue superado
            await asyncio.sleep(3)
            if not await self.detect_captcha():
                logger.info("CAPTCHA superado exitosamente")
                return True
            else:
                logger.warning("CAPTCHA aún presente después del intento")
                return False
                
        except Exception as e:
            logger.error(f"Error manejando CAPTCHA: {e}")
            return False
    
    async def simulate_human_behavior(self):
        """Simular comportamiento humano realista"""
        try:
            # Movimientos de mouse aleatorios
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, 1800)
                y = random.randint(100, 1000)
                await self.page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.3))
            
            # Scroll aleatorio
            scroll_amount = random.randint(-500, 500)
            await self.page.mouse.wheel(0, scroll_amount)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Pausa realista
            await asyncio.sleep(random.uniform(1, 3))
            
            logger.debug("Comportamiento humano simulado")
            
        except Exception as e:
            logger.error(f"Error simulando comportamiento humano: {e}")
    
    async def navigate_to_url(self, url: str, max_retries: int = 3) -> bool:
        """Navegar a una URL con manejo de CAPTCHAs"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Navegando a {url} (intento {attempt + 1}/{max_retries})")
                
                # Simular comportamiento humano antes de navegar
                if attempt > 0:
                    await self.simulate_human_behavior()
                
                # Navegar a la URL
                response = await self.page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout
                )
                
                if not response:
                    logger.warning(f"No se recibió respuesta para {url}")
                    continue
                
                logger.info(f"Respuesta recibida: {response.status}")
                
                # Esperar a que la página se cargue
                await self.page.wait_for_load_state("load", timeout=self.timeout)
                
                # Detectar y manejar CAPTCHA
                if await self.detect_captcha():
                    logger.warning(f"CAPTCHA detectado en {url}")
                    if await self.handle_captcha(url):
                        logger.info("CAPTCHA superado, continuando")
                    else:
                        logger.error("No se pudo superar el CAPTCHA")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(random.uniform(5, 10))
                            continue
                        return False
                
                # Verificar si la página se cargó correctamente
                page_content = await self.page.content()
                if len(page_content) < 100:
                    logger.warning("Página parece estar vacía o bloqueada")
                    continue
                
                # Simular lectura de la página
                await asyncio.sleep(random.uniform(2, 5))
                
                self.visited_urls.add(url)
                logger.info(f"Navegación exitosa a {url}")
                return True
                
            except PlaywrightTimeoutError:
                logger.warning(f"Timeout navegando a {url} (intento {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(3, 7))
                    continue
            except Exception as e:
                logger.error(f"Error navegando a {url}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(2, 5))
                    continue
        
        logger.error(f"Falló la navegación a {url} después de {max_retries} intentos")
        return False
    
    async def extract_page_info(self) -> Dict[str, Any]:
        """Extraer información básica de la página actual"""
        try:
            info = {
                'url': self.page.url,
                'title': await self.page.title(),
                'timestamp': datetime.now().isoformat()
            }
            
            # Extraer enlaces
            links = await self.page.query_selector_all('a[href]')
            info['links'] = []
            for link in links[:20]:  # Limitar a 20 enlaces
                href = await link.get_attribute('href')
                text = await link.inner_text()
                if href:
                    full_url = urljoin(self.page.url, href)
                    info['links'].append({
                        'url': full_url,
                        'text': text.strip()[:100]  # Limitar texto
                    })
            
            # Extraer formularios
            forms = await self.page.query_selector_all('form')
            info['forms'] = len(forms)
            
            # Extraer scripts
            scripts = await self.page.query_selector_all('script[src]')
            info['external_scripts'] = len(scripts)
            
            logger.info(f"Información extraída: {len(info['links'])} enlaces, {info['forms']} formularios")
            return info
            
        except Exception as e:
            logger.error(f"Error extrayendo información de la página: {e}")
            return {'error': str(e)}
    
    async def crawl_url(self, url: str) -> Dict[str, Any]:
        """Función principal para crawlear una URL"""
        result = {
            'url': url,
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'captcha_detected': False,
            'captcha_solved': False
        }
        
        try:
            # Inicializar navegador si no está iniciado
            if not self.browser:
                await self.start_browser()
            
            # Navegar a la URL
            if await self.navigate_to_url(url):
                result['success'] = True
                
                # Detectar CAPTCHA final
                result['captcha_detected'] = await self.detect_captcha()
                result['captcha_solved'] = not result['captcha_detected']
                
                # Extraer información de la página
                page_info = await self.extract_page_info()
                result.update(page_info)
                
                logger.info(f"Crawl exitoso de {url}")
            else:
                result['error'] = 'Failed to navigate to URL'
                logger.error(f"Falló el crawl de {url}")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error en crawl de {url}: {e}")
        
        return result

async def main():
    """Función principal para uso desde línea de comandos"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CAPTCHA Crawler - Navegador web con capacidad de superar CAPTCHAs')
    parser.add_argument('url', help='URL a navegar')
    parser.add_argument('--headless', action='store_true', default=True, help='Ejecutar en modo headless (por defecto)')
    parser.add_argument('--visible', action='store_true', help='Ejecutar con navegador visible')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout en segundos (por defecto: 30)')
    parser.add_argument('--output', help='Archivo para guardar resultados JSON')
    
    args = parser.parse_args()
    
    # Configurar modo headless
    headless = args.headless and not args.visible
    
    crawler = CaptchaCrawler(headless=headless, timeout=args.timeout)
    
    try:
        logger.info(f"Iniciando crawl de {args.url}")
        result = await crawler.crawl_url(args.url)
        
        # Mostrar resultados
        print("\n" + "="*50)
        print("RESULTADOS DEL CRAWL")
        print("="*50)
        print(f"URL: {result['url']}")
        print(f"Éxito: {result['success']}")
        print(f"CAPTCHA detectado: {result['captcha_detected']}")
        print(f"CAPTCHA resuelto: {result['captcha_solved']}")
        
        if 'title' in result:
            print(f"Título: {result['title']}")
        if 'links' in result:
            print(f"Enlaces encontrados: {len(result['links'])}")
        if 'forms' in result:
            print(f"Formularios encontrados: {result['forms']}")
        if 'error' in result:
            print(f"Error: {result['error']}")
        
        # Guardar resultados si se especifica archivo
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nResultados guardados en: {args.output}")
        
    except KeyboardInterrupt:
        logger.info("Crawl interrumpido por el usuario")
    except Exception as e:
        logger.error(f"Error en main: {e}")
    finally:
        await crawler.close_browser()

if __name__ == "__main__":
    asyncio.run(main())
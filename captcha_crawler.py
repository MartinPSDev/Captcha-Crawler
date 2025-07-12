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
        self.timeout = timeout * 1000  
        self.browser = None
        self.context = None
        self.page = None
        self.visited_urls = set()
        self.max_pages = 50  # Máximo de páginas a visitar
        self.captcha_found = False
        self.captcha_solved = False
        
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
    
    def normalize_url(self, url: str) -> str:
        """Normalizar URL agregando protocolo si es necesario"""
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            # Agregar https por defecto
            url = 'https://' + url
        return url
    
    def is_same_domain(self, url1: str, url2: str) -> bool:
        """Verificar si dos URLs pertenecen al mismo dominio"""
        try:
            domain1 = urlparse(url1).netloc.lower()
            domain2 = urlparse(url2).netloc.lower()
            return domain1 == domain2
        except:
            return False
    
    async def interact_with_page(self) -> bool:
        """Interactuar con elementos de la página para activar posibles CAPTCHAs"""
        try:
            # Primero intentar navegación profunda en e-commerce
            if await self.deep_ecommerce_navigation():
                return True
            
            # Si no es e-commerce o no se encontró CAPTCHA, usar navegación estándar
            return await self.standard_page_interaction()
            
        except Exception as e:
            logger.error(f"Error interactuando con la página: {e}")
            return False
    
    async def deep_ecommerce_navigation(self) -> bool:
        """Navegación profunda específica para sitios de e-commerce"""
        try:
            page_content = await self.page.content()
            ecommerce_indicators = [
                'product', 'precio', 'price', 'cart', 'carrito', 'shop', 'tienda',
                'buy', 'comprar', 'add to cart', 'añadir al carrito', 'checkout'
            ]
            
            is_ecommerce = any(indicator in page_content.lower() for indicator in ecommerce_indicators)
            
            if not is_ecommerce:
                return False
            
            logger.info("Sitio de e-commerce detectado, iniciando navegación profunda")
            
            # 1. Buscar y hacer clic en tarjetas de productos
            product_selectors = [
                '.product-card', '.product-item', '.product', '.item-card',
                '[data-product]', '.card', '.listing-item', '.product-tile',
                'article[class*="product"]', 'div[class*="product"]',
                'a[href*="product"]', 'a[href*="item"]'
            ]
            
            products_clicked = 0
            for selector in product_selectors:
                try:
                    products = await self.page.query_selector_all(selector)
                    if products and products_clicked < 3:  # Máximo 3 productos
                        for product in products[:3]:
                            if await product.is_visible() and products_clicked < 3:
                                await product.scroll_into_view_if_needed()
                                await asyncio.sleep(random.uniform(1, 2))
                                
                                # Simular hover antes del clic
                                await product.hover()
                                await asyncio.sleep(random.uniform(0.5, 1))
                                
                                await product.click()
                                products_clicked += 1
                                
                                # Esperar a que cargue la página del producto
                                await asyncio.sleep(random.uniform(2, 4))
                                
                                # Verificar CAPTCHA después de cada clic
                                if await self.detect_captcha():
                                    return True
                                
                                # Simular lectura del producto
                                await self.simulate_product_reading()
                                
                                # Verificar CAPTCHA después de la interacción
                                if await self.detect_captcha():
                                    return True
                                
                                # Volver atrás
                                await self.page.go_back()
                                await asyncio.sleep(random.uniform(1, 2))
                                
                                break
                except Exception:
                    continue
            
            # 2. Buscar paginación y navegar
            await self.navigate_pagination()
            
            # 3. Interactuar con filtros si existen
            await self.interact_with_filters()
            
            return False
            
        except Exception as e:
            logger.error(f"Error en navegación profunda de e-commerce: {e}")
            return False
    
    async def simulate_product_reading(self):
        """Simular lectura de página de producto"""
        try:
            # Scroll gradual por la página del producto
            scroll_positions = [0.2, 0.4, 0.6, 0.8, 1.0]
            for position in scroll_positions:
                await self.page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {position})")
                await asyncio.sleep(random.uniform(1, 2))
            
            tab_selectors = [
                '.tab', '.tabs a', '[role="tab"]', '.product-tab',
                'a[href*="#"]', '.nav-tabs a'
            ]
            
            for selector in tab_selectors:
                try:
                    tabs = await self.page.query_selector_all(selector)
                    if tabs:
                        for tab in tabs[:2]:  # Máximo 2 tabs
                            if await tab.is_visible():
                                await tab.click()
                                await asyncio.sleep(random.uniform(1, 2))
                                break
                        break
                except Exception:
                    continue
            
            # Simular interacción con botones de cantidad o variantes
            interaction_selectors = [
                '.quantity-selector', '.size-selector', '.color-selector',
                'select[name*="quantity"]', 'select[name*="size"]',
                '.variant-selector', '.option-selector'
            ]
            
            for selector in interaction_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element and await element.is_visible():
                        await element.click()
                        await asyncio.sleep(random.uniform(0.5, 1))
                        break
                except Exception:
                    continue
                    
        except Exception as e:
            logger.error(f"Error simulando lectura de producto: {e}")
    
    async def navigate_pagination(self):
        """Navegar por páginas de resultados"""
        try:
            pagination_selectors = [
                '.pagination a', '.pager a', '.page-numbers a',
                'a[aria-label*="Next"]', 'a[aria-label*="Siguiente"]',
                '.next-page', '.page-next', '[data-page]'
            ]
            
            for selector in pagination_selectors:
                try:
                    next_buttons = await self.page.query_selector_all(selector)
                    if next_buttons:
                        for button in next_buttons:
                            button_text = await button.inner_text()
                            if any(text in button_text.lower() for text in ['next', 'siguiente', '>', '»']):
                                if await button.is_visible():
                                    await button.scroll_into_view_if_needed()
                                    await asyncio.sleep(random.uniform(1, 2))
                                    await button.click()
                                    await asyncio.sleep(random.uniform(2, 3))
                                    return
                except Exception:
                    continue
                    
        except Exception as e:
            logger.error(f"Error navegando paginación: {e}")
    
    async def interact_with_filters(self):
        """Interactuar con filtros de búsqueda"""
        try:
            filter_selectors = [
                '.filter', '.filters input', '.sidebar input[type="checkbox"]',
                '.facet input', '.search-filter', '.category-filter'
            ]
            
            filters_clicked = 0
            for selector in filter_selectors:
                try:
                    filters = await self.page.query_selector_all(selector)
                    if filters and filters_clicked < 2:  
                        for filter_elem in filters[:2]:
                            if await filter_elem.is_visible() and filters_clicked < 2:
                                await filter_elem.scroll_into_view_if_needed()
                                await asyncio.sleep(random.uniform(0.5, 1))
                                await filter_elem.click()
                                filters_clicked += 1
                                await asyncio.sleep(random.uniform(1, 2))
                                break
                except Exception:
                    continue
                    
        except Exception as e:
            logger.error(f"Error interactuando con filtros: {e}")
    
    async def deep_page_exploration(self, url: str):
        """Exploración profunda de la página actual para activar CAPTCHAs"""
        try:
            logger.info(f"Iniciando exploración profunda en: {url}")
            
            await self.comprehensive_page_scroll()
            
            captcha_found = await self.interact_with_page()
            if captcha_found:
                return
            
            await self.explore_forms()
            
            if await self.detect_captcha():
                return
            
            await self.interact_with_media()
            
            # Simular actividad de usuario prolongada
            await self.simulate_extended_user_activity()
            
            # Intentar activar contenido dinámico
            await self.trigger_dynamic_content()
            
            logger.info("Exploración profunda completada")
            
        except Exception as e:
            logger.error(f"Error en exploración profunda: {e}")
    
    async def comprehensive_page_scroll(self):
        """Scroll completo y realista de la página"""
        try:
            # Obtener altura total de la página
            page_height = await self.page.evaluate("document.body.scrollHeight")
            viewport_height = await self.page.evaluate("window.innerHeight")
            
            # Scroll gradual hacia abajo
            current_position = 0
            scroll_step = viewport_height // 3
            
            while current_position < page_height:
                await self.page.evaluate(f"window.scrollTo(0, {current_position})")
                await asyncio.sleep(random.uniform(1, 2.5))
                current_position += scroll_step
            
            # Scroll hasta el final
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(random.uniform(2, 3))
            
            # Scroll de vuelta hacia arriba (comportamiento humano)
            for position in [0.8, 0.6, 0.4, 0.2, 0]:
                await self.page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {position})")
                await asyncio.sleep(random.uniform(1, 2))
                
        except Exception as e:
            logger.error(f"Error en scroll comprensivo: {e}")
    
    async def explore_forms(self):
        """Explorar y llenar formularios para activar CAPTCHAs"""
        try:
            forms = await self.page.query_selector_all('form')
            
            for form in forms[:2]:  # Máximo 2 formularios
                try:
                    # Buscar campos de entrada
                    inputs = await form.query_selector_all('input[type="text"], input[type="email"], textarea')
                    
                    for input_field in inputs[:3]:  # Máximo 3 campos por formulario
                        if await input_field.is_visible():
                            await input_field.scroll_into_view_if_needed()
                            await asyncio.sleep(random.uniform(0.5, 1))
                            
                            # Simular escritura lenta
                            test_text = "test@example.com" if "email" in str(await input_field.get_attribute('type')) else "test text"
                            await input_field.click()
                            await asyncio.sleep(random.uniform(0.5, 1))
                            
                            for char in test_text:
                                await input_field.type(char)
                                await asyncio.sleep(random.uniform(0.1, 0.3))
                            
                            await asyncio.sleep(random.uniform(1, 2))
                            
                            # Verificar si apareció CAPTCHA
                            if await self.detect_captcha():
                                return
                                
                except Exception:
                    continue
                    
        except Exception as e:
            logger.error(f"Error explorando formularios: {e}")
    
    async def interact_with_media(self):
        """Interactuar con elementos multimedia"""
        try:
            # Buscar videos
            videos = await self.page.query_selector_all('video')
            for video in videos[:2]:
                try:
                    if await video.is_visible():
                        await video.scroll_into_view_if_needed()
                        await asyncio.sleep(random.uniform(1, 2))
                        await video.click()
                        await asyncio.sleep(random.uniform(2, 3))
                        break
                except Exception:
                    continue
            
            # Buscar iframes (pueden contener CAPTCHAs)
            iframes = await self.page.query_selector_all('iframe')
            for iframe in iframes[:3]:
                try:
                    if await iframe.is_visible():
                        await iframe.scroll_into_view_if_needed()
                        await asyncio.sleep(random.uniform(1, 2))
                        # No hacer clic en iframes, solo asegurar que estén visibles
                except Exception:
                    continue
                    
        except Exception as e:
            logger.error(f"Error interactuando con multimedia: {e}")
    
    async def simulate_extended_user_activity(self):
        """Simular actividad de usuario prolongada"""
        try:
            # Movimientos de mouse más extensos
            for _ in range(random.randint(5, 10)):
                x = random.randint(100, 1800)
                y = random.randint(100, 1000)
                await self.page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.2, 0.5))
            
            # Simular lectura (pausas más largas)
            await asyncio.sleep(random.uniform(3, 6))
            
            # Clicks aleatorios en áreas seguras
            safe_areas = [
                (200, 200), (500, 300), (800, 400), (1200, 500)
            ]
            
            for x, y in random.sample(safe_areas, 2):
                await self.page.mouse.click(x, y)
                await asyncio.sleep(random.uniform(1, 2))
                
        except Exception as e:
            logger.error(f"Error simulando actividad extendida: {e}")
    
    async def trigger_dynamic_content(self):
        """Intentar activar contenido dinámico que pueda contener CAPTCHAs"""
        try:
            # Buscar botones de "Load More", "Show More", etc.
            dynamic_triggers = [
                'button:contains("Load")', 'button:contains("More")', 'button:contains("Show")',
                'button:contains("Cargar")', 'button:contains("Más")', 'button:contains("Ver")',
                '.load-more', '.show-more', '.expand', '.toggle'
            ]
            
            for selector in dynamic_triggers:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements[:2]:
                        if await element.is_visible():
                            await element.scroll_into_view_if_needed()
                            await asyncio.sleep(random.uniform(1, 2))
                            await element.click()
                            await asyncio.sleep(random.uniform(2, 4))
                            
                            # Verificar CAPTCHA después de cada activación
                            if await self.detect_captcha():
                                return
                            break
                except Exception:
                    continue
            
            # Activar eventos de hover en elementos interactivos
            interactive_elements = await self.page.query_selector_all('a, button, .clickable, [onclick]')
            for element in random.sample(interactive_elements, min(5, len(interactive_elements))):
                try:
                    if await element.is_visible():
                        await element.hover()
                        await asyncio.sleep(random.uniform(0.5, 1))
                except Exception:
                    continue
                    
        except Exception as e:
            logger.error(f"Error activando contenido dinámico: {e}")
    
    async def standard_page_interaction(self) -> bool:
        """Interacción estándar con la página"""
        try:
            # Buscar y hacer clic en botones comunes
            button_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:contains("Siguiente")',
                'button:contains("Next")',
                'button:contains("Continuar")',
                'button:contains("Continue")',
                'button:contains("Ver más")',
                'button:contains("Load more")',
                'a:contains("Siguiente")',
                'a:contains("Next")',
                '.btn',
                '.button',
                '[role="button"]'
            ]
            
            for selector in button_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        # Hacer clic en el primer botón visible
                        for element in elements[:3]:  # Máximo 3 botones
                            if await element.is_visible():
                                await element.scroll_into_view_if_needed()
                                await asyncio.sleep(random.uniform(0.5, 1.0))
                                await element.click()
                                await asyncio.sleep(random.uniform(1, 2))
                                
                                # Verificar si apareció un CAPTCHA después del clic
                                if await self.detect_captcha():
                                    return True
                                break
                except Exception:
                    continue
            
            # Scroll por la página para cargar contenido dinámico
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
            await asyncio.sleep(1)
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            
            return False
            
        except Exception as e:
            logger.error(f"Error en interacción estándar: {e}")
            return False
    
    async def get_page_links(self, base_url: str) -> List[str]:
        """Obtener enlaces de la página actual que pertenezcan al mismo dominio"""
        try:
            links = await self.page.query_selector_all('a[href]')
            valid_links = []
            
            for link in links:
                href = await link.get_attribute('href')
                if href:
                    full_url = urljoin(self.page.url, href)
                    
                    # Filtrar enlaces válidos del mismo dominio
                    if (self.is_same_domain(full_url, base_url) and 
                        full_url not in self.visited_urls and
                        not any(ext in full_url.lower() for ext in ['.pdf', '.jpg', '.png', '.gif', '.zip', '.doc'])):
                        valid_links.append(full_url)
            
            return valid_links[:10]  # Limitar a 10 enlaces por página
            
        except Exception as e:
            logger.error(f"Error obteniendo enlaces: {e}")
            return []
    
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
                self.captcha_solved = True
                # Obtener título de la página
                try:
                    page_title = await self.page.title()
                    if not page_title:
                        page_title = "Página sin título"
                except:
                    page_title = "Título no disponible"
                
                # Crear recuadro visual de éxito
                print("\n" + "█"*80)
                print("█" + " "*78 + "█")
                print("█" + "🎉 ¡CAPTCHA SUPERADO EXITOSAMENTE! 🎉".center(78) + "█")
                print("█" + " "*78 + "█")
                print("█" + "─"*78 + "█")
                print("█" + " "*78 + "█")
                print("█" + f"🌐 SITIO: {url}".ljust(78) + "█")
                print("█" + " "*78 + "█")
                print("█" + "📄 TÍTULO DE LA PÁGINA:".ljust(78) + "█")
                # Dividir título largo en múltiples líneas si es necesario
                title_lines = [page_title[i:i+70] for i in range(0, len(page_title), 70)]
                for title_line in title_lines:
                    print("█" + f"   {title_line}".ljust(78) + "█")
                print("█" + " "*78 + "█")
                print("█" + f"⏰ TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".ljust(78) + "█")
                print("█" + " "*78 + "█")
                print("█"*80 + "\n")
                logger.info("CAPTCHA superado exitosamente - OBJETIVO COMPLETADO")
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
    
    async def crawl_site_for_captcha(self, start_url: str) -> Dict[str, Any]:
        """Navegar por el sitio automáticamente buscando CAPTCHAs"""
        start_url = self.normalize_url(start_url)
        
        result = {
            'start_url': start_url,
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'captcha_found': False,
            'captcha_solved': False,
            'pages_visited': 0,
            'visited_urls': []
        }
        
        try:
            # Inicializar navegador si no está iniciado
            if not self.browser:
                await self.start_browser()
            
            print(f"\n🚀 Iniciando búsqueda de CAPTCHAs en: {start_url}")
            print("🔍 Navegando automáticamente por el sitio...\n")
            
            # Cola de URLs por visitar
            urls_to_visit = [start_url]
            
            while urls_to_visit and len(self.visited_urls) < self.max_pages and not self.captcha_solved:
                current_url = urls_to_visit.pop(0)
                
                if current_url in self.visited_urls:
                    continue
                
                print(f"📄 Visitando página {len(self.visited_urls) + 1}: {current_url}")
                
                # Navegar a la URL actual
                if await self.navigate_to_url(current_url):
                    result['pages_visited'] += 1
                    result['visited_urls'].append(current_url)
                    
                    # Verificar si hay CAPTCHA inmediatamente
                    if await self.detect_captcha():
                        print(f"🎯 ¡CAPTCHA encontrado en: {current_url}!")
                        result['captcha_found'] = True
                        self.captcha_found = True
                        
                        # Intentar superar el CAPTCHA
                        if await self.handle_captcha(current_url):
                            result['captcha_solved'] = True
                            result['success'] = True
                            return result  # Salir inmediatamente cuando se supere el CAPTCHA
                        else:
                            print("❌ No se pudo superar el CAPTCHA, continuando búsqueda...")
                    
                    # Si no hay CAPTCHA, realizar navegación profunda
                    if not self.captcha_found:
                        print("   🔄 Realizando navegación profunda en la página...")
                        
                        # Pasar más tiempo explorando la página actual
                        await self.deep_page_exploration(current_url)
                        
                        # Verificar CAPTCHA después de la exploración profunda
                        if await self.detect_captcha():
                            print(f"🎯 ¡CAPTCHA encontrado durante exploración profunda en: {current_url}!")
                            result['captcha_found'] = True
                            self.captcha_found = True
                            
                            # Intentar superar el CAPTCHA
                            if await self.handle_captcha(current_url):
                                result['captcha_solved'] = True
                                result['success'] = True
                                return result  # Salir inmediatamente cuando se supere el CAPTCHA
                            else:
                                print("❌ No se pudo superar el CAPTCHA encontrado, continuando búsqueda...")
                    
                    # Si aún no hay CAPTCHA, obtener más enlaces para continuar navegando
                    if not self.captcha_found:
                        new_links = await self.get_page_links(start_url)
                        for link in new_links:
                            if link not in urls_to_visit and link not in self.visited_urls:
                                urls_to_visit.append(link)
                        
                        print(f"   ➡️  Encontrados {len(new_links)} enlaces adicionales")
                    
                    # Pausa más larga entre páginas para simular navegación humana
                    await asyncio.sleep(random.uniform(3, 6))
                else:
                    print(f"   ❌ Error navegando a: {current_url}")
            
            # Resultados finales
            if self.captcha_solved:
                result['success'] = True
                print(f"\n✅ Misión completada: CAPTCHA encontrado y superado")
            elif self.captcha_found:
                print(f"\n⚠️  CAPTCHA encontrado pero no superado")
            else:
                print(f"\n🔍 No se encontraron CAPTCHAs en {result['pages_visited']} páginas visitadas")
                print("💡 Esto puede significar que el sitio no tiene CAPTCHAs o están en secciones protegidas")
            
        except KeyboardInterrupt:
            print("\n⏹️  Búsqueda interrumpida por el usuario")
            result['error'] = 'Interrupted by user'
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error en crawl del sitio: {e}")
        
        return result
    
    async def crawl_url(self, url: str) -> Dict[str, Any]:
        """Función de compatibilidad - redirige al nuevo método de búsqueda"""
        return await self.crawl_site_for_captcha(url)

async def main():
    """Función principal para uso desde línea de comandos"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CAPTCHA Crawler - Navegador automático que busca y supera CAPTCHAs')
    parser.add_argument('url', help='URL inicial para comenzar la búsqueda (acepta example.com o https://example.com)')
    parser.add_argument('--headless', action='store_true', default=True, help='Ejecutar en modo headless (por defecto)')
    parser.add_argument('--visible', action='store_true', help='Ejecutar con navegador visible')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout en segundos (por defecto: 30)')
    parser.add_argument('--output', help='Archivo para guardar resultados JSON')
    parser.add_argument('--max-pages', type=int, default=50, help='Máximo número de páginas a visitar (por defecto: 50)')
    
    args = parser.parse_args()
    
    # Configurar modo headless
    headless = args.headless and not args.visible
    
    crawler = CaptchaCrawler(headless=headless, timeout=args.timeout)
    crawler.max_pages = args.max_pages
    
    try:
        logger.info(f"Iniciando crawl de {args.url}")
        result = await crawler.crawl_url(args.url)
        
        # Mostrar resultados finales
        print("\n" + "="*60)
        print("📊 RESUMEN DE LA BÚSQUEDA DE CAPTCHAS")
        print("="*60)
        print(f"🌐 URL inicial: {result['start_url']}")
        print(f"📄 Páginas visitadas: {result['pages_visited']}")
        print(f"🎯 CAPTCHA encontrado: {'✅ SÍ' if result['captcha_found'] else '❌ NO'}")
        print(f"🏆 CAPTCHA superado: {'✅ SÍ' if result['captcha_solved'] else '❌ NO'}")
        
        if result['pages_visited'] > 0:
            print(f"\n📋 URLs visitadas:")
            for i, url in enumerate(result['visited_urls'][:10], 1):  # Mostrar máximo 10
                print(f"   {i}. {url}")
            if len(result['visited_urls']) > 10:
                print(f"   ... y {len(result['visited_urls']) - 10} más")
        
        if 'error' in result:
            print(f"\n❌ Error: {result['error']}")
        
        if result['captcha_solved']:
            print("\n🎉 ¡OBJETIVO COMPLETADO! El programa encontró y superó un CAPTCHA.")
        elif result['captcha_found']:
            print("\n⚠️  Se encontró un CAPTCHA pero no se pudo superar automáticamente.")
        else:
            print("\n🔍 No se encontraron CAPTCHAs en las páginas exploradas.")
            print("💡 Sugerencias:")
            print("   - Intenta con un sitio diferente")
            print("   - Algunos CAPTCHAs aparecen solo después de ciertas acciones")
            print("   - Usa --visible para ver el navegador en acción")
        
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
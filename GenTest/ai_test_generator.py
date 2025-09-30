import os
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions

from config import Config
from ai_client import UniversalAIClient

class AILocatorFinder:
    def __init__(self):
        self.config = Config()
        self.ai_client = UniversalAIClient()
        self.driver = None
        self.debug_mode = True
        
    def setup_driver(self):
        """Настраивает браузер для анализа страницы"""
        print("🔧 Настраиваю браузер для анализа...")
        
        try:
            options = ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--log-level=3")
            
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.implicitly_wait(10)
            
            print("✅ Браузер настроен для анализа")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка настройки браузера: {e}")
            return False

    def analyze_test_scenario(self, test_scenario):
        """ШАГ 1: AI анализирует сценарий и определяет требуемые элементы"""
        print("🎯 ШАГ 1: Анализирую тестовый сценарий...")
        
        prompt = f"""
        Проанализируй тестовый сценарий и определи, какие веб-элементы потребуются для его выполнения.
        
        ТЕСТОВЫЙ СЦЕНАРИЙ:
        {test_scenario}
        
        Верни JSON в формате:
        {{
            "scenario_analysis": {{
                "description": "краткое описание что нужно сделать",
                "required_elements": [
                    {{
                        "name": "уникальное_название_элемента",
                        "description": "подробное описание элемента",
                        "element_type": "input|button|link|form|etc",
                        "priority": "high|medium|low"
                    }}
                ]
            }}
        }}
        
        Примеры названий элементов:
        - "username_field", "password_field", "login_button"
        - "search_input", "search_button" 
        - "email_input", "submit_button"
        - "navigation_menu", "product_card"
        """
        
        if self.debug_mode:
            print("\n" + "="*80)
            print("🔍 ШАГ 1: ПРОМПТ ДЛЯ АНАЛИЗА СЦЕНАРИЯ")
            print("="*80)
            print(prompt)
            print("="*80)
        
        try:
            response = self.ai_client.generate_response(
                prompt=prompt,
                system_message="Ты анализируешь тестовые сценарии и определяешь необходимые веб-элементы. Возвращай только валидный JSON.",
                max_tokens=1000
            )
            
            if self.debug_mode:
                print("\n" + "="*80)
                print("🔍 ШАГ 1: ОТВЕТ AI ПО СЦЕНАРИЮ")
                print("="*80)
                print(response)
                print("="*80)
            
            # Парсим JSON ответ
            scenario_analysis = self._parse_ai_response(response)
            return scenario_analysis
            
        except Exception as e:
            print(f"❌ Ошибка анализа сценария: {e}")
            return None

    def collect_page_info(self, url):
        """ШАГ 2: Собираем информацию о странице с помощью Selenium"""
        print("🌐 ШАГ 2: Собираю информацию о странице...")
        
        if not self.setup_driver():
            return None
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            # Ждем загрузки
            WebDriverWait(self.driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            page_info = {
                'url': url,
                'title': self.driver.title,
                'page_structure': self._get_page_structure(),
                'all_elements': self._get_all_elements(),
                'forms': self._get_forms_info(),
                'screenshot_available': True
            }
            
            print(f"✅ Информация о странице собрана: {len(page_info['all_elements'])} элементов")
            return page_info
            
        except Exception as e:
            print(f"❌ Ошибка сбора информации о странице: {e}")
            return None

    def find_locators_for_elements(self, scenario_analysis, page_info):
        """ШАГ 3: AI находит локаторы для каждого требуемого элемента"""
        print("🔍 ШАГ 3: Ищу локаторы для элементов...")
        
        required_elements = scenario_analysis.get('scenario_analysis', {}).get('required_elements', [])
        
        if not required_elements:
            print("❌ Нет элементов для поиска локаторов")
            return None
        
        locators_result = {
            'scenario_description': scenario_analysis.get('scenario_analysis', {}).get('description', ''),
            'page_info': {
                'url': page_info['url'],
                'title': page_info['title'],
                'total_elements': len(page_info['all_elements'])
            },
            'elements_with_locators': []
        }
        
        for element in required_elements:
            print(f"   🔎 Ищу локатор для: {element['name']} ({element['description']})")
            
            locator_info = self._find_single_element_locator(element, page_info['all_elements'])
            
            if locator_info and "error" not in locator_info:
                locators_result['elements_with_locators'].append({
                    'element_info': element,
                    'locator_info': locator_info
                })
                print(f"   ✅ Найдено {len(locator_info.get('locators', []))} локаторов")
            else:
                print(f"   ❌ Не удалось найти локатор для {element['name']}")
                locators_result['elements_with_locators'].append({
                    'element_info': element,
                    'locator_info': {"error": "Не удалось найти локатор"}
                })
        
        return locators_result

    def _find_single_element_locator(self, element_info, all_elements):
        """Находит локаторы для одного элемента"""
        prompt = f"""
        Найди лучшие локаторы для элемента:
        
        ОПИСАНИЕ ЭЛЕМЕНТА:
        - Название: {element_info['name']}
        - Описание: {element_info['description']} 
        - Тип: {element_info['element_type']}
        - Приоритет: {element_info['priority']}
        
        ВСЕ ЭЛЕМЕНТЫ НА СТРАНИЦЕ (первые 30):
        {json.dumps(all_elements[:30], ensure_ascii=False, indent=2)}
        
        Верни JSON в формате:
        {{
            "element_found": true/false,
            "element_description": "описание найденного элемента",
            "locators": [
                {{
                    "type": "ID|CSS|XPATH|NAME",
                    "value": "значение локатора",
                    "confidence": 0.95,
                    "explanation": "объяснение выбора"
                }}
            ],
            "reasoning": "краткое обоснование выбора"
        }}
        """
        
        if self.debug_mode:
            print(f"\n   🔍 ПРОМПТ ДЛЯ ЭЛЕМЕНТА: {element_info['name']}")
            print("   " + "="*60)
            print(f"   {prompt[:500]}..." if len(prompt) > 500 else f"   {prompt}")
            print("   " + "="*60)
        
        try:
            response = self.ai_client.generate_response(
                prompt=prompt,
                system_message="Ты находишь лучшие Selenium локаторы для веб-элементов. Возвращай только валидный JSON.",
                max_tokens=1500
            )
            
            locator_info = self._parse_ai_response(response)
            return locator_info
            
        except Exception as e:
            print(f"   ❌ Ошибка поиска локатора: {e}")
            return {"error": str(e)}

    def complete_analysis(self, test_scenario, url):
        """Полный процесс анализа: сценарий -> сбор страницы -> поиск локаторов"""
        print("🚀 Запускаю полный анализ...")
        print(f"📝 Сценарий: {test_scenario}")
        print(f"🌐 URL: {url}")
        
        # ШАГ 1: Анализ сценария
        scenario_analysis = self.analyze_test_scenario(test_scenario)
        if not scenario_analysis:
            print("❌ Не удалось проанализировать сценарий")
            return None
        
        print(f"✅ Сценарий проанализирован: {len(scenario_analysis.get('scenario_analysis', {}).get('required_elements', []))} элементов")
        
        # ШАГ 2: Сбор информации о странице
        page_info = self.collect_page_info(url)
        if not page_info:
            print("❌ Не удалось собрать информацию о странице")
            return None
        
        # ШАГ 3: Поиск локаторов
        final_result = self.find_locators_for_elements(scenario_analysis, page_info)
        
        return final_result

    def _get_page_structure(self):
        """Получает структуру страницы"""
        try:
            structure = {
                'headers': self._get_headers(),
                'main_sections': self._get_main_sections(),
            }
            return structure
        except:
            return {}

    def _get_headers(self):
        """Получает заголовки страницы"""
        headers = {}
        for tag in ['h1', 'h2', 'h3']:
            elements = self.driver.find_elements(By.TAG_NAME, tag)
            headers[tag] = [el.text for el in elements if el.text.strip()]
        return headers

    def _get_main_sections(self):
        """Получает основные секции страницы"""
        sections = []
        try:
            containers = self.driver.find_elements(By.CSS_SELECTOR, "main, section, .container, .main, .content")
            for container in containers[:5]:
                if container.is_displayed():
                    text = container.text[:200] if container.text else ""
                    sections.append({
                        'tag': container.tag_name,
                        'text_preview': text,
                    })
        except:
            pass
        return sections

    def _get_all_elements(self):
        """Получает все элементы страницы"""
        elements = []
        
        selectors = [
            "input:not([type='hidden'])",
            "button", 
            "a",
            "select",
            "textarea",
            "[onclick]",
            "[role='button']",
            "[type='submit']",
            "[type='button']",
            "form",
            "nav",
            "menu",
            "[data-testid]"
        ]
        
        for selector in selectors:
            try:
                found_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in found_elements[:20]:  # Ограничиваем количество
                    if element.is_displayed():
                        element_info = self._extract_element_info(element)
                        if element_info:
                            elements.append(element_info)
            except:
                continue
        
        return elements

    def _extract_element_info(self, element):
        """Извлекает информацию об элементе"""
        try:
            info = {
                'tag': element.tag_name,
                'text': element.text.strip() if element.text else "",
                'attributes': {}
            }
            
            attributes = ['id', 'name', 'type', 'placeholder', 'class', 'value', 'href', 'aria-label', 'data-testid', 'for']
            for attr in attributes:
                value = element.get_attribute(attr)
                if value and value.strip():
                    info['attributes'][attr] = value.strip()
            
            if not info['text'] and not info['attributes']:
                return None
                
            return info
            
        except:
            return None

    def _get_forms_info(self):
        """Получает информацию о формах"""
        forms = []
        try:
            form_elements = self.driver.find_elements(By.TAG_NAME, "form")
            for form in form_elements[:3]:
                if form.is_displayed():
                    form_info = {
                        'action': form.get_attribute('action'),
                        'method': form.get_attribute('method'),
                    }
                    forms.append(form_info)
        except:
            pass
        return forms

    def _parse_ai_response(self, response):
        """Парсит ответ AI в JSON"""
        try:
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            response = response.strip()
            
            return json.loads(response)
            
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            print(f"Ответ AI: {response}")
            return {"error": f"Invalid JSON: {e}"}

    def save_analysis_report(self, analysis_result, filename):
        """Сохраняет полный отчет анализа"""
        if not analysis_result:
            print("❌ Нечего сохранять - результат анализа пустой")
            return None
            
        os.makedirs(self.config.GENERATED_TESTS_DIR, exist_ok=True)
        filepath = os.path.join(self.config.GENERATED_TESTS_DIR, filename)
        
        report = self._create_comprehensive_report(analysis_result)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"💾 Полный отчет сохранен: {filepath}")
        return filepath

    def _create_comprehensive_report(self, analysis_result):
        """Создает комплексный отчет"""
        report = f"""# ПОЛНЫЙ ОТЧЕТ АНАЛИЗА АВТО-ТЕСТА

## 📋 Информация о тестовом сценарии
**Описание:** {analysis_result.get('scenario_description', 'Не указано')}

## 🌐 Информация о странице
- **URL:** {analysis_result['page_info']['url']}
- **Заголовок:** {analysis_result['page_info']['title']}
- **Всего элементов на странице:** {analysis_result['page_info']['total_elements']}

## 🎯 Результаты поиска локаторов

"""
        
        for item in analysis_result['elements_with_locators']:
            element_info = item['element_info']
            locator_info = item['locator_info']
            
            report += f"### 🔹 {element_info['name']}\n"
            report += f"**Описание элемента:** {element_info['description']}\n"
            report += f"**Тип:** {element_info['element_type']} | **Приоритет:** {element_info['priority']}\n\n"
            
            if "error" in locator_info:
                report += "❌ **Не удалось найти локатор**\n\n"
            else:
                report += f"**Найденный элемент:** {locator_info.get('element_description', 'Не указано')}\n"
                report += f"**Обоснование:** {locator_info.get('reasoning', 'Не указано')}\n\n"
                
                report += "**Локаторы:**\n"
                for i, locator in enumerate(locator_info.get('locators', []), 1):
                    report += f"{i}. **Тип:** `{locator['type']}`\n"
                    report += f"   **Локатор:** `{locator['value']}`\n"
                    report += f"   **Уверенность:** {locator.get('confidence', 'N/A')}\n"
                    report += f"   **Объяснение:** {locator.get('explanation', 'Не указано')}\n\n"
        
        report += "## 💻 Пример использования в коде\n\n```python\nfrom selenium import webdriver\nfrom selenium.webdriver.common.by import By\nfrom selenium.webdriver.support.ui import WebDriverWait\nfrom selenium.webdriver.support import expected_conditions as EC\n\n# Настройка драйвера\ndriver = webdriver.Chrome()\n\ntry:\n    driver.get(\"{analysis_result['page_info']['url']}\")\n    \n"
        
        for item in analysis_result['elements_with_locators']:
            element_info = item['element_info']
            locator_info = item['locator_info']
            
            if "error" not in locator_info and locator_info.get('locators'):
                best_locator = locator_info['locators'][0]
                var_name = element_info['name']
                report += f"    # {element_info['description']}\n"
                report += f"    {var_name} = WebDriverWait(driver, 10).until(\n"
                report += f"        EC.presence_of_element_located((By.{best_locator['type']}, \"{best_locator['value']}\"))\n"
                report += f"    )\n\n"
        
        report += "    # Действия с элементами...\n    \nfinally:\n    driver.quit()\n```\n"
        
        return report

    def close(self):
        """Закрывает браузер"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
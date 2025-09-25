import os
import requests
import json
import time
import subprocess
import tempfile
import shutil
from datetime import datetime
from github import Github, GithubException
from jenkins import Jenkins, JenkinsException
import logging
import sys
from llama_cpp import Llama

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GGUFModelClient:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.llm = None

    def load_model(self):
        """Загрузка GGUF модели"""
        try:
            if not os.path.exists(self.model_path):
                logger.error(f"Model file not found: {self.model_path}")
                return False

            logger.info("Loading GGUF model...")
            self.llm = Llama(
                model_path=self.model_path,
                n_threads=os.cpu_count(),
                n_ctx=8192,
                n_batch=512,
                top_k=40,
                top_p=0.9,
                repeat_penalty=1.1,
                verbose=False,
                echo=False,
                stop=["</s>"]
            )
            logger.info("GGUF model successfully loaded!")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def generate_text(self, prompt: str, max_tokens: int = 8000,
                     temperature: float = 0.7) -> str:
        """Генерация текста с помощью загруженной модели"""
        if not self.llm:
            logger.error("Model not loaded")
            return ""

        try:
            full_prompt = f"""<s> [INST] <<SYS>>
Ты - эксперт по автоматизации тестирования на Java + Selenium.
Сгенерируй полнофункциональный Java тест на основе описания сценария.
Используй Java 11+, Selenium 4+, JUnit 5, WebDriverWait.
Верни только Java код без дополнительных объяснений.
<</SYS>>

{prompt}

Верни только Java код. [/INST]"""

            output = self.llm(
                full_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )

            # Исправлено: проверка структуры ответа
            if isinstance(output, dict) and "choices" in output and output["choices"]:
                result_text = output["choices"][0].get("text", "").strip()
            else:
                logger.error("Unexpected model output format")
                return ""

            return self._clean_generated_code(result_text)

        except Exception as e:
            logger.error(f"Text generation error: {e}")
            return ""

    def _clean_generated_code(self, code: str) -> str:
        """Очистка сгенерированного кода"""
        if not code:
            return ""

        lines = code.split('\n')
        cleaned_lines = []

        for line in lines:
            if any(artifact in line for artifact in ['[INST]', '<<SYS>>', '[/INST]', '<s>', '</s>']):
                continue
            if line.strip() in ['```java', '```']:
                continue
            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines).strip()

class TestAutomationAgent:
    def __init__(self, github_token: str, jenkins_url: str,
                 jenkins_username: str, jenkins_token: str,
                 model_path: str, github_username: str,
                 scenario_repo: str, aft_repo: str):
        self.github_token = github_token
        self.github_username = github_username
        self.jenkins_url = jenkins_url
        self.jenkins_username = jenkins_username
        self.jenkins_token = jenkins_token

        # Репозитории (полные имена с username)
        self.scenario_repo_name = scenario_repo  # format: "username/scenario"
        self.aft_repo_name = aft_repo  # format: "username/AFT"

        # Инициализация модели
        self.model_client = GGUFModelClient(model_path)

        # Инициализация клиентов
        try:
            self.github_client = Github(github_token)
            # Проверяем подключение
            user = self.github_client.get_user()
            logger.info(f"Connected to GitHub as: {user.login}")
        except Exception as e:
            logger.error(f"GitHub connection failed: {e}")
            raise

        self.jenkins_client = None
        try:
            self.jenkins_client = Jenkins(
                jenkins_url,
                username=jenkins_username,
                password=jenkins_token,
                timeout=30  # Увеличиваем таймаут
            )
            # Простая проверка
            self.jenkins_client.get_version()
            logger.info(f"Connected to Jenkins version: {self.jenkins_client.get_version()}")
        except Exception as e:
            logger.warning(f"Jenkins connection failed: {e}")
            logger.warning("Jenkins operations will be skipped")
            self.jenkins_client = None

        # Для отслеживания изменений
        self.last_checked = datetime.now()
        self.processed_files = set()

        # Загрузка модели
        if not self.model_client.load_model():
            logger.warning("Failed to load model, using fallback mode")

    def scan_scenario_repository(self):
        """Сканирование репозитория сценариев на изменения"""
        try:
            logger.info(f"Scanning repository: {self.scenario_repo_name}")
            repo = self.github_client.get_repo(self.scenario_repo_name)

            # Получаем все файлы в репозитории
            contents = repo.get_contents("")
            txt_files = []

            for content in contents:
                if content.type == "file" and content.name.endswith('.txt'):
                    txt_files.append(content.name)
                elif content.type == "dir":
                    # Рекурсивно проверяем поддиректории
                    sub_contents = repo.get_contents(content.path)
                    for sub_content in sub_contents:
                        if sub_content.type == "file" and sub_content.name.endswith('.txt'):
                            txt_files.append(sub_content.path)

            logger.info(f"Found text files: {txt_files}")
            return set(txt_files)

        except GithubException as e:
            logger.error(f"Ошибка при сканировании репозитория {self.scenario_repo_name}: {e}")
            # Проверяем существование репозитория
            try:
                self.github_client.get_repo(self.scenario_repo_name)
            except GithubException as e2:
                if hasattr(e2, 'status') and e2.status == 404:
                    logger.error(f"Repository {self.scenario_repo_name} not found!")
                    logger.error("Please check:")
                    logger.error("1. Repository exists")
                    logger.error("2. You have access to it")
                    logger.error("3. Format is 'username/repository-name'")
                else:
                    logger.error(f"GitHub error: {e2}")
            return set()

    def download_scenario_file(self, filename):
        """Скачивание файла сценария"""
        try:
            repo = self.github_client.get_repo(self.scenario_repo_name)
            file_content = repo.get_contents(filename).decoded_content.decode('utf-8')

            # Сохраняем временную копию
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, filename)

            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)

            return file_path, file_content

        except GithubException as e:
            logger.error(f"Ошибка при скачивании файла {filename}: {e}")
            return None, None

    def generate_java_test_code(self, scenario_content, filename):
        """Генерация Java кода теста с помощью GGUF модели"""
        test_name = os.path.splitext(os.path.basename(filename))[0].replace(' ', '_').replace('-', '_')
        prompt = f"""Описание сценария:
{scenario_content}

Требования:
- Имя класса: {test_name}Test
- Используй JUnit 5
- Добавь WebDriverWait для ожиданий
- Включи логирование шагов
- Добавь cleanup в @After метод"""

        java_code = self.model_client.generate_text(prompt)

        # Удалено создание структуры maven проекта

        if java_code and self.validate_java_code(java_code):
            logger.info(f"Сгенерирован код для {test_name}Test")
        else:
            logger.warning("Модель недоступна или сгенерировала невалидный код, используем fallback")
            java_code = self._generate_fallback_test(test_name, scenario_content)

        return java_code, f"{test_name}Test.java"

    def _generate_fallback_test(self, test_name, scenario_content):
        """Резервная генерация теста если модель недоступна"""
        return f"""package tests;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import java.time.Duration;

public class {test_name}Test {{
    private WebDriver driver;
    private WebDriverWait wait;

    @BeforeEach
    public void setUp() {{
        System.setProperty("webdriver.chrome.driver", "/path/to/chromedriver");
        driver = new ChromeDriver();
        wait = new WebDriverWait(driver, Duration.ofSeconds(10));
        driver.manage().window().maximize();
    }}

    @Test
    public void test{test_name}() {{
        // Автоматически сгенерированный тест
        // Сценарий: {scenario_content}

        // TODO: Реализовать шаги сценария
    }}

    @AfterEach
    public void tearDown() {{
        if (driver != null) {{
            driver.quit();
        }}
    }}
}}
"""

    def validate_java_code(self, java_code):
        """Валидация сгенерированного Java кода"""
        if not java_code:
            return False

        required_patterns = [
            "class", "WebDriver", "@Test",
            "import org.junit", "import org.openqa.selenium"
        ]

        return all(pattern in java_code for pattern in required_patterns)

    def push_to_aft_repository(self, java_code, java_filename):
        """Загрузка сгенерированного кода в репозиторий AFT"""
        try:
            if not self.validate_java_code(java_code):
                logger.warning(f"Сгенерированный код не прошел валидацию: {java_filename}")
                return False

            aft_repo = self.github_client.get_repo(self.aft_repo_name)
            file_path = f"src/test/java/tests/{java_filename}"

            commit_message = f"Auto-generated test: {java_filename}"

            try:
                existing_file = aft_repo.get_contents(file_path)
                aft_repo.update_file(file_path, commit_message, java_code, existing_file.sha)
                logger.info(f"Обновлен файл: {file_path}")
            except GithubException as e:
                # Исправлено: если файл не найден, создаём новый
                if hasattr(e, 'status') and e.status == 404:
                    aft_repo.create_file(file_path, commit_message, java_code)
                    logger.info(f"Создан файл: {file_path}")
                else:
                    logger.error(f"Ошибка при обновлении файла: {e}")
                    return False

            return True

        except GithubException as e:
            logger.error(f"Ошибка при загрузке в репозиторий AFT: {e}")
            if hasattr(e, 'status') and e.status == 404:
                logger.error(f"Repository {self.aft_repo_name} not found!")
            return False

    def run(self, scan_interval=300):
        """Основной цикл работы агента"""
        logger.info("Запуск агента автоматизации тестирования с GGUF моделью")

        try:
            while True:
                try:
                    changed_files = self.scan_scenario_repository()

                    if changed_files:
                        logger.info(f"Обнаружены файлы: {changed_files}")

                        for filename in changed_files:
                            if filename not in self.processed_files:
                                logger.info(f"Обработка нового файла: {filename}")
                                success = self.process_scenario(filename)
                                if success:
                                    self.processed_files.add(filename)
                                    logger.info(f"Успешно обработан: {filename}")
                                else:
                                    logger.error(f"Ошибка обработки: {filename}")
                    else:
                        logger.info("Изменений не обнаружено")

                    time.sleep(scan_interval)

                except Exception as e:
                    logger.error(f"Ошибка в основном цикле: {e}")
                    time.sleep(scan_interval)

        except KeyboardInterrupt:
            logger.info("Агент остановлен пользователем")

    def process_scenario(self, filename):
        """Обработка одного сценария"""
        logger.info(f"Обработка сценария: {filename}")

        file_path, scenario_content = self.download_scenario_file(filename)
        if not scenario_content:
            return False

        java_code, java_filename = self.generate_java_test_code(scenario_content, filename)

        if not self.push_to_aft_repository(java_code, java_filename):
            return False

        # Очищаем временные файлы
        logger.info(f"+++ file_path = {file_path} , путь {os.path.dirname(file_path) if file_path else 'None'} +++")
        if file_path and os.path.exists(os.path.dirname(file_path)):
            shutil.rmtree(os.path.dirname(file_path))

        logger.info(f"Сценарий {filename} успешно обработан")
        return True

# Пример использования
if __name__ == "__main__":
    # Конфигурация - используйте переменные окружения!
    import os
    from dotenv import load_dotenv

    load_dotenv()

    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', 'your_github_token_here')
    GITHUB_USERNAME = os.getenv('GITHUB_USERNAME', 'your_username')
    JENKINS_URL = os.getenv('JENKINS_URL', 'http://localhost:8080')
    JENKINS_USERNAME = os.getenv('JENKINS_USERNAME', 'admin')
    JENKINS_TOKEN = os.getenv('JENKINS_TOKEN', 'your_jenkins_token')
    MODEL_PATH = os.getenv('MODEL_PATH', './models/yandex-gpt.gguf')

    # Имена репозиториев в формате username/repository
    SCENARIO_REPO = os.getenv('SCENARIO_REPO', f'{GITHUB_USERNAME}/scenario')
    AFT_REPO = os.getenv('AFT_REPO', f'{GITHUB_USERNAME}/AFT')

    # Проверка обязательных переменных
    if not GITHUB_TOKEN or GITHUB_TOKEN == 'your_github_token_here':
        logger.error("Please set GITHUB_TOKEN environment variable!")
        exit(1)

    try:
        agent = TestAutomationAgent(
            github_token=GITHUB_TOKEN,
            jenkins_url=JENKINS_URL,
            jenkins_username=JENKINS_USERNAME,
            jenkins_token=JENKINS_TOKEN,
            model_path=MODEL_PATH,
            github_username=GITHUB_USERNAME,
            scenario_repo=SCENARIO_REPO,
            aft_repo=AFT_REPO
        )

        agent.run(scan_interval=300)

    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        logger.error("Please check your configuration:")
        logger.error("1. GitHub token and repository names")
        logger.error("2. Jenkins URL and credentials")
        logger.error("3. Model file path")

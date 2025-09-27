#!/usr/bin/env python3
"""
Агент автоматизации тестирования v0.2
Улучшенная версия с умным отслеживанием изменений и лучшим логированием
"""

import os
import time
import tempfile
import shutil
import json
from datetime import datetime
import logging
from github import Github, GithubException
from jenkins import Jenkins
from llama_cpp import Llama

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Файл для хранения статуса файлов сценариев
SCENARIO_STATUS_FILE = "scenario_file_status.json"

class GGUFModelClient:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.llm = None

    def load_model(self):
        """Загрузка GGUF модели"""
        if not os.path.exists(self.model_path):
            logger.error(f"Model file not found: {self.model_path}")
            return False
        try:
            logger.info("🤖 Loading GGUF model...")
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
            logger.info("✅ GGUF model successfully loaded!")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            return False

    def generate_text(self, prompt: str, max_tokens: int = 8000, temperature: float = 0.7) -> str:
        """Генерация текста с помощью загруженной модели"""
        if not self.llm:
            logger.error("Model not loaded")
            return ""
        try:
            full_prompt = (
                "[INST] <<SYS>>\n"
                "Ты - эксперт по автоматизации тестирования на Java + Selenium.\n"
                "Сгенерируй полнофункциональный Java тест на основе описания сценария.\n"
                "Используй Java 11+, Selenium 4+, JUnit 5, WebDriverWait.\n"
                "Верни только Java код без дополнительных объяснений.\n"
                "<</SYS>>\n\n"
                f"{prompt}\n\n"
                "Верни только Java код. [/INST]"
            )
            output = self.llm(
                full_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            result_text = output["choices"][0]["text"].strip()
            return self._clean_generated_code(result_text)
        except Exception as e:
            logger.error(f"Text generation error: {e}")
            return ""

    def _clean_generated_code(self, code: str) -> str:
        """Очистка сгенерированного кода"""
        if not code:
            return ""
        lines = code.split('\n')
        cleaned_lines = [
            line for line in lines
            if not any(artifact in line for artifact in ['[INST]', '<<SYS>>', '[/INST]', '<s>', '</s>'])
            and line.strip() not in ['```java', '```']
        ]
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

        self.scenario_repo_name = scenario_repo
        self.aft_repo_name = aft_repo

        # Инициализация модели
        self.model_client = GGUFModelClient(model_path)

        # Инициализация клиентов
        try:
            self.github_client = Github(github_token)
            # Проверяем подключение
            user = self.github_client.get_user()
            logger.info(f"🔗 Connected to GitHub as: {user.login}")
        except Exception as e:
            logger.error(f"❌ GitHub connection failed: {e}")
            raise

        self.jenkins_client = None
        try:
            self.jenkins_client = Jenkins(
                jenkins_url,
                username=jenkins_username,
                password=jenkins_token,
                timeout=30
            )
            # Простая проверка
            self.jenkins_client.get_version()
            logger.info(f"🔗 Connected to Jenkins version: {self.jenkins_client.get_version()}")
        except Exception as e:
            logger.warning(f"⚠️ Jenkins connection failed: {e}")
            logger.warning("Jenkins operations will be skipped")
            self.jenkins_client = None

        # Для отслеживания изменений
        self.last_checked = datetime.now()
        self.processed_files = set()
        
        # Словарь для отслеживания изменений файлов (filename -> sha)
        self.file_tracking = {}

        # Загрузка статуса файлов из файла
        self._load_file_tracking_status()

        # Загрузка модели
        if not self.model_client.load_model():
            logger.warning("⚠️ Failed to load model, using fallback mode")

    def _load_file_tracking_status(self):
        """Загрузка статуса файлов из локального файла"""
        if os.path.exists(SCENARIO_STATUS_FILE):
            try:
                with open(SCENARIO_STATUS_FILE, "r", encoding="utf-8") as f:
                    self.file_tracking = json.load(f)
                logger.info(f"📂 Loaded scenario file status from {SCENARIO_STATUS_FILE}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load scenario file status: {e}")
                self.file_tracking = {}
        else:
            self.file_tracking = {}

    def _save_file_tracking_status(self):
        """Сохраняет статус файлов в локальный файл"""
        try:
            with open(SCENARIO_STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.file_tracking, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Saved scenario file status to {SCENARIO_STATUS_FILE}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to save scenario file status: {e}")

    def _is_file_changed(self, filename, current_sha):
        """Проверяет, изменился ли файл"""
        tracked_sha = self.file_tracking.get(filename)
        if tracked_sha is None:
            logger.info(f"🆕 New file detected: {filename}")
            return True
        if tracked_sha != current_sha:
            logger.info(f"🔄 File modified: {filename}")
            return True
        return False

    def _list_all_txt_files(self, repo, path=""):
        """
        Рекурсивно возвращает список всех .txt файлов в репозитории.
        """
        txt_files = []
        try:
            contents = repo.get_contents(path)
            for content in contents:
                if content.type == "file" and content.name.endswith('.txt'):
                    txt_files.append(content.path)
                elif content.type == "dir":
                    txt_files.extend(self._list_all_txt_files(repo, content.path))
        except GithubException as e:
            logger.error(f"❌ Error listing directory {path}: {e}")
        return txt_files

    def _scan_dir(self, repo, path=""):
        """
        ОСТАВЛЕНО ДЛЯ СОВМЕСТИМОСТИ, но не используется.
        """
        # Не используется, заменено на _list_all_txt_files
        return []

    def scan_scenario_repository(self):
        """Сканирование репозитория сценариев на изменения и новые файлы"""
        try:
            logger.info(f"🔍 Scanning repository: {self.scenario_repo_name}")
            repo = self.github_client.get_repo(self.scenario_repo_name)
            all_txt_files = self._list_all_txt_files(repo)
            changed_files = []
            for file_path in all_txt_files:
                try:
                    content = repo.get_contents(file_path)
                    sha = content.sha
                    # Проверяем, был ли файл изменен или новый
                    if self._is_file_changed(file_path, sha):
                        changed_files.append((file_path, sha))
                except GithubException as e:
                    logger.error(f"❌ Error getting file info for {file_path}: {e}")
            logger.info(f"📊 Found {len(changed_files)} changed/new files: {[f[0] for f in changed_files]}")
            return changed_files
        except GithubException as e:
            logger.error(f"❌ Error scanning repository {self.scenario_repo_name}: {e}")
            # Проверяем существование репозитория
            try:
                self.github_client.get_repo(self.scenario_repo_name)
            except GithubException as e2:
                if getattr(e2, 'status', None) == 404:
                    logger.error(f"Repository {self.scenario_repo_name} not found!")
                    logger.error("Please check:")
                    logger.error("1. Repository exists")
                    logger.error("2. You have access to it")
                    logger.error("3. Format is 'username/repository-name'")
                else:
                    logger.error(f"GitHub error: {e2}")
            return []

    def download_scenario_file(self, filename):
        """Скачивание файла сценария"""
        try:
            logger.info(f"⬇️ Downloading scenario file: {filename}")
            repo = self.github_client.get_repo(self.scenario_repo_name)
            file_content = repo.get_contents(filename).decoded_content.decode('utf-8')

            # Сохраняем временную копию
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, os.path.basename(filename))
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            logger.info(f"✅ File downloaded successfully: {filename}")
            return file_path, file_content
        except GithubException as e:
            logger.error(f"❌ Error downloading file {filename}: {e}")
            return None, None

    def generate_java_test_code(self, scenario_content, filename):
        """Генерация Java кода теста с помощью GGUF модели"""
        test_name = os.path.splitext(os.path.basename(filename))[0].replace(' ', '_').replace('-', '_')
        logger.info(f"🤖 Generating Java test code for: {test_name}")
        prompt = (
            f"Описание сценария:\n{scenario_content}\n\n"
            f"Требования:\n"
            f"- Имя класса: {test_name}Test\n"
            f"- Используй JUnit 5\n"
            f"- Добавь WebDriverWait для ожиданий\n"
            f"- Включи логирование шагов\n"
            f"- Добавь cleanup в @After метод"
        )
        java_code = self.model_client.generate_text(prompt)
        if java_code and self.validate_java_code(java_code):
            logger.info(f"✅ Generated valid code for {test_name}Test")
        else:
            logger.warning("⚠️ Model unavailable or generated invalid code, using fallback")
            java_code = self._generate_fallback_test(test_name, scenario_content)
        return java_code, f"{test_name}Test.java"

    def _generate_fallback_test(self, test_name, scenario_content):
        """Резервная генерация теста если модель недоступна"""
        logger.info(f"🔄 Generating fallback test for: {test_name}")
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
                logger.warning(f"⚠️ Generated code failed validation: {java_filename}")
                return False
            logger.info(f"📤 Pushing to AFT repository: {java_filename}")
            aft_repo = self.github_client.get_repo(self.aft_repo_name)
            file_path = f"src/test/java/tests/{java_filename}"
            commit_message = (
                f"Auto-update test: {java_filename}\n\n"
                f"Generated from scenario update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            try:
                existing_file = aft_repo.get_contents(file_path)
                if existing_file.decoded_content.decode('utf-8') == java_code:
                    logger.info(f"ℹ️ File {file_path} unchanged, skipping update")
                    return True
                aft_repo.update_file(file_path, commit_message, java_code, existing_file.sha)
                logger.info(f"✅ Updated file: {file_path}")
                logger.info(f"📝 Commit: {commit_message}")
            except GithubException as e:
                if getattr(e, 'status', None) == 404:
                    aft_repo.create_file(file_path, commit_message, java_code)
                    logger.info(f"✅ Created new file: {file_path}")
                    logger.info(f"📝 Commit: {commit_message}")
                else:
                    logger.error(f"❌ Error updating/creating file: {e}")
                    return False
            return True
        except GithubException as e:
            logger.error(f"❌ Error pushing to AFT repository: {e}")
            if getattr(e, 'status', None) == 404:
                logger.error(f"Repository {self.aft_repo_name} not found!")
                logger.error("Please check:")
                logger.error("1. Repository exists")
                logger.error("2. You have access to it")
                logger.error("3. Format is 'username/repository-name'")
            return False

    def run(self, scan_interval=300):
        """Основной цикл работы агента"""
        logger.info("🚀 Starting Test Automation Agent v0.2")
        logger.info(f"📂 Monitoring: {self.scenario_repo_name}")
        logger.info(f"📂 Target: {self.aft_repo_name}")
        logger.info(f"⏰ Scan interval: {scan_interval} seconds")
        try:
            while True:
                try:
                    changed_files = self.scan_scenario_repository()
                    if changed_files:
                        logger.info(f"🔄 Processing {len(changed_files)} changed files: {[f[0] for f in changed_files]}")
                        for filename, sha in changed_files:
                            logger.info(f"📝 Processing file: {filename}")
                            success = self.process_scenario(filename)
                            if success:
                                self.processed_files.add(filename)
                                # Обновляем статус файла (sha)
                                self.file_tracking[filename] = sha
                                logger.info(f"✅ Successfully processed: {filename}")
                            else:
                                logger.error(f"❌ Failed to process: {filename}")
                        # После обработки всех файлов сохраняем статус
                        self._save_file_tracking_status()
                    else:
                        logger.info("ℹ️ No changes detected")
                    logger.info(f"⏳ Waiting {scan_interval} seconds until next scan...")
                    time.sleep(scan_interval)
                except Exception as e:
                    logger.error(f"❌ Error in main loop: {e}")
                    time.sleep(scan_interval)
        except KeyboardInterrupt:
            logger.info("🛑 Agent stopped by user")

    def process_scenario(self, filename):
        """Обработка одного сценария"""
        logger.info(f"🔄 Processing scenario: {filename}")
        file_path, scenario_content = self.download_scenario_file(filename)
        if not scenario_content:
            return False
        java_code, java_filename = self.generate_java_test_code(scenario_content, filename)
        if not self.push_to_aft_repository(java_code, java_filename):
            return False

        # Очищаем временные файлы
        if file_path and os.path.exists(os.path.dirname(file_path)):
            try:
                shutil.rmtree(os.path.dirname(file_path))
                logger.info(f"🧹 Cleaned up temporary files for: {filename}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to clean up temp files: {e}")
        logger.info(f"✅ Scenario {filename} processed successfully")
        return True


# Пример использования
if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', 'your_github_token_here')
    GITHUB_USERNAME = os.getenv('GITHUB_USERNAME', 'johny19844')
    JENKINS_URL = os.getenv('JENKINS_URL', 'http://localhost:8080')
    JENKINS_USERNAME = os.getenv('JENKINS_USERNAME', 'admin')
    JENKINS_TOKEN = os.getenv('JENKINS_TOKEN', 'your_jenkins_token')
    MODEL_PATH = os.getenv('MODEL_PATH', './models/yandex-gpt.gguf')

    # Имена репозиториев в формате username/repository
    SCENARIO_REPO = os.getenv('SCENARIO_REPO', 'johny19844/scenario')
    AFT_REPO = os.getenv('AFT_REPO', 'johny19844/AFT')

    if not GITHUB_TOKEN or GITHUB_TOKEN == 'your_github_token_here':
        logger.error("❌ Please set GITHUB_TOKEN environment variable!")
        logger.error("Create a .env file with your GitHub token")
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
        logger.error(f"❌ Failed to initialize agent: {e}")
        logger.error("Please check your configuration:")
        logger.error("1. GitHub token and repository names")
        logger.error("2. Jenkins URL and credentials")
        logger.error("3. Model file path")

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
import xml.etree.ElementTree as ET

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Файл для хранения статуса файлов сценариев
SCENARIO_STATUS_FILE = "scenario_file_status.json"

class GGUFModelClient:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.llm = None

    def log_full_prompt(self, prompt: str):
        """Логирует полный промпт, который передается модели"""
        logger.info("===== FULL PROMPT TO MODEL =====\n%s\n===== END OF PROMPT =====", prompt)

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
                "Верни только Java код без дополнительных объяснений.\n"
                "<</SYS>>\n\n"
                f"{prompt}\n\n"
                "Верни только Java код. [/INST]"
            )
            # Логируем только в generate_text, не дублируем в generate_java_test_code
            self.log_full_prompt(full_prompt)
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

        # Кэш для pom.xml требований
        self._pom_requirements_cache = None
        self._pom_requirements_cache_sha = None

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

    def _get_pom_requirements(self):
        """
        Получает требования к автотесту из pom.xml репозитория AFT.
        Кэширует результат до изменения pom.xml.
        """
        try:
            aft_repo = self.github_client.get_repo(self.aft_repo_name)
            pom_content = aft_repo.get_contents("pom.xml")
            pom_sha = pom_content.sha
            if (
                self._pom_requirements_cache is not None
                and self._pom_requirements_cache_sha == pom_sha
            ):
                return self._pom_requirements_cache

            pom_xml = pom_content.decoded_content.decode("utf-8")
            requirements = []

            try:
                root = ET.fromstring(pom_xml)
                ns = {}
                if root.tag.startswith("{"):
                    ns_tag = root.tag.split("}")[0][1:]
                    ns = {'mvn': ns_tag}

                # Получаем версии из <properties>
                properties = root.find("mvn:properties", ns) if ns else root.find("properties")
                prop_versions = {}
                if properties is not None:
                    for prop in properties:
                        tag = prop.tag
                        if "}" in tag:
                            tag = tag.split("}", 1)[1]
                        prop_versions[tag] = prop.text

                # Java version
                java_version = None
                for key in ["java.version", "maven.compiler.source"]:
                    if key in prop_versions:
                        java_version = prop_versions[key]
                        break
                if java_version:
                    requirements.append(f"- Используй Java {java_version}")

                # Dependencies
                dependencies = root.find("mvn:dependencies", ns) if ns else root.find("dependencies")
                if dependencies is not None:
                    for dep in dependencies.findall("mvn:dependency", ns) if ns else dependencies.findall("dependency"):
                        groupId = dep.find("mvn:groupId", ns).text if dep.find("mvn:groupId", ns) is not None else ""
                        artifactId = dep.find("mvn:artifactId", ns).text if dep.find("mvn:artifactId", ns) is not None else ""
                        version = dep.find("mvn:version", ns).text if dep.find("mvn:version", ns) is not None else ""
                        scope = dep.find("mvn:scope", ns).text if dep.find("mvn:scope", ns) is not None else ""
                        # Если версия указана как ${...}, подставляем из prop_versions
                        if version and version.startswith("${") and version.endswith("}"):
                            prop_key = version[2:-1]
                            version = prop_versions.get(prop_key, version)
                        dep_str = f"- Зависимость: {groupId}:{artifactId}"
                        if version:
                            dep_str += f":{version}"
                        if scope:
                            dep_str += f" (scope: {scope})"
                        requirements.append(dep_str)

                # Плагины
                build = root.find("mvn:build", ns) if ns else root.find("build")
                if build is not None:
                    plugins = build.find("mvn:plugins", ns) if ns else build.find("plugins")
                    if plugins is not None:
                        for plugin in plugins.findall("mvn:plugin", ns) if ns else plugins.findall("plugin"):
                            groupId = plugin.find("mvn:groupId", ns).text if plugin.find("mvn:groupId", ns) is not None else ""
                            artifactId = plugin.find("mvn:artifactId", ns).text if plugin.find("mvn:artifactId", ns) is not None else ""
                            version = plugin.find("mvn:version", ns).text if plugin.find("mvn:version", ns) is not None else ""
                            # Если версия указана как ${...}, подставляем из prop_versions
                            if version and version.startswith("${") and version.endswith("}"):
                                prop_key = version[2:-1]
                                version = prop_versions.get(prop_key, version)
                            plugin_str = f"- Плагин: {groupId}:{artifactId}"
                            if version:
                                plugin_str += f":{version}"
                            requirements.append(plugin_str)

                # Уникальные требования (например, JUnit 5)
                junit_found = any("junit" in req.lower() for req in requirements)
                if not junit_found:
                    requirements.append("- Используй JUnit 5")

                selenium_found = any("selenium" in req.lower() for req in requirements)
                if not selenium_found:
                    requirements.append("- Используй Selenium 4+")

            except Exception as e:
                logger.warning(f"⚠️ Failed to parse pom.xml: {e}")
                requirements = [
                    "- Используй JUnit 5",
                    "- Добавь WebDriverWait для ожиданий",
                    "- Включи логирование шагов",
                    "- Добавь cleanup в @After метод",
                    "- Используй Java 11+",
                    "- Selenium 4+",
                    "- Используй паттерн Page Object Model (POM)."
                ]

            self._pom_requirements_cache = requirements
            self._pom_requirements_cache_sha = pom_sha
            return requirements
        except Exception as e:
            logger.warning(f"⚠️ Failed to get pom.xml from AFT repo: {e}")
            return [
                "- Используй JUnit 5",
                "- Добавь WebDriverWait для ожиданий",
                "- Включи логирование шагов",
                "- Добавь cleanup в @After метод",
                "- Используй Java 11+",
                "- Selenium 4+",
                "- Используй паттерн Page Object Model (POM)."
            ]

    def generate_java_test_code(self, scenario_content, filename):
        """Генерация Java кода теста с помощью GGUF модели"""
        test_name = os.path.splitext(os.path.basename(filename))[0].replace(' ', '_').replace('-', '_')
        logger.info(f"🤖 Generating Java test code for: {test_name}")

        # Получаем требования из pom.xml
        requirements_list = self._get_pom_requirements()
        requirements_str = "\n".join(requirements_list)

        prompt = (
            f"Описание сценария:\n{scenario_content}\n\n"
            f"Требования:\n"
            f"- Имя класса: {test_name}Test\n"
            f"{requirements_str}\n"
        )
        # Не дублируем логирование полного промпта здесь, только в generate_text
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

import os
import subprocess
import shutil
from pathlib import Path
from llama_cpp import Llama
import requests
import json

class TestProjectCreator:
    def __init__(self, model_path):
        """Инициализация с путем к GGUF модели"""
        self.model_path = model_path
        self.llm = None
        self.project_dir = "selenium-test-project"
        self.repo_url = "https://github.com/johny19844/AFT.git"

    def initialize_model(self):
        """Инициализация языковой модели"""
        try:
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=4096,
                n_threads=4,
                verbose=False
            )
            print("✅ Модель успешно загружена")
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки модели: {e}")
            return False

    def generate_with_llm(self, prompt):
        """Генерация текста с помощью LLM"""
        try:
            output = self.llm(
                prompt,
                max_tokens=2000,
                temperature=0.3,
                top_p=0.9,
                echo=False,
                stop=["```", "###", "---"]
            )
            return output['choices'][0]['text'].strip()
        except Exception as e:
            print(f"❌ Ошибка генерации: {e}")
            return None

    def create_maven_structure(self):
        """Создание структуры Maven проекта"""
        try:
            # Удаляем существующую директорию если есть
            if os.path.exists(self.project_dir):
                shutil.rmtree(self.project_dir)

            # Основная структура каталогов
            directories = [
                "src/main/java/com/example",
                "src/test/java/com/example",
                "src/test/resources",
                "src/main/resources"
            ]

            for directory in directories:
                os.makedirs(os.path.join(self.project_dir, directory), exist_ok=True)

            print("✅ Структура Maven проекта создана")
            return True
        except Exception as e:
            print(f"❌ Ошибка создания структуры: {e}")
            return False

    def generate_pom_xml(self):
        """Генерация pom.xml с помощью LLM"""
        prompt = """Создай полный pom.xml файл для Maven проекта с Java Selenium автотестами.
Включи следующие зависимости:
- Selenium WebDriver 4.15.0
- TestNG 7.8.0
- WebDriverManager 5.6.0
- Surefire plugin для запуска тестов
- Компилятор Java 11

Сделай файл готовым к использованию:```xml
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>selenium-test-project</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>"""

        pom_content = self.generate_with_llm(prompt)
        if pom_content:
            pom_path = os.path.join(self.project_dir, "pom.xml")
            with open(pom_path, 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write(pom_content)
            print("✅ pom.xml создан")
            return True
        return False

    def create_base_test_class(self):
        """Создание базового класса для тестов без использования LLM"""
        base_test_content = """package com.example;

import io.github.bonigarcia.wdm.WebDriverManager;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import java.time.Duration;

public class BaseTest {
    protected WebDriver driver;

    @BeforeMethod
    public void setUp() {
        WebDriverManager.chromedriver().setup();
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--headless=new");
        options.addArguments("--disable-gpu");
        options.addArguments("--window-size=1920,1080");
        options.addArguments("--no-sandbox");
        options.addArguments("--disable-dev-shm-usage");
        driver = new ChromeDriver(options);
        driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(10));
        driver.manage().window().maximize();
    }

    @AfterMethod
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }

    protected void navigateTo(String url) {
        driver.get(url);
    }

    protected void waitForPageLoad() {
        try {
            Thread.sleep(2000);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}"""

        try:
            test_path = os.path.join(self.project_dir, "src/test/java/com/example/BaseTest.java")
            with open(test_path, 'w', encoding='utf-8') as f:
                f.write(base_test_content)
            print("✅ BaseTest.java создан")
            return True
        except Exception as e:
            print(f"❌ Ошибка создания BaseTest: {e}")
            return False

    def generate_sample_test(self):
        """Генерация примера теста с помощью LLM"""
        prompt = """Создай пример Selenium теста на TestNG который проверяет Google поиск.
Тест должен:
- Наследоваться от BaseTest
- Искать "Selenium WebDriver" в Google
- Проверять результаты поиска
- Использовать правильные аннотации TestNG
- Включать проверки Assert

Код:```java
package com.example;

import org.openqa.selenium.By;
import org.openqa.selenium.Keys;
import org.openqa.selenium.WebElement;
import org.testng.Assert;
import org.testng.annotations.Test;

public class GoogleSearchTest extends BaseTest {"""

        test_content = self.generate_with_llm(prompt)
        if test_content:
            test_path = os.path.join(self.project_dir, "src/test/java/com/example/GoogleSearchTest.java")
            with open(test_path, 'w', encoding='utf-8') as f:
                f.write(test_content)
            print("✅ GoogleSearchTest.java создан")
            return True
        return False

    def create_config_files(self):
        """Создание конфигурационных файлов"""
        try:
            # .gitignore
            gitignore_content = """target/
*.class
*.jar
*.war
*.ear
*.zip
*.tar.gz
*.rar
*.iml
.idea/
*.log
*.tmp
*.swp
.DS_Store
.env
node_modules/
dist/
build/
*.classpath
*.project
.settings/
bin/
"""
            gitignore_path = os.path.join(self.project_dir, ".gitignore")
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write(gitignore_content)

            print("✅ .gitignore создан")
            return True
        except Exception as e:
            print(f"❌ Ошибка создания конфигурационных файлов: {e}")
            return False

    def create_readme(self):
        """Создание README файла"""
        readme_content = """# Selenium Test Project
Проект автотестов на Java + Selenium + TestNG + WebDriverManager

## 🚀 Требования
- Java 11+
- Maven 3.6+
- Chrome browser

## 📦 Установка и запуск

```bash
# Клонирование репозитория
git clone https://github.com/johny19844/AFT.git
cd AFT

# Запуск тестов
mvn clean test

Структура проекта
text
src/
└── test/
    └── java/
        └── com/
            └── example/
                ├── BaseTest.java      # Базовый класс тестов
                └── GoogleSearchTest.java # Пример теста

Конфигурация
WebDriverManager автоматически управляет драйверами
Тесты запускаются в headless режиме
Используется TestNG как фреймворк для тестирования

Пример теста
Проект содержит пример теста GoogleSearchTest который:
Открывает Google
Выполняет поиск "Selenium WebDriver"
Проверяет наличие результатов

Лицензия
MIT License"""

        try:
            readme_path = os.path.join(self.project_dir, "README.md")
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            print("✅ README.md создан")
            return True
        except Exception as e:
            print(f"❌ Ошибка создания README: {e}")
            return False

    def initialize_git(self):
        """Инициализация git репозитория"""
        try:
            # Переходим в директорию проекта
            original_dir = os.getcwd()
            os.chdir(self.project_dir)

            # Инициализируем git
            subprocess.run(["git", "init"], check=True, capture_output=True)
            subprocess.run(["git", "add", "."], check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit: Selenium test project with Java + TestNG + Selenium"],
                        check=True, capture_output=True)

            print("✅ Git репозиторий инициализирован")
            os.chdir(original_dir)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка git: {e}")
            os.chdir(original_dir)
            return False

    def push_to_github(self, github_token):
        """Пушим проект на GitHub"""
        try:
            if not os.path.exists(self.project_dir):
                print("❌ Проект не существует")
                return False

            original_dir = os.getcwd()
            os.chdir(self.project_dir)

            # Добавляем remote origin
            subprocess.run(["git", "remote", "add", "origin", self.repo_url],
                        check=True, capture_output=True)

            # Переименовываем ветку если нужно
            try:
                subprocess.run(["git", "branch", "-M", "main"],
                            check=True, capture_output=True)
            except:
                pass  # Игнорируем ошибку переименования ветки

            # Пушим на GitHub
            result = subprocess.run(["git", "push", "-u", "origin", "main"],
                                capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ Проект успешно залит на GitHub")
                os.chdir(original_dir)
                return True
            else:
                print(f"❌ Ошибка при пуше на GitHub: {result.stderr}")
                os.chdir(original_dir)
                return False

        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка при пуше на GitHub: {e}")
            os.chdir(original_dir)
            return False

    def create_project(self, github_token=None):
        """Основной метод создания проекта"""
        print("🚀 Начинаем создание проекта...")

        # Инициализируем модель
        if not self.initialize_model():
            return False

        # Создаем структуру
        if not self.create_maven_structure():
            return False

        # Генерируем файлы
        if not self.generate_pom_xml():
            return False

        if not self.create_base_test_class():
            return False

        if not self.generate_sample_test():
            return False

        if not self.create_config_files():
            return False

        if not self.create_readme():
            return False

        # Инициализируем git
        if not self.initialize_git():
            return False

        # Пушим на GitHub если предоставлен токен
        if github_token:
            # Обновляем URL с токеном для аутентификации
            auth_repo_url = self.repo_url.replace(
                "https://github.com/",
                f"https://{github_token}@github.com/"
            )
            self.repo_url = auth_repo_url

            if self.push_to_github(github_token):
                print("🎉 Проект успешно создан и размещен на GitHub!")
                return True
            else:
                print("⚠️ Проект создан, но не удалось разместить на GitHub")
                return True  # Все равно считаем успехом, так как проект создан локально
        else:
            print("📁 Проект создан локально. Для размещения на GitHub укажите токен.")
            return True
def main():
    # Укажите путь к вашей GGUF модели
    model_path = "/home/johny/ai/agent/models/yandex-gpt.gguf" # Замените на реальный путь

    # Токен GitHub (опционально)
    github_token = "" #os.getenv("GITHUB_TOKEN")  # или укажите явно

    # Проверяем наличие обязательных инструментов
    required_tools = ["git", "mvn", "java"]
    for tool in required_tools:
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"❌ Ошибка: {tool} не установлен или не доступен")
            return

    creator = TestProjectCreator(model_path)

    # Создаем проект
    success = creator.create_project(github_token)

    if success:
        print("\n" + "="*50)
        print("✅ Проект успешно создан!")
        print(f"📍 Локальная папка: {os.path.abspath(creator.project_dir)}")
        if github_token:
            print("🌐 Репозиторий: https://github.com/johny19844/AFT")
        print("📋 Для запуска тестов выполните: cd selenium-test-project && mvn clean test")
        print("="*50)
    else:
        print("\n❌ Ошибка при создании проекта")

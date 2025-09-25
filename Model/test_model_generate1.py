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
model_path = "/home/johny/ai/agent/models/yandex-gpt.gguf"  # Укажите путь к своей модели
project_dir = "selenium-test-project"

# prompt = """
# <s>[INST] Ты - эксперт по автоматизации тестирования на Java + Selenium.
# Сгенерируй полноценный Java-тест на основе описания сценария.
# Используй Java 11+, Selenium 4+, JUnit 5, WebDriverWait.
# Верни только Java-код без дополнительных объяснений.
#
# Описание сценария:
# 1. Перейти на страницу https://yandex.ru
# 2. Заполнить строку поиска значением "нейронные сети в медицине"
# 3. Нажать кнопку "найти"
# 4. Проверить релевантность результатов поиска
# 5. Закрыть браузер
#
# Требования:
# - Имя класса: YaTest
# - Используй JUnit 5
# - Добавь WebDriverWait для ожиданий
# - Включи логирование шагов
# - Добавь cleanup в @After метод
#
# Верни только Java-код. [/INST]
# """
prompt = """[INST]
Создай полный pom.xml файл для Maven проекта с Java Selenium автотестами.
Включи следующие зависимости:
- Selenium WebDriver 4+
- JUnit 5+
- Java 17+
верни только pom.xml без объяснений[/INST]
"""
llm = Llama(
                model_path=model_path,
                n_threads=os.cpu_count(),
                n_ctx=8192,
                n_batch=512,
                top_k=40,
                top_p=0.9,
                repeat_penalty=1.1,
                verbose=False,
                echo=False,
                stop=["</s>", "```", "###", "---"]  # Более общие стоп-токены
            )


# Создание структуры Maven проекта
def create_maven_structure():
    project_dir = "selenium-test-project"
    try:
        # Удаляем существующую директорию если есть
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
           # Основная структура каталогов
        directories = [
            "src/main/java/com/example",
            "src/test/java/com/example",
            "src/test/resources",
            "src/main/resources"
        ]
        for directory in directories:
            os.makedirs(os.path.join(project_dir, directory), exist_ok=True)
        print("Структура Maven проекта создана")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания структуры: {e}")
        return False

rez = create_maven_structure()

output = llm(prompt, max_tokens=8000, temperature=0.7)
pom_content = output["choices"][0]["text"].strip()
if pom_content:
    pom_path = os.path.join(project_dir, "pom.xml")
    with open(pom_path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(pom_content)
    print("pom.xml создан")

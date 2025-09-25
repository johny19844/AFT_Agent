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
                n_ctx=4096,
                n_batch=512,
                temperature=0.7,
                top_k=40,
                top_p=0.9,
                repeat_penalty=1.1,
                verbose=False
            )
            logger.info("GGUF model successfully loaded!")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def generate_text(self, prompt: str, max_tokens: int = 1500,
                    temperature: float = 0.3) -> str:
        if not self.llm:
            logger.error("Model not loaded")
            return ""

        try:
            logger.info(f"Generating with max_tokens: {max_tokens}, temp: {temperature}")

            output = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_k=40,
                top_p=0.9,
                repeat_penalty=1.1,
                # stop=["```", "// END", "package"],
                stop=["// END", "}", "*/", "```"],  # Более общие стоп-токены

                echo=True  # Включите echo для отладки
            )

            logger.info(f"Raw output: {output}")

            if "choices" in output and len(output["choices"]) > 0:
                result_text = output["choices"][0]["text"].strip()
                logger.info(f"Generated text: {result_text}")
                return result_text
            else:
                logger.error("No choices in output")
                return ""

        except Exception as e:
            logger.error(f"Text generation error: {e}")
            return ""





    # def _clean_generated_code(self, code: str) -> str:
    #     """Очистка сгенерированного кода"""
    #     if not code:
    #         return ""
    #
    #     lines = code.split('\n')
    #     cleaned_lines = []
    #
    #     for line in lines:
    #         if any(artifact in line for artifact in ['[INST]', '<<SYS>>', '[/INST]', '<s>', '</s>']):
    #             continue
    #         if line.strip() in ['```java', '```']:
    #             continue
    #         cleaned_lines.append(line)
    #
    #     return '\n'.join(cleaned_lines).strip()


# from gguf_model_client import GGUFModelClient  # Предполагаем, что у вас уже есть имплементация этого класса

# Настройки модели
model_path = "./models/yandex-gpt.gguf"  # Укажите путь к своей модели
# prompt = """
# что ты умеешь?
# # """
# prompt = """
# Ты - эксперт по автоматизации тестирования на Java + Selenium.
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
# Верни только Java-код."""


prompt = """
[INST] Ты - эксперт по автоматизации тестирования на Java + Selenium.
Сгенерируй полноценный Java-тест на основе описания сценария.
Используй Java 11+, Selenium 4+, JUnit 5, WebDriverWait.
Верни только Java-код без дополнительных объяснений.

Описание сценария:
1. Перейти на страницу https://yandex.ru
2. Заполнить строку поиска значением "нейронные сети в медицине"
3. Нажать кнопку "найти"
4. Проверить релевантность результатов поиска
5. Закрыть браузер

Требования:
- Имя класса: YaTest
- Используй JUnit 5
- Добавь WebDriverWait для ожиданий
- Включи логирование шагов
- Добавь cleanup в @After метод

Верни только Java-код. [/INST]
"""

# Инициализируем модель
model_client = GGUFModelClient(model_path=model_path)
 # Загрузка модели
if not model_client.load_model():
    logger.warning("Failed to load model, using fallback mode")

# Генерация текста
generated_text = model_client.generate_text(prompt=prompt, max_tokens=2000, temperature=0.75)

# Печать результата
print("Generated Text:")
print(generated_text)

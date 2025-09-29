import os
import platform
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Выбор модели: "openai" или "local"
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'local')
    
    # Настройки OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your-api-key-here')
    OPENAI_MODEL = "gpt-3.5-turbo"
    
    # Настройки локальной модели
    LOCAL_MODEL_PATH = os.getenv('LOCAL_MODEL_PATH', 'models/codellama-7b.q4_0.gguf')
    LOCAL_MODEL_MAX_TOKENS = 2048
    LOCAL_MODEL_TEMPERATURE = 0.1
    
    # Автоматическое определение системы
    SYSTEM = platform.system().lower()
    IS_LINUX = SYSTEM == 'linux'
    IS_WINDOWS = SYSTEM == 'windows'
    IS_MAC = SYSTEM == 'darwin'
    
    # Настройки браузера - используем chromium для Linux
    if IS_LINUX:
        BROWSER = "chromium"  # Используем chromium вместо chrome на Linux
    else:
        BROWSER = "chrome"
        
    HEADLESS = False
    
    # Таймауты
    PAGE_LOAD_TIMEOUT = 30
    ELEMENT_TIMEOUT = 10
    
    # Пути
    GENERATED_TESTS_DIR = "generated_tests"
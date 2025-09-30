from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os

def test_win6():
    """Автоматически сгенерированный тест"""
    
    print("🚀 Запуск автоматически сгенерированного теста")
    
    # Настройка браузера
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    
    try:
        # Основной код теста

        
        print("✅ Тест выполнен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка во время выполнения теста: {e}")
        try:
            driver.save_screenshot("error_screenshot.png")
            print("📸 Скриншот ошибки сохранен: error_screenshot.png")
        except:
            print("⚠️ Не удалось сохранить скриншот")
        raise
    finally:
        try:
            driver.quit()
            print("🔚 Браузер закрыт")
        except:
            print("⚠️ Не удалось корректно закрыть браузер")

if __name__ == "__main__":
    test_win6()
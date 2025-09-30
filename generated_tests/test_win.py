# Авто-тест для Windows - сгенерирован AI
# Сценарий: Открыть страницу https://www.saucedemo.com, Выполнить логин, Найти товар и добавить в корзину, Проверить обновление счетчика корзины, Проверить изменение состояния кнопки товара
# URL: https://www.saucedemo.com

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_auto_generated():
    """Авто-тест для Windows"""
    
    print("🚀 Запуск теста для Windows...")
    
    # Настройка Chrome
    driver = webdriver.Chrome()
    driver.implicitly_wait(10)
    
    try:
        # Открываем страницу
        print("🌐 Открываю страницу...")
        driver.get("https://www.saucedemo.com")
        
        # Ждем загрузки
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(2)
        

        # Ввод логина
        print("📝 Ввожу логин...")
        login_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((ID, "#user-name"))
        )
        login_field.clear()
        login_field.send_keys("test_user")
        time.sleep(1)

        print("✅ Тест успешно выполнен!")
        
    except Exception as e:
        print(f"❌ Ошибка: {{e}}")
        driver.save_screenshot("windows_error.png")
        print("📸 Скриншот сохранен: windows_error.png")
        raise
        
    finally:
        driver.quit()
        print("🔚 Браузер закрыт")

if __name__ == "__main__":
    test_auto_generated()

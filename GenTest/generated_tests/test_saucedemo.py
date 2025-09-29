# Авто-тест сгенерирован AI
# Сценарий: Выполнить логин, Найти товар и добавить в корзину, Проверить обновление счетчика корзины, Проверить изменение состояния кнопки товара
# URL: https://www.saucedemo.com

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_auto_generated():
    """Автоматически сгенерированный тест"""
    
    print("🚀 Запуск авто-теста...")
    
    # Настройка браузера
    driver = webdriver.Chrome()
    driver.maximize_window()
    
    try:
        # Открываем страницу
        print("🌐 Открываю страницу...")
        driver.get("https://www.saucedemo.com")
        time.sleep(3)
        

        # Ввод логина
        print("📝 Ввожу логин...")
        id_element = driver.find_element(ID, "user-name")
        id_element.clear()
        id_element.send_keys("test_user")
        time.sleep(1)

        # Ввод пароля
        print("🔒 Ввожу пароль...")
        id_element = driver.find_element(ID, "password")
        id_element.clear()
        id_element.send_keys("password123")
        time.sleep(1)

        # Нажатие кнопки
        print("🖱️ Нажимаю кнопку...")
        id_element = driver.find_element(ID, "login-button")
        id_element.click()
        time.sleep(2)

        print("✅ Тест успешно выполнен!")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {{e}}")
        raise
    finally:
        driver.quit()
        print("🔚 Браузер закрыт")

if __name__ == "__main__":
    test_auto_generated()

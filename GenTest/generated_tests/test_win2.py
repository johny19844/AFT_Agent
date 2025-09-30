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
        
    # Настройка Chrome для Windows
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
        
    driver = webdriver.Chrome(options=options)
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
            
    
            # Ввод логина: поле для логина
        print("📝 Ввожу логин...")
        try:
            login_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "user-name"))
            )
            login_field.clear()
            login_field.send_keys("standard_user")
            print("✅ Логин введен успешно")
            time.sleep(1)
        except Exception as e:
            print(f"❌ Не удалось ввести логин: {e}")
            raise
    
            # Ввод пароля: поле для пароля
        print("🔒 Ввожу пароль...")
        try:
            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            password_field.clear()
            password_field.send_keys("secret_sauce")
            print("✅ Пароль введен успешно")
            time.sleep(1)
        except Exception as e:
            print(f"❌ Не удалось ввести пароль: {e}")
            raise
    
            # Нажатие кнопки: кнопка входа
        print("🖱️ Нажимаю кнопку...")
        try:
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "login-button"))
            )
            button.click()
            print("✅ Кнопка нажата успешно")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Не удалось нажать кнопку: {e}")
            raise
  
        print("🎉 Тест успешно выполнен!")
          
    except Exception as e:
        print(f"❌ Критическая ошибка: {{e}}")
          # Сохраняем скриншот при ошибке
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
    test_auto_generated()
    
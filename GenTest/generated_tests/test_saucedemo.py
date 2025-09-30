from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def test_saucedemo_login():
    # Настройка драйвера
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    wait = WebDriverWait(driver, 10)
    
    try:
        # Открытие страницы
        driver.get("https://www.saucedemo.com/")
        
        # Ввод логина
        username_field = wait.until(EC.presence_of_element_located((By.ID, "user-name")))
        username_field.send_keys("standard_user")
        
        # Ввод пароля
        password_field = driver.find_element(By.ID, "password")
        password_field.send_keys("secret_sauce")
        
        # Нажатие кнопки Login
        login_button = driver.find_element(By.ID, "login-button")
        login_button.click()
        
        # Проверка успешного входа
        products_title = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "title")))
        assert "Products" in products_title.text
        print("✅ Login successful!")
        
        # Дополнительная проверка URL
        assert "/inventory.html" in driver.current_url
        
    finally:
        driver.quit()

if __name__ == "__main__":
    test_saucedemo_login()
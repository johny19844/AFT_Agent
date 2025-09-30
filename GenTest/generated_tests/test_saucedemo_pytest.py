import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

@pytest.fixture
def driver():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.implicitly_wait(5)
    yield driver
    driver.quit()

def test_valid_login(driver):
    """Тест успешного входа"""
    driver.get("https://www.saucedemo.com/")
    
    # Ввод учетных данных
    driver.find_element(By.ID, "user-name").send_keys("standard_user")
    driver.find_element(By.ID, "password").send_keys("secret_sauce")
    driver.find_element(By.ID, "login-button").click()
    
    # Проверка успешного входа
    wait = WebDriverWait(driver, 10)
    title = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "title")))
    
    assert title.text == "Products"
    assert "/inventory.html" in driver.current_url

def test_invalid_login(driver):
    """Тест входа с невалидными данными"""
    driver.get("https://www.saucedemo.com/")
    
    # Ввод неверных учетных данных
    driver.find_element(By.ID, "user-name").send_keys("invalid_user")
    driver.find_element(By.ID, "password").send_keys("wrong_password")
    driver.find_element(By.ID, "login-button").click()
    
    # Проверка сообщения об ошибке
    error_message = driver.find_element(By.CSS_SELECTOR, "[data-test='error']")
    assert "Username and password do not match" in error_message.text

# Запуск: pytest test_saucedemo_pytest.py -v
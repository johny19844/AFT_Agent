from selenium import webdriver
from selenium.webdriver.common.by import By

def test_win8():
    # Устанавливаем драйвер для браузера
    driver = webdriver.Chrome()
    
    # Открываем страницу
    driver.get("https://www.saucedemo.com")
    
    # Находим поле логина и вводим логин
    login_field = driver.find_element(By.ID, "user-name")
    login_field.send_keys("standard_user")
    
    # Находим поле пароля и вводим пароль
    password_field = driver.find_element(By.ID, "password")
    password_field.send_keys("secret_sauce")
    
    # Находим кнопку входа и нажимаем её
    login_button = driver.find_element(By.ID, "login-button")
    login_button.click()
    
    # Добавляем проверку, что вход выполнен (можно проверить URL или наличие элементов после входа)
    # Здесь проверяем URL, чтобы убедиться, что пользователь перенаправлен на главную страницу после входа
    assert driver.current_url == "https://www.saucedemo.com/inventory.html"
    
    # Закрываем драйвер
    driver.quit()
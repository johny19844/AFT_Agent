import requests
from jenkins import Jenkins
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_jenkins_detailed():
    load_dotenv()

    JENKINS_URL = os.getenv('JENKINS_URL', 'http://localhost:8080')
    JENKINS_USERNAME = os.getenv('JENKINS_USERNAME', 'johny')
    JENKINS_TOKEN = os.getenv('JENKINS_TOKEN', '11a96a491331f3dd25d16caa6e5757272c')

    logger.info(f"Подробная проверка Jenkins: {JENKINS_URL}")

    # Проверка 1: Базовый HTTP доступ
    try:
        response = requests.get(JENKINS_URL, timeout=10)
        logger.info(f"✓ Jenkins HTTP доступен, статус: {response.status_code}")
    except Exception as e:
        logger.error(f"✗ HTTP ошибка: {e}")
        return False

    # Проверка 2: API без аутентификации
    try:
        response = requests.get(f"{JENKINS_URL}/api/json", timeout=10)
        if response.status_code == 200:
            logger.info("✓ API доступен без аутентификации")
            data = response.json()
            logger.info(f"Jenkins version: {data.get('jenkinsVersion', 'unknown')}")
        elif response.status_code == 403:
            logger.info("✓ API требует аутентификации (нормально)")
        else:
            logger.warning(f"API статус: {response.status_code}")
    except Exception as e:
        logger.error(f"API ошибка: {e}")

    # Проверка 3: Аутентификация с токеном
    try:
        response = requests.get(
            f"{JENKINS_URL}/api/json",
            auth=(JENKINS_USERNAME, JENKINS_TOKEN),
            timeout=10
        )
        if response.status_code == 200:
            logger.info("✓ Аутентификация с токеном успешна")
            data = response.json()
            logger.info(f"Authenticated as: {data.get('primaryView', {}).get('name', 'unknown')}")
        else:
            logger.error(f"✗ Ошибка аутентификации: {response.status_code}")
            logger.error(f"Response: {response.text[:200]}")
    except Exception as e:
        logger.error(f"Ошибка аутентификации: {e}")

    # Проверка 4: Получение CSRF crumb (если включено)
    try:
        crumb_response = requests.get(
            f"{JENKINS_URL}/crumbIssuer/api/json",
            auth=(JENKINS_USERNAME, JENKINS_TOKEN),
            timeout=10
        )
        if crumb_response.status_code == 200:
            crumb_data = crumb_response.json()
            logger.info(f"✓ CSRF crumb доступен: {crumb_data['crumbRequestField']}")
        elif crumb_response.status_code == 404:
            logger.info("✓ CSRF protection отключена")
        else:
            logger.warning(f"CSRF статус: {crumb_response.status_code}")
    except Exception as e:
        logger.error(f"CSRF ошибка: {e}")

    # Проверка 5: Python-Jenkins библиотека
    try:
        jenkins = Jenkins(JENKINS_URL, username=JENKINS_USERNAME, password=JENKINS_TOKEN)

        # Пробуем разные методы
        try:
            version = jenkins.get_version()
            logger.info(f"✓ Python-Jenkins подключение: version {version}")
        except:
            # Если get_version не работает, пробуем другой метод
            jobs = jenkins.get_jobs()
            logger.info(f"✓ Python-Jenkins подключение: найдено {len(jobs)} jobs")

        return True

    except Exception as e:
        logger.error(f"✗ Python-Jenkins ошибка: {e}")

        # Детальная диагностика
        if "403" in str(e):
            logger.error("Возможные причины 403:")
            logger.error("1. Неправильный токен")
            logger.error("2. Нет прав у пользователя")
            logger.error("3. CSRF protection включена")
        elif "401" in str(e):
            logger.error("Неверные учетные данные")
        elif "Connection refused" in str(e):
            logger.error("Jenkins не запущен или неправильный порт")

        return False

def check_jenkins_alternative():
    """Альтернативная проверка с разными параметрами"""
    load_dotenv()

    JENKINS_URL = os.getenv('JENKINS_URL', 'http://localhost:8080')
    JENKINS_USERNAME = os.getenv('JENKINS_USERNAME', 'admin')
    JENKINS_TOKEN = os.getenv('JENKINS_TOKEN', '')

    # Попробуем разные варианты аутентификации
    auth_methods = [
        ("Token", JENKINS_TOKEN),
        ("Password", "your_actual_password"),  # Замените на реальный пароль
        ("None", None)
    ]

    for auth_name, auth_value in auth_methods:
        try:
            if auth_value:
                jenkins = Jenkins(JENKINS_URL, username=JENKINS_USERNAME, password=auth_value)
            else:
                jenkins = Jenkins(JENKINS_URL)

            info = jenkins.get_info()
            logger.info(f"✓ Успех с {auth_name}: {info['jenkinsVersion']}")
            return True

        except Exception as e:
            logger.warning(f"✗ {auth_name} failed: {e}")

    return False

if __name__ == "__main__":
    logger.info("=== Детальная проверка Jenkins ===")

    if check_jenkins_detailed():
        logger.info("✓ Jenkins подключение успешно")
    else:
        logger.warning("Пробуем альтернативные методы...")
        check_jenkins_alternative()

import requests
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_crumb(jenkins_url, auth):
    """
    Получение crumb-токена для последующих запросов.
    """
    crumb_response = requests.get(f"{jenkins_url}/crumbIssuer/api/json", auth=auth)
    if crumb_response.ok:
        data = crumb_response.json()
        return {
            data['crumbRequestField']: data['crumb'],
            "Content-Type": "application/json"
        }
    else:
        logger.error("Не удалось получить crumb.")
        return {}

def get_jenkins_version(jenkins_url, auth, headers=None):
    """
    Получение версии Jenkins.
    """
    response = requests.get(f"{jenkins_url}/api/json", auth=auth, headers=headers)
    if response.ok:
        try:
            data = response.json()
            return data.get('version', 'Unknown')
        except ValueError:
            logger.error("Ошибка при разборе JSON.")
            return None
    else:
        logger.error(f"Ошибка получения версии Jenkins: {response.status_code}, {response.text}")
        return None

def main():
    # Настроечные параметры
    jenkins_url = "http://localhost:8080/"
    jenkins_username = "johny"
    jenkins_password = "1234"

    # Получаем crumb для будущих запросов
    headers = fetch_crumb(jenkins_url, (jenkins_username, jenkins_password))

    try:
        # Пробуем получить версию Jenkins
        version = get_jenkins_version(jenkins_url, (jenkins_username, jenkins_password), headers)
        if version:
            print(f"Подключено к Jenkins версия: {version}")
        else:
            logger.error("Не удалось получить версию Jenkins.")

    except Exception as e:
        logger.error(f"Произошла общая ошибка: {e}")

if __name__ == "__main__":
    main()

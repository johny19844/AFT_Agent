import requests
import json
import time
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlencode  # Добавьте этот импорт

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JenkinsManager:
    def __init__(self, jenkins_url: str, username: str, token: str):
        self.jenkins_url = jenkins_url.rstrip('/')
        self.username = username
        self.token = token
        self.session = requests.Session()
        self.session.auth = (username, token)
        self.crumb = None

    def get_crumb(self) -> Optional[str]:
        """Получение CSRF crumb для Jenkins"""
        try:
            response = self.session.get(f"{self.jenkins_url}/crumbIssuer/api/json", timeout=10)
            if response.status_code == 200:
                crumb_data = response.json()
                self.crumb = {
                    'crumb': crumb_data['crumb'],
                    'field': crumb_data['crumbRequestField']
                }
                logger.info("CSRF crumb получен")
                return self.crumb
            elif response.status_code == 404:
                logger.info("CSRF protection отключена")
                return None
            else:
                logger.warning(f"Ошибка получения crumb: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении crumb: {e}")
            return None

    def create_job(self, job_name: str, git_repo: str, test_class: str) -> bool:
        """Создание Jenkins job для запуска тестов"""
        config_xml = f"""<?xml version='1.1' encoding='UTF-8'?>
<project>
  <description>Automated test for {test_class}</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.StringParameterDefinition>
          <name>TEST_CLASS</name>
          <description>Test class to run</description>
          <defaultValue>{test_class}</defaultValue>
        </hudson.model.StringParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>GIT_BRANCH</name>
          <description>Git branch to use</description>
          <defaultValue>main</defaultValue>
        </hudson.model.StringParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <scm class="hudson.plugins.git.GitSCM">
    <configVersion>2</configVersion>
    <userRemoteConfigs>
      <hudson.plugins.git.UserRemoteConfig>
        <url>{git_repo}</url>
      </hudson.plugins.git.UserRemoteConfig>
    </userRemoteConfigs>
    <branches>
      <hudson.plugins.git.BranchSpec>
        <name>${{GIT_BRANCH}}</name>
      </hudson.plugins.git.BranchSpec>
    </branches>
    <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
    <submoduleCfg class="list"/>
    <extensions/>
  </scm>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.tasks.Maven>
      <targets>clean test -Dtest=$TEST_CLASS</targets>
      <mavenName>M3</mavenName>
      <usePrivateRepository>false</usePrivateRepository>
      <settings class="jenkins.mvn.DefaultSettingsProvider"/>
      <globalSettings class="jenkins.mvn.DefaultGlobalSettingsProvider"/>
      <injectBuildVariables>false</injectBuildVariables>
    </hudson.tasks.Maven>
  </builders>
  <publishers>
    <hudson.tasks.junit.JUnitResultArchiver>
      <testResults>target/surefire-reports/*.xml</testResults>
      <keepLongStdio>true</keepLongStdio>
      <healthScaleFactor>1.0</healthScaleFactor>
      <allowEmptyResults>false</allowEmptyResults>
    </hudson.tasks.junit.JUnitResultArchiver>
  </publishers>
  <buildWrappers/>
</project>"""

        headers = {'Content-Type': 'application/xml'}
        if self.crumb:
            headers[self.crumb['field']] = self.crumb['crumb']

        try:
            # Проверяем существование job
            check_response = self.session.get(
                f"{self.jenkins_url}/job/{job_name}/config.xml",
                headers=headers,
                timeout=10
            )

            if check_response.status_code == 200:
                # Job существует - обновляем
                response = self.session.post(
                    f"{self.jenkins_url}/job/{job_name}/config.xml",
                    data=config_xml,
                    headers=headers,
                    timeout=30
                )
                if response.status_code in [200, 201]:
                    logger.info(f"Job {job_name} обновлен")
                    return True
                else:
                    logger.error(f"Ошибка обновления job: {response.status_code}")
                    return False
            else:
                # Job не существует - создаем новый
                response = self.session.post(
                    f"{self.jenkins_url}/createItem?name={job_name}",
                    data=config_xml,
                    headers=headers,
                    timeout=30
                )
                if response.status_code in [200, 201]:
                    logger.info(f"Job {job_name} создан")
                    return True
                else:
                    logger.error(f"Ошибка создания job: {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Ошибка при создании job: {e}")
            return False

    def run_job(self, job_name: str, parameters: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Запуск Jenkins job с параметрами"""
        if parameters is None:
            parameters = {}

        # Формируем URL с параметрами
        if parameters:
            params_query = urlencode(parameters)  # Теперь urlencode определен
            url = f"{self.jenkins_url}/job/{job_name}/buildWithParameters?{params_query}"
        else:
            url = f"{self.jenkins_url}/job/{job_name}/build"

        headers = {}
        if self.crumb:
            headers[self.crumb['field']] = self.crumb['crumb']

        try:
            logger.info(f"Запуск job: {url}")
            response = self.session.post(url, headers=headers, timeout=30)

            if response.status_code in [200, 201]:
                # Анализируем заголовки для получения queue ID
                location = response.headers.get('Location', '')
                if location:
                    queue_id = location.rstrip('/').split('/')[-1]
                    logger.info(f"Job {job_name} запущен, Queue ID: {queue_id}")
                    return queue_id
                else:
                    logger.info(f"Job {job_name} запущен успешно")
                    return "success"
            else:
                logger.error(f"Ошибка запуска job: {response.status_code}")
                logger.error(f"Response text: {response.text[:200]}")
                return None

        except Exception as e:
            logger.error(f"Ошибка при запуске job: {e}")
            return None

    def get_build_number_from_queue(self, queue_id: str) -> Optional[int]:
        """Получение номера сборки из очереди"""
        try:
            response = self.session.get(
                f"{self.jenkins_url}/queue/item/{queue_id}/api/json",
                timeout=10
            )

            if response.status_code == 200:
                queue_info = response.json()
                if 'executable' in queue_info and queue_info['executable']:
                    return queue_info['executable']['number']
            return None

        except Exception as e:
            logger.error(f"Ошибка получения номера сборки: {e}")
            return None

    def get_job_status(self, job_name: str, build_number: int) -> Optional[Dict[str, Any]]:
        """Получение статуса выполнения job"""
        try:
            response = self.session.get(
                f"{self.jenkins_url}/job/{job_name}/{build_number}/api/json",
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except Exception as e:
            logger.error(f"Ошибка при получении статуса: {e}")
            return None

    def wait_for_job_completion(self, job_name: str, build_number: int, timeout: int = 600) -> bool:
        """Ожидание завершения job"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.get_job_status(job_name, build_number)

            if status:
                if status.get('building', False):
                    logger.info(f"Job {job_name} #{build_number} still running...")
                    time.sleep(10)
                else:
                    result = status.get('result', 'UNKNOWN')
                    if result == 'SUCCESS':
                        logger.info(f"Job {job_name} #{build_number} completed successfully")
                        return True
                    else:
                        logger.warning(f"Job {job_name} #{build_number} failed with result: {result}")
                        return False
            else:
                time.sleep(5)

        logger.error(f"Timeout waiting for job {job_name} #{build_number}")
        return False
# метод для проверки окружения
    def check_jenkins_environment(self):
        """Проверка окружения Jenkins"""
        try:
            response = self.session.get(
                f"{self.jenkins_url}/systemInfo",
                timeout=10
            )
            if response.status_code == 200:
                system_info = response.json()
                logger.info("Jenkins system info:")
                logger.info(f"Java: {system_info.get('java.version', 'unknown')}")
                logger.info(f"OS: {system_info.get('os.name', 'unknown')}")

            # Проверка установленных инструментов
            response = self.session.get(
                f"{self.jenkins_url}/toolProvisioning",
                timeout=10
            )
            if response.status_code == 200:
                logger.info("Tools provisioning available")

        except Exception as e:
            logger.error(f"Ошибка проверки окружения: {e}")

# Пример использования
def main():
    # Настройки Jenkins
    JENKINS_URL = "http://localhost:8080"
    JENKINS_USERNAME = "johny"
    JENKINS_TOKEN = "11a96a491331f3dd25d16caa6e5757272c"

    # Настройки теста
    JOB_NAME = "selenium-test-job"
    GIT_REPO = "https://github.com/johny19844/AFT.git"
    TEST_CLASS = "ya_testTest"

    # Создаем менеджер
    jenkins = JenkinsManager(JENKINS_URL, JENKINS_USERNAME, JENKINS_TOKEN)

    # Получаем CSRF crumb
    jenkins.get_crumb()
    jenkins.check_jenkins_environment()
    # Создаем job
    if jenkins.create_job(JOB_NAME, GIT_REPO, TEST_CLASS):
        logger.info("Job создан успешно")

        # Запускаем job
        queue_id = jenkins.run_job(JOB_NAME, {
            'TEST_CLASS': TEST_CLASS,
            'GIT_BRANCH': 'main'
        })

        if queue_id and queue_id != "success":
            logger.info(f"Ожидаем получения номера сборки...")
            time.sleep(3)

            # Получаем номер сборки из очереди
            build_number = jenkins.get_build_number_from_queue(queue_id)
            if build_number:
                logger.info(f"Номер сборки: {build_number}")

                # Мониторим статус выполнения
                logger.info("Мониторинг выполнения job...")
                success = jenkins.wait_for_job_completion(JOB_NAME, build_number)

                if success:
                    logger.info("✅ Job выполнен успешно!")
                else:
                    logger.warning("❌ Job завершился с ошибкой")
            else:
                logger.warning("Не удалось получить номер сборки")
        elif queue_id == "success":
            logger.info("Job запущен без параметров")
        else:
            logger.error("Не удалось запустить job")
    else:
        logger.error("Не удалось создать job")

if __name__ == "__main__":
    main()

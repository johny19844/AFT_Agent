import requests
import json
import time
import logging
from typing import Optional, Dict, Any

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
        
        # XML конфигурация для Jenkins 2.516.2
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
        <credentialsId>github-credentials</credentialsId>
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
  <triggers>
    <hudson.triggers.TimerTrigger>
      <spec>H/30 * * * *</spec>
    </hudson.triggers.TimerTrigger>
  </triggers>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.tasks.Shell>
      <command>echo "Cleaning workspace..."</command>
    </hudson.tasks.Shell>
    <hudson.tasks.Maven>
      <targets>clean test -Dtest=${{TEST_CLASS}} -Dwebdriver.chrome.driver=/usr/bin/chromedriver</targets>
      <mavenName>MAVEN_HOME</mavenName>
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
    <hudson.plugins.emailext.ExtendedEmailPublisher>
      <recipientList>builds@example.com</recipientList>
      <configuredTriggers>
        <hudson.plugins.emailext.plugins.trigger.FailureTrigger>
          <email>
            <subject>${{PROJECT_NAME}} - Build #${{BUILD_NUMBER}} - FAILURE</subject>
            <body>${{PROJECT_NAME}} - Build #${{BUILD_NUMBER}} - FAILURE</body>
            <recipientProviders>
              <hudson.plugins.emailext.plugins.recipients.DevelopersRecipientProvider/>
            </recipientProviders>
            <attachBuildLog>false</attachBuildLog>
            <compressBuildLog>false</compressBuildLog>
          </email>
        </hudson.plugins.emailext.plugins.trigger.FailureTrigger>
        <hudson.plugins.emailext.plugins.trigger.SuccessTrigger>
          <email>
            <subject>${{PROJECT_NAME}} - Build #${{BUILD_NUMBER}} - SUCCESS</subject>
            <body>${{PROJECT_NAME}} - Build #${{BUILD_NUMBER}} - SUCCESS</body>
            <recipientProviders>
              <hudson.plugins.emailext.plugins.recipients.DevelopersRecipientProvider/>
            </recipientProviders>
            <attachBuildLog>false</attachBuildLog>
            <compressBuildLog>false</compressBuildLog>
          </email>
        </hudson.plugins.emailext.plugins.trigger.SuccessTrigger>
      </configuredTriggers>
      <contentType>text/html</contentType>
      <defaultSubject>${{PROJECT_NAME}} - Build #${{BUILD_NUMBER}} - Result</defaultSubject>
      <defaultContent>${{PROJECT_NAME}} - Build #${{BUILD_NUMBER}} - Result</defaultContent>
      <attachmentsPattern></attachmentsPattern>
      <presendScript></presendScript>
      <postsendScript></postsendScript>
      <attachBuildLog>false</attachBuildLog>
      <compressBuildLog>false</compressBuildLog>
      <replyTo></replyTo>
      <saveOutput>false</saveOutput>
      <disabled>false</disabled>
    </hudson.plugins.emailext.ExtendedEmailPublisher>
  </publishers>
  <buildWrappers>
    <hudson.plugins.timestamper.TimestamperBuildWrapper/>
    <hudson.plugins.ansicolor.AnsiColorBuildWrapper>
      <colorMapName>xterm</colorMapName>
    </hudson.plugins.ansicolor.AnsiColorBuildWrapper>
  </buildWrappers>
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
            params_query = urlencode(parameters)
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

# Пример использования
def main():
    JENKINS_URL = "http://localhost:8080"
    JENKINS_USERNAME = "johny"
    JENKINS_TOKEN = "11a96a491331f3dd25d16caa6e5757272c"

    JOB_NAME = "selenium-test-job"
    GIT_REPO = "https://github.com/johny19844/AFT.git"
    TEST_CLASS = "ya_testTest"

    jenkins = JenkinsManager(JENKINS_URL, JENKINS_USERNAME, JENKINS_TOKEN)
    jenkins.get_crumb()

    # Создаем job
    if jenkins.create_job(JOB_NAME, GIT_REPO, TEST_CLASS):
        # Запускаем job
        queue_id = jenkins.run_job(JOB_NAME, {
            'TEST_CLASS': TEST_CLASS,
            'GIT_BRANCH': 'main'
        })

        if queue_id and queue_id != "success":
            # Ждем и получаем номер сборки
            time.sleep(5)
            build_number = jenkins.get_build_number_from_queue(queue_id)
            if build_number:
                logger.info(f"Build number: {build_number}")

                # Мониторим статус
                time.sleep(30)
                status = jenkins.get_job_status(JOB_NAME, build_number)
                if status:
                    logger.info(f"Build status: {status.get('result', 'UNKNOWN')}")

if __name__ == "__main__":
    main()

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import subprocess
import threading
import os
import json
import sys
import shutil
import time
import re

app = Flask(__name__)
CORS(app)

# Глобальные переменные
agent_process = None
agent_status = "stopped"
agent_logs = []
last_log_count = 0

def add_agent_log(message, log_type="info"):
    """Добавляет сообщение в логи агента с типом для цветового кодирования"""
    global agent_logs
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"{timestamp} - {message}"
    
    # Определяем тип сообщения для цветового кодирования в интерфейсе
    if any(keyword in message.lower() for keyword in ['error', 'failed', 'ошибка', 'не удалось']):
        log_type = "error"
    elif any(keyword in message.lower() for keyword in ['success', 'успешно', 'завершено', '✅']):
        log_type = "success"
    elif any(keyword in message.lower() for keyword in ['warning', 'предупреждение', '⚠️']):
        log_type = "warning"
    elif any(keyword in message.lower() for keyword in ['info', 'информация']):
        log_type = "info"
    
    log_entry = {
        "message": formatted_message,
        "type": log_type,
        "timestamp": timestamp,
        "raw_message": message
    }
    
    agent_logs.append(log_entry)
    print(f"📝 {formatted_message}")

def get_absolute_model_path(model_filename):
    """Возвращает абсолютный путь к файлу модели"""
    # Пробуем найти файл в разных местах
    possible_paths = [
        model_filename,  # Если уже передан полный путь
        f"./models/{model_filename}",  # В папке models
        f"./{model_filename}",  # В корневой папке
        f"../{model_filename}",  # На уровень выше
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return os.path.abspath(path)
    
    return None

@app.route('/')
def index():
    """Главная страница - загружаем HTML из файла"""
    return render_template('index.html')

@app.route('/api/upload-model', methods=['POST'])
def upload_model():
    """Загружает файл модели на сервер"""
    try:
        if 'model' not in request.files:
            return jsonify({"status": "error", "message": "Файл не найден"})
        
        file = request.files['model']
        if file.filename == '':
            return jsonify({"status": "error", "message": "Файл не выбран"})
        
        if file and file.filename.endswith('.gguf'):
            # Сохраняем файл в папку models
            filename = file.filename
            models_dir = './models'
            os.makedirs(models_dir, exist_ok=True)
            
            file_path = os.path.join(models_dir, filename)
            file.save(file_path)
            
            absolute_path = os.path.abspath(file_path)
            add_agent_log(f"INFO - 📁 Файл модели загружен: {filename}", "success")
            add_agent_log(f"INFO - 📂 Полный путь: {absolute_path}", "info")
            
            return jsonify({
                "status": "success", 
                "message": f"Файл {filename} загружен", 
                "path": absolute_path,
                "filename": filename
            })
        else:
            return jsonify({"status": "error", "message": "Неверный формат файла. Нужен .gguf"})
            
    except Exception as e:
        add_agent_log(f"ERROR - ❌ Ошибка загрузки файла: {str(e)}", "error")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/start', methods=['POST'])
def start_agent():
    global agent_process, agent_status, agent_logs, last_log_count
    
    # Проверяем существование agent_v024_interface.py
    if not os.path.exists('agent_v024_interface.py'):
        add_agent_log("ERROR - ❌ Файл agent_v024_interface.py не найден!", "error")
        return jsonify({
            "status": "error", 
            "message": "Файл agent_v024_interface.py не найден! Убедитесь, что он в той же папке."
        })
    
    # Получаем настройки из интерфейса
    config = request.json
    add_agent_log(f"INFO - 🔄 Получены настройки от интерфейса", "info")
    add_agent_log(f"INFO -    Модель: {config['model_path']}", "info")
    add_agent_log(f"INFO -    Репозиторий сценариев: {config['scenario_repo']}", "info")
    add_agent_log(f"INFO -    Репозиторий AFT: {config['aft_repo']}", "info")
    add_agent_log(f"INFO -    Интервал сканирования: {config['scan_interval']} сек", "info")
    
    # Очищаем предыдущие логи
    agent_logs = []
    last_log_count = 0
    
    add_agent_log("INFO - 🚀 Запуск агента с новыми настройками...", "info")
    
    # Получаем полный путь к файлу модели
    model_filename = config["model_path"]
    absolute_model_path = get_absolute_model_path(model_filename)
    
    if not absolute_model_path:
        add_agent_log(f"ERROR - ❌ Файл модели не найден: {model_filename}", "error")
        add_agent_log("INFO - 🔍 Искали в: ./models/, ./, ../", "info")
        return jsonify({
            "status": "error", 
            "message": f"Файл модели не найден: {model_filename}. Проверьте путь или загрузите файл через интерфейс."
        })
    
    add_agent_log(f"INFO - ✅ Найден файл модели: {absolute_model_path}", "success")
    
    try:
        # Создаем команду для запуска агента
        cmd = [
            sys.executable,  # Используем тот же Python, что и сервер
            "agent_v024_interface.py",
            "--model", absolute_model_path,  # Передаем полный путь
            "--scenario-repo", config["scenario_repo"], 
            "--aft-repo", config["aft_repo"],
            "--interval", str(config["scan_interval"])
        ]
        
        add_agent_log(f"INFO - 🔧 Команда запуска: {' '.join(cmd)}", "info")
        
        # Устанавливаем переменные окружения для корректной кодировки
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'
        
        agent_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            encoding='utf-8',
            errors='replace',
            env=env
        )
        
        agent_status = "running"
        add_agent_log("INFO - ✅ Агент успешно запущен!", "success")
        add_agent_log("INFO - 📖 Начинаем чтение логов агента...", "info")
        
        # Запускаем чтение логов в отдельном потоке
        threading.Thread(target=read_agent_logs, daemon=True).start()
        
        return jsonify({"status": "success", "message": "Агент запущен!"})
    
    except Exception as e:
        error_msg = f"ERROR - ❌ Ошибка запуска: {str(e)}"
        add_agent_log(error_msg, "error")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/stop', methods=['POST'])
def stop_agent():
    global agent_process, agent_status
    
    if agent_process:
        add_agent_log("WARNING - 🛑 Остановка агента по команде пользователя...", "warning")
        agent_process.terminate()
        try:
            agent_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            agent_process.kill()
            add_agent_log("WARNING - ⚠️ Агент был принудительно остановлен", "warning")
        agent_process = None
        add_agent_log("INFO - ✅ Агент остановлен", "info")
    
    agent_status = "stopped"
    return jsonify({"status": "success", "message": "Агент остановлен"})

@app.route('/api/status', methods=['GET'])
def get_status():
    global last_log_count, agent_logs
    # Возвращаем только новые логи (оптимизация)
    new_logs = agent_logs[last_log_count:]
    last_log_count = len(agent_logs)
    
    return jsonify({
        "status": agent_status,
        "logs": new_logs,  # Только новые логи
        "total_logs": len(agent_logs)
    })

@app.route('/api/logs', methods=['GET'])
def get_all_logs():
    """Возвращает все логи (для экспорта)"""
    return jsonify({
        "logs": agent_logs,
        "total": len(agent_logs)
    })

def read_agent_logs():
    """Читает логи из запущенного агента в реальном времени"""
    global agent_logs, agent_status, agent_process
    
    add_agent_log("INFO - 📖 Запущен мониторинг логов агента...", "info")
    
    while agent_process and agent_process.poll() is None:
        try:
            line = agent_process.stdout.readline()
            if line:
                cleaned_line = line.strip()
                if cleaned_line:
                    # Определяем тип сообщения на основе содержимого
                    log_type = "info"
                    line_lower = cleaned_line.lower()
                    
                    if any(word in line_lower for word in ['error', 'failed', 'exception', 'traceback', 'ошибка', 'не удалось']):
                        log_type = "error"
                    elif any(word in line_lower for word in ['success', 'успешно', 'завершено', '✅']):
                        log_type = "success"
                    elif any(word in line_lower for word in ['warning', 'предупреждение', '⚠️']):
                        log_type = "warning"
                    elif any(word in line_lower for word in ['debug', 'отладка']):
                        log_type = "debug"
                    
                    # Форматируем сообщение для единообразия
                    formatted_message = cleaned_line
                    add_agent_log(formatted_message, log_type)
        except Exception as e:
            add_agent_log(f"ERROR - Ошибка чтения логов агента: {e}", "error")
            break
    
    # Если процесс завершился
    if agent_process:
        return_code = agent_process.poll()
        agent_status = "stopped"
        
        if return_code == 0:
            add_agent_log("INFO - ✅ Агент завершил работу успешно", "success")
        elif return_code is None:
            add_agent_log("WARNING - ⚠️ Агент был остановлен", "warning")
        else:
            add_agent_log(f"ERROR - ❌ Агент завершил работу с кодом ошибки: {return_code}", "error")
        
        agent_process = None

if __name__ == '__main__':
    # Создаем папку для моделей если её нет
    os.makedirs('./models', exist_ok=True)
    
    print("🔍 Проверяем зависимости...")
    try:
        import flask
        import flask_cors
        from github import Github
        import jenkins
        from llama_cpp import Llama
        from selenium import webdriver
        from dotenv import load_dotenv
        print("✅ Все зависимости установлены!")
    except ImportError as e:
        print(f"❌ Отсутствует библиотека: {e.name}")
        print("📦 Установите зависимости командой:")
        print("pip install flask flask-cors PyGithub python-jenkins llama-cpp-python selenium python-dotenv")
        sys.exit(1)
    
    print("🌐 Запускаем сервер...")
    print("📱 Интерфейс будет доступен по адресу: http://localhost:5000")
    print("📝 Все логи агента будут отображаться в реальном времени")
    print("🛑 Чтобы остановить сервер, нажмите Ctrl+C")
    app.run(debug=True, port=5000)
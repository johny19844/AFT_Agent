import json
import re
from llama_cpp import Llama
from config import Config

class LocalAIClient:
    def __init__(self):
        self.config = Config()
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Загружает локальную GGUF модель"""
        print("🔄 Загружаю локальную AI модель...")
        
        try:
            self.model = Llama(
                model_path=self.config.LOCAL_MODEL_PATH,
                n_ctx=4096,  # Размер контекста
                n_threads=6,  # Количество потоков
                n_gpu_layers=0,  # 0 = только CPU, больше 0 = использовать GPU
                verbose=False
            )
            print("✅ Локальная модель загружена успешно!")
        except Exception as e:
            print(f"❌ Ошибка загрузки модели: {e}")
            raise
    
    def generate_response(self, prompt, system_message=None, max_tokens=None):
        """Генерирует ответ с помощью локальной модели"""
        
        if not self.model:
            raise Exception("Модель не загружена")
        
        # Формируем сообщения
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        try:
            # Преобразуем в формат для llama-cpp
            prompt_text = self._format_messages(messages)
            
            # Генерируем ответ
            response = self.model(
                prompt=prompt_text,
                max_tokens=max_tokens or self.config.LOCAL_MODEL_MAX_TOKENS,
                temperature=self.config.LOCAL_MODEL_TEMPERATURE,
                stop=["</s>", "```", "###", "---"],
                echo=False,
                stream=False
            )
            
            text_response = response['choices'][0]['text'].strip()
            
            # Очищаем ответ
            cleaned_response = self._clean_response(text_response)
            
            return cleaned_response
            
        except Exception as e:
            print(f"❌ Ошибка генерации: {e}")
            return f'{{"error": "Ошибка генерации: {e}"}}'
    
    def _format_messages(self, messages):
        """Форматирует сообщения для локальной модели"""
        formatted_text = ""
        
        for message in messages:
            if message["role"] == "system":
                formatted_text += f"<s>[INST] <<SYS>>\n{message['content']}\n<</SYS>>\n\n"
            elif message["role"] == "user":
                if formatted_text.endswith("\n\n"):
                    formatted_text += f"{message['content']} [/INST]"
                else:
                    formatted_text += f"{message['content']} [/INST]"
            elif message["role"] == "assistant":
                formatted_text += f" {message['content']} </s>"
        
        return formatted_text
    
    def _clean_response(self, text):
        """Очищает ответ от лишних символов и извлекает JSON если есть"""
        
        # Пытаемся найти JSON в ответе
        json_pattern = r'\{[\s\S]*\}'
        matches = re.findall(json_pattern, text)
        
        if matches:
            # Берем последний найденный JSON (обычно это основной ответ)
            return matches[-1]
        else:
            # Если JSON не найден, возвращаем как есть
            return text
    
    def chat_completion(self, messages, max_tokens=None):
        """Интерфейс совместимый с OpenAI"""
        if not messages:
            return {"choices": [{"message": {"content": "No messages"}}]}
        
        # Извлекаем system message и user message
        system_msg = ""
        user_msg = ""
        
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            elif msg["role"] == "user":
                user_msg = msg["content"]
        
        response_text = self.generate_response(
            prompt=user_msg,
            system_message=system_msg,
            max_tokens=max_tokens
        )
        
        return {
            "choices": [{
                "message": {
                    "content": response_text
                }
            }]
        }
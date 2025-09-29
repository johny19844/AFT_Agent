import openai
from local_ai import LocalAIClient
from config import Config

class UniversalAIClient:
    def __init__(self):
        self.config = Config()
        self.client = None
        self.setup_client()
    
    def setup_client(self):
        """Настраивает клиент для выбранного провайдера"""
        if self.config.AI_PROVIDER == "openai":
            print("🔗 Использую OpenAI API")
            openai.api_key = self.config.OPENAI_API_KEY
            self.client = "openai"
        else:
            print("💻 Использую локальную модель")
            self.client = LocalAIClient()
    
    def generate_response(self, prompt, system_message=None, max_tokens=None):
        """Универсальный метод генерации ответа"""
        
        if self.client == "openai":
            return self._openai_generate(prompt, system_message, max_tokens)
        else:
            return self._local_generate(prompt, system_message, max_tokens)
    
    def _openai_generate(self, prompt, system_message, max_tokens):
        """Генерация через OpenAI"""
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = openai.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=messages,
                max_tokens=max_tokens or 1000,
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            return f'{{"error": "OpenAI error: {e}"}}'
    
    def _local_generate(self, prompt, system_message, max_tokens):
        """Генерация через локальную модель"""
        return self.client.generate_response(prompt, system_message, max_tokens)
    
    def chat_completion(self, messages, max_tokens=None):
        """Совместимый с OpenAI интерфейс"""
        if self.client == "openai":
            try:
                response = openai.chat.completions.create(
                    model=self.config.OPENAI_MODEL,
                    messages=messages,
                    max_tokens=max_tokens or 1000,
                    temperature=0.1
                )
                return response
            except Exception as e:
                return {"choices": [{"message": {"content": f'{{"error": "OpenAI error: {e}"}}'}}]}
        else:
            return self.client.chat_completion(messages, max_tokens)
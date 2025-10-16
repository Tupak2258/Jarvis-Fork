# llm_clients.py (обновленная версия)

import requests
import json
import logging
import re
from typing import Dict, List, Optional
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT

class OllamaClient:
    """Клиент для взаимодействия с Ollama API"""
    
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL
        self.timeout = OLLAMA_TIMEOUT
        self.conversation_history = []
        self.logger = logging.getLogger(__name__)
        
        # --- НОВЫЙ, УЛУЧШЕННЫЙ СИСТЕМНЫЙ ПРОМПТ ---
        self.system_prompt = """
Ты — 'Джарвис', продвинутый ИИ-ассистент, интегрированный в операционную систему.

Твои задачи:
1.  **Выполнять системные команды:** Если пользователь просит что-то сделать с компьютером (открыть, закрыть, создать, написать), ты ДОЛЖЕН сгенерировать команду в специальном формате.
2.  **Поддерживать разговор:** Если пользователь задает вопрос или просто общается, ты должен ответить как эрудированный собеседник, НЕ генерируя команду.

СТРОГО СЛЕДУЙ ФОРМАТУ ВЫВОДА:
<command>[здесь команда]</command>
<answer>[здесь твой ответ для пользователя]</answer>

--- ИНСТРУКЦИИ ПО КОМАНДАМ ---

1.  **ЕСЛИ ЭТО СИСТЕМНАЯ КОМАНДА (открыть, закрыть, написать и т.д.):**
    - В тег <command> помести четкое описание действия.
    - В тег <answer> помести краткое подтверждение для пользователя.
    
    ПРИМЕР 1 (Открыть программу):
    Пользователь: "Запусти хром"
    Твой вывод:
    <command>открыть chrome</command>
    <answer>Открываю Google Chrome.</answer>
    
    ПРИМЕР 2 (Написать текст):
    Пользователь: "Открой блокнот и напиши: Привет, мир!"
    Твой вывод:
    <command>написать в блокнот: Привет, мир!</command>
    <answer>Хорошо, печатаю "Привет, мир!" в Блокноте.</answer>

2.  **ЕСЛИ ЭТО ПРОСТОЙ РАЗГОВОР ИЛИ ВОПРОС:**
    - В тег <command> ОБЯЗАТЕЛЬНО помести специальное слово: **none**
    - В тег <answer> помести полноценный, развернутый ответ на вопрос пользователя.
    
    ПРИМЕР:
    Пользователь: "Кто написал роман Война и мир?"
    Твой вывод:
    <command>none</command>
    <answer>Роман "Война и мир" был написан великим русским писателем Львом Николаевичем Толстым.</answer>
"""

    def _make_request(self, endpoint: str, data: Dict) -> Optional[Dict]:
        """Выполняет запрос к Ollama API"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.post(
                url, 
                json=data, 
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ошибка запроса к Ollama: {e}")
            return None
    
    def is_available(self) -> bool:
        """Проверяет доступность Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate_response(self, user_input: str, use_history: bool = True) -> str:
        """Генерирует ответ на основе пользовательского ввода"""
        try:
            messages = [{"role": "system", "content": self.system_prompt}]
            if use_history:
                messages.extend(self.conversation_history)
            messages.append({"role": "user", "content": user_input})
            
            data = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
            
            response = self._make_request("api/chat", data)
            
            if response and "message" in response:
                ai_response = response["message"]["content"].strip()
                if use_history:
                    self.conversation_history.append({"role": "user", "content": user_input})
                    self.conversation_history.append({"role": "assistant", "content": ai_response})
                    if len(self.conversation_history) > 10:
                        self.conversation_history = self.conversation_history[-10:]
                
                self.logger.info(f"Получен ответ от LLM: {ai_response[:100]}...")
                return ai_response
            else:
                return "<command>none</command><answer>Извините, не могу получить ответ от языковой модели.</answer>"
                
        except Exception as e:
            self.logger.error(f"Ошибка генерации ответа: {e}")
            return "<command>none</command><answer>Произошла ошибка при обработке вашего запроса.</answer>"
    
    def parse_command(self, response: str) -> tuple[Optional[str], str]:
        """Парсит ответ на команду и обычный ответ из XML-подобного формата"""
        command_search = re.search(r'<command>(.*?)</command>', response, re.DOTALL)
        answer_search = re.search(r'<answer>(.*?)</answer>', response, re.DOTALL)
        
        command = None
        answer = response.strip()  # По умолчанию - весь ответ
        
        if command_search:
            command = command_search.group(1).strip()
            # Проверяем на специальное слово "none"
            if command.lower() == 'none':
                command = None

        if answer_search:
            answer = answer_search.group(1).strip()
        
        return command, answer
    
    def clear_history(self):
        """Очищает историю разговора"""
        self.conversation_history.clear()
        self.logger.info("История разговора очищена")
    
    def set_model(self, model_name: str):
        """Устанавливает модель для использования"""
        self.model = model_name
        self.logger.info(f"Модель изменена на: {model_name}")
    
    def get_available_models(self) -> List[str]:
        """Получает список доступных моделей"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except:
            return []
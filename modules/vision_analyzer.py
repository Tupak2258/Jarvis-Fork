"""
Модуль для анализа изображений и текста с помощью QwenVL
"""

import base64
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from PIL import Image
import io


class VisionAnalyzer:
    """Класс для анализа изображений с помощью QwenVL через Ollama"""
    
    def __init__(self, model_name: str = "qwen2.5vl:7b"):
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name
        self.ollama_url = "http://localhost:11434"
        
        # Проверяем доступность модели
        self._check_model_availability()
        
        self.logger.info(f"VisionAnalyzer инициализирован с моделью {model_name}")
    
    def _check_model_availability(self) -> bool:
        """Проверяет доступность модели QwenVL"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
                
                if self.model_name in available_models:
                    self.logger.info(f"Модель {self.model_name} доступна")
                    return True
                else:
                    self.logger.warning(f"Модель {self.model_name} не найдена. Доступные: {available_models}")
                    return False
            else:
                self.logger.error(f"Ошибка подключения к Ollama: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка проверки модели: {e}")
            return False
    
    def _encode_image(self, image_path: str) -> Optional[str]:
        """Кодирует изображение в base64"""
        try:
            with open(image_path, 'rb') as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_string
        except Exception as e:
            self.logger.error(f"Ошибка кодирования изображения {image_path}: {e}")
            return None
    
    def analyze_telegram_screenshot(self, image_path: str, analysis_type: str = "general") -> Dict[str, Any]:
        """
        Анализирует скриншот Telegram с помощью QwenVL
        
        Args:
            image_path: Путь к изображению
            analysis_type: Тип анализа ('general', 'messages', 'contacts', 'media')
            
        Returns:
            Результат анализа
        """
        try:
            # Кодируем изображение
            encoded_image = self._encode_image(image_path)
            if not encoded_image:
                return {'error': 'Не удалось закодировать изображение'}
            
            # Формируем промпт в зависимости от типа анализа
            prompts = {
                'general': """Проанализируй этот скриншот Telegram. Опиши что ты видишь:
                - Какой чат открыт (имя, тип чата)
                - Сколько сообщений видно
                - Основные темы разговора
                - Есть ли медиафайлы (фото, видео, документы)
                - Время последних сообщений
                Отвечай на русском языке.""",
                
                'messages': """Извлеки и структурируй все текстовые сообщения из этого скриншота Telegram:
                - Имя отправителя
                - Текст сообщения
                - Время отправки (если видно)
                - Тип сообщения (текст, медиа, пересланное)
                Представь в виде списка. Отвечай на русском языке.""",
                
                'contacts': """Найди и перечисли все контакты/участников, которые видны в этом скриншоте Telegram:
                - Имена пользователей
                - Статусы (онлайн, был недавно)
                - Аватарки (есть/нет)
                Отвечай на русском языке.""",
                
                'media': """Найди и опиши все медиафайлы в этом скриншоте Telegram:
                - Фотографии (что изображено)
                - Видео (превью, длительность)
                - Документы (названия, типы файлов)
                - Стикеры или эмодзи
                Отвечай на русском языке.""",
                
                'data_extraction': """Извлеки структурированные данные из этого скриншота Telegram для переноса в таблицу:
                - Контакты (имена, телефоны, email если есть)
                - Важные даты и события
                - Числовые данные (цены, количества, адреса)
                - Ссылки и упоминания
                - Задачи и поручения
                Представь в формате: Тип данных | Значение | Контекст
                Отвечай на русском языке."""
            }
            
            prompt = prompts.get(analysis_type, prompts['general'])
            
            # Отправляем запрос к Ollama
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "images": [encoded_image],
                "stream": False
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_result = {
                    'success': True,
                    'analysis_type': analysis_type,
                    'image_path': image_path,
                    'response': result.get('response', ''),
                    'model': self.model_name,
                    'prompt_used': prompt
                }
                
                self.logger.info(f"Анализ изображения завершен: {analysis_type}")
                return analysis_result
            else:
                error_msg = f"Ошибка API Ollama: {response.status_code}"
                self.logger.error(error_msg)
                return {'error': error_msg, 'success': False}
                
        except Exception as e:
            error_msg = f"Ошибка анализа изображения: {e}"
            self.logger.error(error_msg)
            return {'error': error_msg, 'success': False}
    
    def extract_structured_data(self, image_path: str, data_types: List[str]) -> Dict[str, List[str]]:
        """
        Извлекает структурированные данные определенных типов
        
        Args:
            image_path: Путь к изображению
            data_types: Типы данных для извлечения ['contacts', 'dates', 'numbers', 'tasks']
            
        Returns:
            Словарь с извлеченными данными по типам
        """
        try:
            # Формируем специализированный промпт
            data_type_prompts = {
                'contacts': "Найди все имена людей, телефоны, email адреса",
                'dates': "Найди все даты, время, временные периоды",
                'numbers': "Найди все числа, цены, количества, адреса",
                'tasks': "Найди все задачи, поручения, планы, дедлайны",
                'links': "Найди все ссылки, упоминания каналов, хештеги"
            }
            
            requested_types = [data_type_prompts[dt] for dt in data_types if dt in data_type_prompts]
            
            prompt = f"""Извлеки из этого скриншота Telegram следующие типы данных:
            {'; '.join(requested_types)}
            
            Представь результат в формате JSON:
            {{
                "contacts": ["имя1", "телефон1", "email1"],
                "dates": ["дата1", "время1"],
                "numbers": ["число1", "цена1"],
                "tasks": ["задача1", "поручение1"],
                "links": ["ссылка1", "@канал1"]
            }}
            
            Если данных определенного типа нет, оставь пустой массив.
            """
            
            encoded_image = self._encode_image(image_path)
            if not encoded_image:
                return {}
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "images": [encoded_image],
                "stream": False
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                
                # Пытаемся извлечь JSON из ответа
                try:
                    import json
                    import re
                    
                    # Ищем JSON в ответе
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        structured_data = json.loads(json_str)
                        return structured_data
                    else:
                        # Если JSON не найден, парсим текст вручную
                        return self._parse_structured_response(response_text, data_types)
                        
                except json.JSONDecodeError:
                    # Если JSON невалидный, парсим текст
                    return self._parse_structured_response(response_text, data_types)
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Ошибка извлечения структурированных данных: {e}")
            return {}
    
    def _parse_structured_response(self, response_text: str, data_types: List[str]) -> Dict[str, List[str]]:
        """Парсит ответ модели для извлечения структурированных данных"""
        result = {dt: [] for dt in data_types}
        
        lines = response_text.split('\n')
        current_type = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Определяем тип данных по ключевым словам
            if any(keyword in line.lower() for keyword in ['контакт', 'имя', 'телефон', 'email']):
                current_type = 'contacts'
            elif any(keyword in line.lower() for keyword in ['дата', 'время', 'число']):
                current_type = 'dates'
            elif any(keyword in line.lower() for keyword in ['цена', 'рубл', 'долл', 'количество']):
                current_type = 'numbers'
            elif any(keyword in line.lower() for keyword in ['задача', 'поручение', 'план', 'дедлайн']):
                current_type = 'tasks'
            elif any(keyword in line.lower() for keyword in ['ссылка', '@', 'http', 'канал']):
                current_type = 'links'
            
            # Добавляем данные в соответствующий тип
            if current_type and current_type in result:
                # Очищаем строку от маркеров списка
                cleaned_line = re.sub(r'^[-*•]\s*', '', line)
                if cleaned_line and len(cleaned_line) > 2:
                    result[current_type].append(cleaned_line)
        
        return result
    
    def analyze_chat_sentiment(self, image_path: str) -> Dict[str, Any]:
        """Анализирует эмоциональную окраску чата"""
        try:
            prompt = """Проанализируй эмоциональную окраску этого чата в Telegram:
            - Общее настроение разговора (позитивное, негативное, нейтральное)
            - Уровень активности участников
            - Наличие конфликтов или споров
            - Дружелюбность общения
            - Деловой или личный характер переписки
            
            Дай оценку от 1 до 10 по каждому параметру и общий вывод.
            Отвечай на русском языке."""
            
            encoded_image = self._encode_image(image_path)
            if not encoded_image:
                return {'error': 'Не удалось закодировать изображение'}
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "images": [encoded_image],
                "stream": False
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'sentiment_analysis': result.get('response', ''),
                    'image_path': image_path
                }
            
            return {'error': f'Ошибка API: {response.status_code}', 'success': False}
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа настроения: {e}")
            return {'error': str(e), 'success': False}
    
    def compare_screenshots(self, image1_path: str, image2_path: str) -> Dict[str, Any]:
        """Сравнивает два скриншота чата"""
        try:
            prompt = """Сравни эти два скриншота Telegram чата:
            - Что изменилось между ними?
            - Появились ли новые сообщения?
            - Изменился ли статус участников?
            - Есть ли различия в интерфейсе?
            
            Опиши все найденные различия.
            Отвечай на русском языке."""
            
            encoded_image1 = self._encode_image(image1_path)
            encoded_image2 = self._encode_image(image2_path)
            
            if not encoded_image1 or not encoded_image2:
                return {'error': 'Не удалось закодировать изображения'}
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "images": [encoded_image1, encoded_image2],
                "stream": False
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'comparison': result.get('response', ''),
                    'image1_path': image1_path,
                    'image2_path': image2_path
                }
            
            return {'error': f'Ошибка API: {response.status_code}', 'success': False}
            
        except Exception as e:
            self.logger.error(f"Ошибка сравнения скриншотов: {e}")
            return {'error': str(e), 'success': False}
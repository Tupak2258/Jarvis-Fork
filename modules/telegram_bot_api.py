"""
Модуль для работы с Telegram Bot API
Обеспечивает отправку сообщений, получение обновлений и анализ чатов
"""

import os
import json
import logging
import asyncio
import aiohttp
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from pathlib import Path
import threading
import queue


class TelegramBotAPI:
    """Класс для работы с Telegram Bot API"""
    
    def __init__(self, bot_token: str = None, webhook_url: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Получаем токен бота из переменных окружения или параметра
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            # Пытаемся загрузить из файла конфигурации
            config_path = Path("config/telegram_bot.json")
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        self.bot_token = config.get('bot_token')
                except Exception as e:
                    self.logger.error(f"Ошибка загрузки конфигурации Telegram: {e}")
        
        if not self.bot_token:
            raise ValueError("Telegram Bot Token не найден. Установите TELEGRAM_BOT_TOKEN или создайте config/telegram_bot.json")
        
        self.webhook_url = webhook_url
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Очередь для обработки сообщений
        self.message_queue = queue.Queue()
        self.is_running = False
        self.update_offset = 0
        
        # Обработчики команд
        self.command_handlers = {}
        self.message_handlers = []
        
        # Кэш для чатов и пользователей
        self.chats_cache = {}
        self.users_cache = {}
        
        # Настройки
        self.max_message_length = 4096
        self.rate_limit_delay = 0.1  # Задержка между запросами
        
        self.logger.info("TelegramBotAPI инициализирован")
    
    async def get_me(self) -> Optional[Dict]:
        """Получает информацию о боте"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/getMe") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            return data.get('result')
                    else:
                        self.logger.error(f"Ошибка получения информации о боте: {response.status}")
        except Exception as e:
            self.logger.error(f"Ошибка запроса getMe: {e}")
        return None
    
    async def send_message(self, chat_id: str, text: str, 
                          parse_mode: str = "HTML", 
                          reply_to_message_id: int = None,
                          disable_web_page_preview: bool = True) -> bool:
        """
        Отправляет сообщение в чат
        
        Args:
            chat_id: ID чата или username
            text: Текст сообщения
            parse_mode: Режим парсинга (HTML, Markdown)
            reply_to_message_id: ID сообщения для ответа
            disable_web_page_preview: Отключить предпросмотр ссылок
        
        Returns:
            True если сообщение отправлено успешно
        """
        try:
            # Разбиваем длинные сообщения на части
            if len(text) > self.max_message_length:
                messages = self._split_message(text)
                success_count = 0
                for i, message_text in enumerate(messages):
                    if await self._send_single_message(chat_id, message_text, parse_mode, 
                                                     reply_to_message_id if i == 0 else None, 
                                                     disable_web_page_preview):
                        success_count += 1
                    await asyncio.sleep(self.rate_limit_delay)
                return success_count > 0
            else:
                return await self._send_single_message(chat_id, text, parse_mode, 
                                                     reply_to_message_id, disable_web_page_preview)
        
        except Exception as e:
            self.logger.error(f"Ошибка отправки сообщения: {e}")
            return False
    
    async def _send_single_message(self, chat_id: str, text: str, 
                                  parse_mode: str, reply_to_message_id: int = None,
                                  disable_web_page_preview: bool = True) -> bool:
        """Отправляет одно сообщение"""
        try:
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': disable_web_page_preview
            }
            
            if reply_to_message_id:
                payload['reply_to_message_id'] = reply_to_message_id
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/sendMessage", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            self.logger.info(f"Сообщение отправлено в чат {chat_id}")
                            return True
                        else:
                            self.logger.error(f"Ошибка API Telegram: {data.get('description')}")
                    else:
                        self.logger.error(f"HTTP ошибка: {response.status}")
        
        except Exception as e:
            self.logger.error(f"Ошибка отправки сообщения: {e}")
        
        return False
    
    def _split_message(self, text: str) -> List[str]:
        """Разбивает длинное сообщение на части"""
        if len(text) <= self.max_message_length:
            return [text]
        
        parts = []
        current_part = ""
        
        # Разбиваем по абзацам
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            if len(current_part) + len(paragraph) + 2 <= self.max_message_length:
                if current_part:
                    current_part += "\n\n" + paragraph
                else:
                    current_part = paragraph
            else:
                if current_part:
                    parts.append(current_part)
                    current_part = paragraph
                else:
                    # Если абзац слишком длинный, разбиваем по предложениям
                    sentences = paragraph.split('. ')
                    for sentence in sentences:
                        if len(current_part) + len(sentence) + 2 <= self.max_message_length:
                            if current_part:
                                current_part += ". " + sentence
                            else:
                                current_part = sentence
                        else:
                            if current_part:
                                parts.append(current_part)
                                current_part = sentence
                            else:
                                # Если предложение слишком длинное, разбиваем принудительно
                                while len(sentence) > self.max_message_length:
                                    parts.append(sentence[:self.max_message_length])
                                    sentence = sentence[self.max_message_length:]
                                current_part = sentence
        
        if current_part:
            parts.append(current_part)
        
        return parts
    
    async def get_chat_info(self, chat_id: str) -> Optional[Dict]:
        """Получает информацию о чате"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/getChat", 
                                     params={'chat_id': chat_id}) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            chat_info = data.get('result')
                            self.chats_cache[chat_id] = chat_info
                            return chat_info
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о чате: {e}")
        return None
    
    async def get_chat_members_count(self, chat_id: str) -> Optional[int]:
        """Получает количество участников чата"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/getChatMemberCount", 
                                     params={'chat_id': chat_id}) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            return data.get('result')
        except Exception as e:
            self.logger.error(f"Ошибка получения количества участников: {e}")
        return None
    
    async def get_chat_history(self, chat_id: str, limit: int = 100) -> List[Dict]:
        """
        Получает историю сообщений чата
        
        Args:
            chat_id: ID чата
            limit: Максимальное количество сообщений
        
        Returns:
            Список сообщений
        """
        try:
            messages = []
            offset = 0
            
            while len(messages) < limit:
                async with aiohttp.ClientSession() as session:
                    params = {
                        'chat_id': chat_id,
                        'limit': min(100, limit - len(messages)),
                        'offset': offset
                    }
                    
                    async with session.get(f"{self.base_url}/getUpdates", params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('ok'):
                                updates = data.get('result', [])
                                if not updates:
                                    break
                                
                                for update in updates:
                                    if 'message' in update:
                                        message = update['message']
                                        if str(message.get('chat', {}).get('id')) == str(chat_id):
                                            messages.append(message)
                                
                                offset = max(update.get('update_id', 0) for update in updates) + 1
                            else:
                                break
                        else:
                            break
                
                await asyncio.sleep(self.rate_limit_delay)
            
            return messages[:limit]
        
        except Exception as e:
            self.logger.error(f"Ошибка получения истории чата: {e}")
            return []
    
    async def search_messages(self, chat_id: str, query: str, limit: int = 50) -> List[Dict]:
        """
        Ищет сообщения в чате по тексту
        
        Args:
            chat_id: ID чата
            query: Поисковый запрос
            limit: Максимальное количество результатов
        
        Returns:
            Список найденных сообщений
        """
        try:
            # Получаем историю сообщений
            messages = await self.get_chat_history(chat_id, limit * 2)
            
            # Фильтруем по тексту
            query_lower = query.lower()
            filtered_messages = []
            
            for message in messages:
                text = message.get('text', '').lower()
                if query_lower in text:
                    filtered_messages.append(message)
                    if len(filtered_messages) >= limit:
                        break
            
            return filtered_messages
        
        except Exception as e:
            self.logger.error(f"Ошибка поиска сообщений: {e}")
            return []
    
    async def analyze_chat_sentiment(self, chat_id: str, limit: int = 50) -> Dict[str, Any]:
        """
        Анализирует настроение в чате
        
        Args:
            chat_id: ID чата
            limit: Количество сообщений для анализа
        
        Returns:
            Результат анализа настроения
        """
        try:
            messages = await self.get_chat_history(chat_id, limit)
            
            if not messages:
                return {
                    'success': False,
                    'error': 'Нет сообщений для анализа',
                    'total_messages': 0
                }
            
            # Простой анализ настроения по ключевым словам
            positive_words = ['хорошо', 'отлично', 'супер', 'класс', 'спасибо', '👍', '😊', '😄', '❤️']
            negative_words = ['плохо', 'ужасно', 'проблема', 'ошибка', '😞', '😢', '😡', '👎']
            
            positive_count = 0
            negative_count = 0
            total_text_length = 0
            
            for message in messages:
                text = message.get('text', '').lower()
                total_text_length += len(text)
                
                for word in positive_words:
                    if word in text:
                        positive_count += 1
                
                for word in negative_words:
                    if word in text:
                        negative_count += 1
            
            # Определяем общее настроение
            if positive_count > negative_count:
                sentiment = 'positive'
                sentiment_score = positive_count / (positive_count + negative_count) if (positive_count + negative_count) > 0 else 0.5
            elif negative_count > positive_count:
                sentiment = 'negative'
                sentiment_score = negative_count / (positive_count + negative_count) if (positive_count + negative_count) > 0 else 0.5
            else:
                sentiment = 'neutral'
                sentiment_score = 0.5
            
            return {
                'success': True,
                'sentiment': sentiment,
                'sentiment_score': sentiment_score,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'total_messages': len(messages),
                'average_message_length': total_text_length / len(messages) if messages else 0
            }
        
        except Exception as e:
            self.logger.error(f"Ошибка анализа настроения: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_messages': 0
            }
    
    async def extract_contacts_from_chat(self, chat_id: str, limit: int = 100) -> List[Dict[str, str]]:
        """
        Извлекает контакты из чата
        
        Args:
            chat_id: ID чата
            limit: Количество сообщений для анализа
        
        Returns:
            Список найденных контактов
        """
        try:
            messages = await self.get_chat_history(chat_id, limit)
            contacts = []
            
            import re
            
            # Паттерны для поиска контактов
            phone_pattern = r'(\+?[1-9]\d{1,14})'
            email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            username_pattern = r'@([a-zA-Z0-9_]{5,32})'
            
            for message in messages:
                text = message.get('text', '')
                if not text:
                    continue
                
                # Поиск телефонов
                phones = re.findall(phone_pattern, text)
                for phone in phones:
                    contacts.append({
                        'type': 'phone',
                        'value': phone,
                        'message_id': message.get('message_id'),
                        'date': message.get('date')
                    })
                
                # Поиск email
                emails = re.findall(email_pattern, text)
                for email in emails:
                    contacts.append({
                        'type': 'email',
                        'value': email,
                        'message_id': message.get('message_id'),
                        'date': message.get('date')
                    })
                
                # Поиск username
                usernames = re.findall(username_pattern, text)
                for username in usernames:
                    contacts.append({
                        'type': 'username',
                        'value': f'@{username}',
                        'message_id': message.get('message_id'),
                        'date': message.get('date')
                    })
            
            # Удаляем дубликаты
            unique_contacts = []
            seen = set()
            for contact in contacts:
                key = (contact['type'], contact['value'])
                if key not in seen:
                    seen.add(key)
                    unique_contacts.append(contact)
            
            return unique_contacts
        
        except Exception as e:
            self.logger.error(f"Ошибка извлечения контактов: {e}")
            return []
    
    def register_command_handler(self, command: str, handler: Callable):
        """Регистрирует обработчик команды"""
        self.command_handlers[command] = handler
        self.logger.info(f"Зарегистрирован обработчик команды: {command}")
    
    def register_message_handler(self, handler: Callable):
        """Регистрирует обработчик всех сообщений"""
        self.message_handlers.append(handler)
        self.logger.info("Зарегистрирован обработчик сообщений")
    
    async def start_polling(self):
        """Запускает polling для получения обновлений"""
        self.is_running = True
        self.logger.info("Запуск polling для получения обновлений")
        
        try:
            while self.is_running:
                try:
                    # Получаем обновления
                    updates = await self._get_updates()
                    
                    for update in updates:
                        await self._process_update(update)
                    
                    await asyncio.sleep(1)  # Пауза между запросами
                
                except Exception as e:
                    self.logger.error(f"Ошибка в polling: {e}")
                    await asyncio.sleep(5)  # Пауза при ошибке
        
        except Exception as e:
            self.logger.error(f"Критическая ошибка polling: {e}")
        finally:
            self.is_running = False
    
    async def _get_updates(self) -> List[Dict]:
        """Получает обновления от Telegram"""
        try:
            params = {'offset': self.update_offset, 'timeout': 30}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/getUpdates", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            updates = data.get('result', [])
                            if updates:
                                self.update_offset = max(update.get('update_id', 0) for update in updates) + 1
                            return updates
        except Exception as e:
            self.logger.error(f"Ошибка получения обновлений: {e}")
        
        return []
    
    async def _process_update(self, update: Dict):
        """Обрабатывает полученное обновление"""
        try:
            if 'message' in update:
                message = update['message']
                await self._process_message(message)
        
        except Exception as e:
            self.logger.error(f"Ошибка обработки обновления: {e}")
    
    async def _process_message(self, message: Dict):
        """Обрабатывает сообщение"""
        try:
            text = message.get('text', '')
            chat_id = message.get('chat', {}).get('id')
            
            # Обработка команд
            if text.startswith('/'):
                command = text.split()[0][1:]  # Убираем /
                if command in self.command_handlers:
                    await self.command_handlers[command](message)
                else:
                    await self.send_message(chat_id, f"Неизвестная команда: /{command}")
            
            # Обработка всех сообщений
            for handler in self.message_handlers:
                try:
                    await handler(message)
                except Exception as e:
                    self.logger.error(f"Ошибка в обработчике сообщений: {e}")
        
        except Exception as e:
            self.logger.error(f"Ошибка обработки сообщения: {e}")
    
    def stop_polling(self):
        """Останавливает polling"""
        self.is_running = False
        self.logger.info("Polling остановлен")
    
    async def set_webhook(self, webhook_url: str) -> bool:
        """Устанавливает webhook"""
        try:
            payload = {'url': webhook_url}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/setWebhook", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            self.webhook_url = webhook_url
                            self.logger.info(f"Webhook установлен: {webhook_url}")
                            return True
        except Exception as e:
            self.logger.error(f"Ошибка установки webhook: {e}")
        
        return False
    
    async def delete_webhook(self) -> bool:
        """Удаляет webhook"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/deleteWebhook") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('ok'):
                            self.webhook_url = None
                            self.logger.info("Webhook удален")
                            return True
        except Exception as e:
            self.logger.error(f"Ошибка удаления webhook: {e}")
        
        return False
    
    def get_chat_list(self) -> List[Dict]:
        """Возвращает список известных чатов"""
        return list(self.chats_cache.values())
    
    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Возвращает информацию о пользователе из кэша"""
        return self.users_cache.get(user_id)
    
    async def close(self):
        """Закрывает соединения и останавливает бота"""
        self.stop_polling()
        self.logger.info("TelegramBotAPI закрыт")

"""
Модуль для памяти разговоров в Telegram
Обеспечивает сохранение контекста и истории разговоров
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import hashlib


class TelegramMemory:
    """Класс для управления памятью разговоров в Telegram"""
    
    def __init__(self, data_dir: str = "data", max_memory_size: int = 1000):
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Файлы для хранения данных
        self.conversations_file = self.data_dir / "telegram_conversations.json"
        self.context_file = self.data_dir / "telegram_context.json"
        self.memory_file = self.data_dir / "telegram_memory.json"
        
        # Настройки
        self.max_memory_size = max_memory_size
        self.context_ttl = 3600  # 1 час
        self.conversation_ttl = 86400 * 7  # 7 дней
        
        # Кэш данных
        self.conversations = {}
        self.context = {}
        self.memory = {}
        
        # Загружаем данные
        self._load_data()
        
        self.logger.info("TelegramMemory инициализирован")
    
    def _load_data(self):
        """Загружает данные из файлов"""
        try:
            # Загружаем разговоры
            if self.conversations_file.exists():
                with open(self.conversations_file, 'r', encoding='utf-8') as f:
                    self.conversations = json.load(f)
            
            # Загружаем контекст
            if self.context_file.exists():
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    self.context = json.load(f)
            
            # Загружаем память
            if self.memory_file.exists():
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.memory = json.load(f)
            
            self.logger.info(f"Загружено: {len(self.conversations)} разговоров, {len(self.context)} контекстов, {len(self.memory)} записей памяти")
        
        except Exception as e:
            self.logger.error(f"Ошибка загрузки данных памяти: {e}")
    
    def _save_data(self):
        """Сохраняет данные в файлы"""
        try:
            # Сохраняем разговоры
            with open(self.conversations_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversations, f, ensure_ascii=False, indent=2)
            
            # Сохраняем контекст
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump(self.context, f, ensure_ascii=False, indent=2)
            
            # Сохраняем память
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
            
            self.logger.info("Данные памяти сохранены")
        
        except Exception as e:
            self.logger.error(f"Ошибка сохранения данных памяти: {e}")
    
    def add_message(self, chat_id: str, user_id: str, message: str, 
                   message_type: str = "text", metadata: Dict = None) -> str:
        """
        Добавляет сообщение в память
        
        Args:
            chat_id: ID чата
            user_id: ID пользователя
            message: Текст сообщения
            message_type: Тип сообщения
            metadata: Дополнительные метаданные
        
        Returns:
            ID сообщения
        """
        try:
            message_id = f"msg_{int(datetime.now().timestamp())}_{hash(message) % 10000}"
            
            message_data = {
                'id': message_id,
                'chat_id': chat_id,
                'user_id': user_id,
                'message': message,
                'type': message_type,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            # Добавляем в разговор
            if chat_id not in self.conversations:
                self.conversations[chat_id] = {
                    'chat_id': chat_id,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'messages': [],
                    'participants': set(),
                    'message_count': 0
                }
            
            self.conversations[chat_id]['messages'].append(message_data)
            self.conversations[chat_id]['participants'].add(user_id)
            self.conversations[chat_id]['message_count'] += 1
            self.conversations[chat_id]['updated_at'] = datetime.now().isoformat()
            
            # Ограничиваем размер разговора
            if len(self.conversations[chat_id]['messages']) > self.max_memory_size:
                self.conversations[chat_id]['messages'] = self.conversations[chat_id]['messages'][-self.max_memory_size:]
            
            # Обновляем контекст
            self._update_context(chat_id, message_data)
            
            self._save_data()
            self.logger.info(f"Сообщение {message_id} добавлено в память")
            return message_id
        
        except Exception as e:
            self.logger.error(f"Ошибка добавления сообщения в память: {e}")
            return ""
    
    def get_conversation_history(self, chat_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Получает историю разговора
        
        Args:
            chat_id: ID чата
            limit: Максимальное количество сообщений
        
        Returns:
            Список сообщений
        """
        try:
            if chat_id not in self.conversations:
                return []
            
            messages = self.conversations[chat_id]['messages']
            return messages[-limit:] if limit > 0 else messages
        
        except Exception as e:
            self.logger.error(f"Ошибка получения истории разговора: {e}")
            return []
    
    def get_context(self, chat_id: str) -> Dict[str, Any]:
        """
        Получает контекст разговора
        
        Args:
            chat_id: ID чата
        
        Returns:
            Контекст разговора
        """
        try:
            context = self.context.get(chat_id, {})
            
            # Проверяем актуальность контекста
            if context:
                last_update = context.get('last_update')
                if last_update:
                    last_update_time = datetime.fromisoformat(last_update)
                    if datetime.now() - last_update_time > timedelta(seconds=self.context_ttl):
                        # Контекст устарел
                        context = {}
            
            return context
        
        except Exception as e:
            self.logger.error(f"Ошибка получения контекста: {e}")
            return {}
    
    def _update_context(self, chat_id: str, message_data: Dict[str, Any]):
        """Обновляет контекст разговора"""
        try:
            if chat_id not in self.context:
                self.context[chat_id] = {
                    'last_message': None,
                    'last_user': None,
                    'message_count': 0,
                    'topics': [],
                    'keywords': [],
                    'sentiment': 'neutral',
                    'last_update': None
                }
            
            context = self.context[chat_id]
            
            # Обновляем базовую информацию
            context['last_message'] = message_data['message']
            context['last_user'] = message_data['user_id']
            context['message_count'] += 1
            context['last_update'] = datetime.now().isoformat()
            
            # Извлекаем ключевые слова
            keywords = self._extract_keywords(message_data['message'])
            context['keywords'].extend(keywords)
            
            # Ограничиваем количество ключевых слов
            if len(context['keywords']) > 100:
                context['keywords'] = context['keywords'][-100:]
            
            # Анализируем настроение
            sentiment = self._analyze_sentiment(message_data['message'])
            context['sentiment'] = sentiment
            
            # Определяем темы
            topics = self._extract_topics(message_data['message'])
            context['topics'].extend(topics)
            
            # Ограничиваем количество тем
            if len(context['topics']) > 20:
                context['topics'] = context['topics'][-20:]
        
        except Exception as e:
            self.logger.error(f"Ошибка обновления контекста: {e}")
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Извлекает ключевые слова из текста"""
        try:
            # Простое извлечение ключевых слов
            words = text.lower().split()
            
            # Фильтруем стоп-слова
            stop_words = {
                'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'за', 'при', 'через',
                'а', 'но', 'или', 'что', 'как', 'где', 'когда', 'почему', 'зачем',
                'это', 'то', 'так', 'уже', 'еще', 'только', 'даже', 'все', 'всего',
                'очень', 'много', 'мало', 'больше', 'меньше', 'лучше', 'хуже'
            }
            
            keywords = []
            for word in words:
                # Убираем знаки препинания
                clean_word = ''.join(c for c in word if c.isalnum())
                
                # Фильтруем по длине и стоп-словам
                if (len(clean_word) > 2 and 
                    clean_word not in stop_words and 
                    not clean_word.isdigit()):
                    keywords.append(clean_word)
            
            return keywords[:10]  # Возвращаем максимум 10 ключевых слов
        
        except Exception as e:
            self.logger.error(f"Ошибка извлечения ключевых слов: {e}")
            return []
    
    def _analyze_sentiment(self, text: str) -> str:
        """Анализирует настроение текста"""
        try:
            positive_words = [
                'хорошо', 'отлично', 'супер', 'класс', 'спасибо', 'спасибо большое',
                '👍', '😊', '😄', '❤️', '💕', '😍', '🤗', '🎉', '✅'
            ]
            
            negative_words = [
                'плохо', 'ужасно', 'проблема', 'ошибка', 'не работает', 'не получается',
                '😞', '😢', '😡', '👎', '❌'
            ]
            
            text_lower = text.lower()
            
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count > negative_count:
                return 'positive'
            elif negative_count > positive_count:
                return 'negative'
            else:
                return 'neutral'
        
        except Exception as e:
            self.logger.error(f"Ошибка анализа настроения: {e}")
            return 'neutral'
    
    def _extract_topics(self, text: str) -> List[str]:
        """Извлекает темы из текста"""
        try:
            # Словарь тем и ключевых слов
            topic_keywords = {
                'работа': ['работа', 'рабочий', 'зарплата', 'проект', 'задача', 'дедлайн', 'коллега', 'начальник', 'офис'],
                'семья': ['семья', 'мама', 'папа', 'брат', 'сестра', 'дети', 'ребенок', 'муж', 'жена', 'родители'],
                'здоровье': ['здоровье', 'болезнь', 'врач', 'больница', 'лекарство', 'лечение', 'симптомы', 'анализы'],
                'покупки': ['покупка', 'магазин', 'цена', 'скидка', 'заказ', 'доставка', 'товар', 'покупки'],
                'путешествия': ['путешествие', 'отпуск', 'поездка', 'отель', 'билет', 'самолет', 'поезд', 'автобус'],
                'технологии': ['компьютер', 'телефон', 'интернет', 'программа', 'приложение', 'техника', 'гаджет'],
                'спорт': ['спорт', 'тренировка', 'фитнес', 'бег', 'зал', 'футбол', 'баскетбол', 'плавание'],
                'развлечения': ['фильм', 'сериал', 'музыка', 'книга', 'игра', 'вечеринка', 'концерт', 'театр']
            }
            
            text_lower = text.lower()
            topics = []
            
            for topic, keywords in topic_keywords.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        topics.append(topic)
                        break
            
            return topics
        
        except Exception as e:
            self.logger.error(f"Ошибка извлечения тем: {e}")
            return []
    
    def search_messages(self, query: str, chat_id: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Ищет сообщения по запросу
        
        Args:
            query: Поисковый запрос
            chat_id: ID чата для поиска (опционально)
            limit: Максимальное количество результатов
        
        Returns:
            Список найденных сообщений
        """
        try:
            query_lower = query.lower()
            results = []
            
            # Определяем чаты для поиска
            chat_ids = [chat_id] if chat_id else self.conversations.keys()
            
            for cid in chat_ids:
                if cid not in self.conversations:
                    continue
                
                for message in self.conversations[cid]['messages']:
                    if query_lower in message['message'].lower():
                        results.append(message)
                        
                        if len(results) >= limit:
                            break
                
                if len(results) >= limit:
                    break
            
            # Сортируем по времени (новые первыми)
            results.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return results[:limit]
        
        except Exception as e:
            self.logger.error(f"Ошибка поиска сообщений: {e}")
            return []
    
    def get_conversation_summary(self, chat_id: str) -> Dict[str, Any]:
        """
        Получает краткое резюме разговора
        
        Args:
            chat_id: ID чата
        
        Returns:
            Резюме разговора
        """
        try:
            if chat_id not in self.conversations:
                return {}
            
            conversation = self.conversations[chat_id]
            context = self.get_context(chat_id)
            
            # Подсчитываем статистику
            total_messages = conversation['message_count']
            unique_participants = len(conversation['participants'])
            
            # Время разговора
            if conversation['messages']:
                first_message = conversation['messages'][0]
                last_message = conversation['messages'][-1]
                
                first_time = datetime.fromisoformat(first_message['timestamp'])
                last_time = datetime.fromisoformat(last_message['timestamp'])
                duration = last_time - first_time
            else:
                duration = timedelta(0)
            
            # Основные темы
            topics = context.get('topics', [])
            topic_counts = {}
            for topic in topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            main_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                'chat_id': chat_id,
                'total_messages': total_messages,
                'unique_participants': unique_participants,
                'duration_hours': duration.total_seconds() / 3600,
                'main_topics': main_topics,
                'sentiment': context.get('sentiment', 'neutral'),
                'last_activity': conversation.get('updated_at'),
                'created_at': conversation.get('created_at')
            }
        
        except Exception as e:
            self.logger.error(f"Ошибка получения резюме разговора: {e}")
            return {}
    
    def get_user_activity(self, user_id: str) -> Dict[str, Any]:
        """
        Получает активность пользователя
        
        Args:
            user_id: ID пользователя
        
        Returns:
            Статистика активности пользователя
        """
        try:
            user_messages = 0
            user_chats = set()
            last_activity = None
            
            for chat_id, conversation in self.conversations.items():
                for message in conversation['messages']:
                    if message['user_id'] == user_id:
                        user_messages += 1
                        user_chats.add(chat_id)
                        
                        if not last_activity or message['timestamp'] > last_activity:
                            last_activity = message['timestamp']
            
            return {
                'user_id': user_id,
                'total_messages': user_messages,
                'active_chats': len(user_chats),
                'last_activity': last_activity
            }
        
        except Exception as e:
            self.logger.error(f"Ошибка получения активности пользователя: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30):
        """Очищает старые данные"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_iso = cutoff_date.isoformat()
            
            # Очищаем старые разговоры
            old_conversations = []
            for chat_id, conversation in self.conversations.items():
                if conversation.get('updated_at', '') < cutoff_iso:
                    old_conversations.append(chat_id)
            
            for chat_id in old_conversations:
                del self.conversations[chat_id]
                if chat_id in self.context:
                    del self.context[chat_id]
            
            if old_conversations:
                self._save_data()
                self.logger.info(f"Удалено {len(old_conversations)} старых разговоров")
        
        except Exception as e:
            self.logger.error(f"Ошибка очистки старых данных: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получает статистику памяти"""
        try:
            total_conversations = len(self.conversations)
            total_messages = sum(conv['message_count'] for conv in self.conversations.values())
            
            # Статистика по участникам
            all_participants = set()
            for conversation in self.conversations.values():
                all_participants.update(conversation['participants'])
            
            # Статистика по темам
            all_topics = []
            for context in self.context.values():
                all_topics.extend(context.get('topics', []))
            
            topic_counts = {}
            for topic in all_topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            main_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'unique_participants': len(all_participants),
                'main_topics': main_topics,
                'last_updated': datetime.now().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики памяти: {e}")
            return {}

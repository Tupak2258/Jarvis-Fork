"""
Модуль для AI-анализа Telegram чатов
Использует современные модели для анализа переписок, извлечения информации и понимания контекста
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import aiohttp

# AI модели (опциональные зависимости)
try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    from sentence_transformers import SentenceTransformer
    import torch
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


class TelegramAIAnalyzer:
    """Класс для AI-анализа Telegram чатов"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.ai_available = AI_AVAILABLE
        
        # Инициализация AI моделей
        self.sentiment_analyzer = None
        self.text_classifier = None
        self.sentence_encoder = None
        self.ner_pipeline = None
        
        if self.ai_available:
            self._initialize_ai_models()
        else:
            self.logger.warning("AI модели недоступны. Установите transformers и sentence-transformers")
        
        # Кэш для результатов анализа
        self.analysis_cache = {}
        self.cache_ttl = 3600  # 1 час
        
        # Паттерны для извлечения информации
        self.patterns = {
            'phone': r'(\+?[1-9]\d{1,14})',
            'email': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            'url': r'(https?://[^\s]+)',
            'username': r'@([a-zA-Z0-9_]{5,32})',
            'hashtag': r'#([a-zA-Z0-9_]+)',
            'date': r'(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})',
            'time': r'(\d{1,2}:\d{2}(?::\d{2})?)',
            'money': r'(\d+(?:[.,]\d{2})?\s*(?:руб|р|дол|usd|eur|€|\$))',
            'address': r'([А-Яа-я\s]+,\s*(?:ул|улица|пр|проспект|пер|переулок|д|дом|кв|квартира))',
        }
        
        self.logger.info(f"TelegramAIAnalyzer инициализирован (AI: {'✅' if self.ai_available else '❌'})")
    
    def _initialize_ai_models(self):
        """Инициализирует AI модели"""
        try:
            # Модель для анализа настроения
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="blanchefort/rubert-base-cased-sentiment",
                return_all_scores=True
            )
            
            # Модель для классификации текста
            self.text_classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli"
            )
            
            # Модель для извлечения именованных сущностей
            self.ner_pipeline = pipeline(
                "ner",
                model="DeepPavlov/rubert-base-cased-sentence",
                aggregation_strategy="simple"
            )
            
            # Модель для кодирования предложений
            self.sentence_encoder = SentenceTransformer('cointegrated/rubert-tiny2')
            
            self.logger.info("AI модели успешно загружены")
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки AI моделей: {e}")
            self.ai_available = False
    
    async def analyze_chat_comprehensive(self, messages: List[Dict], 
                                       analysis_type: str = "full") -> Dict[str, Any]:
        """
        Комплексный анализ чата
        
        Args:
            messages: Список сообщений
            analysis_type: Тип анализа (full, sentiment, entities, topics, contacts)
        
        Returns:
            Результат анализа
        """
        try:
            if not messages:
                return {
                    'success': False,
                    'error': 'Нет сообщений для анализа',
                    'total_messages': 0
                }
            
            # Базовый анализ
            basic_analysis = self._analyze_basic_stats(messages)
            
            result = {
                'success': True,
                'basic_stats': basic_analysis,
                'timestamp': datetime.now().isoformat(),
                'analysis_type': analysis_type
            }
            
            # Анализ настроения
            if analysis_type in ['full', 'sentiment']:
                sentiment_analysis = await self._analyze_sentiment(messages)
                result['sentiment'] = sentiment_analysis
            
            # Извлечение сущностей
            if analysis_type in ['full', 'entities']:
                entities = await self._extract_entities(messages)
                result['entities'] = entities
            
            # Анализ тем
            if analysis_type in ['full', 'topics']:
                topics = await self._analyze_topics(messages)
                result['topics'] = topics
            
            # Извлечение контактов
            if analysis_type in ['full', 'contacts']:
                contacts = await self._extract_contacts(messages)
                result['contacts'] = contacts
            
            # Анализ активности
            if analysis_type in ['full', 'activity']:
                activity = self._analyze_activity_patterns(messages)
                result['activity'] = activity
            
            # Классификация сообщений
            if analysis_type in ['full', 'classification']:
                classification = await self._classify_messages(messages)
                result['classification'] = classification
            
            return result
        
        except Exception as e:
            self.logger.error(f"Ошибка комплексного анализа: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_messages': len(messages) if messages else 0
            }
    
    def _analyze_basic_stats(self, messages: List[Dict]) -> Dict[str, Any]:
        """Анализирует базовую статистику чата"""
        try:
            total_messages = len(messages)
            total_text_length = 0
            users = set()
            message_types = {}
            dates = []
            
            for message in messages:
                # Длина текста
                text = message.get('text', '')
                total_text_length += len(text)
                
                # Пользователи
                user = message.get('from', {})
                if user:
                    user_id = user.get('id')
                    if user_id:
                        users.add(user_id)
                
                # Типы сообщений
                msg_type = 'text'
                if 'photo' in message:
                    msg_type = 'photo'
                elif 'document' in message:
                    msg_type = 'document'
                elif 'voice' in message:
                    msg_type = 'voice'
                elif 'video' in message:
                    msg_type = 'video'
                elif 'sticker' in message:
                    msg_type = 'sticker'
                
                message_types[msg_type] = message_types.get(msg_type, 0) + 1
                
                # Даты
                date = message.get('date')
                if date:
                    dates.append(datetime.fromtimestamp(date))
            
            # Временной анализ
            time_analysis = {}
            if dates:
                dates.sort()
                time_analysis = {
                    'first_message': dates[0].isoformat(),
                    'last_message': dates[-1].isoformat(),
                    'duration_days': (dates[-1] - dates[0]).days if len(dates) > 1 else 0,
                    'messages_per_day': total_messages / max(1, (dates[-1] - dates[0]).days) if len(dates) > 1 else total_messages
                }
            
            return {
                'total_messages': total_messages,
                'unique_users': len(users),
                'total_text_length': total_text_length,
                'average_message_length': total_text_length / total_messages if total_messages > 0 else 0,
                'message_types': message_types,
                'time_analysis': time_analysis
            }
        
        except Exception as e:
            self.logger.error(f"Ошибка анализа базовой статистики: {e}")
            return {}
    
    async def _analyze_sentiment(self, messages: List[Dict]) -> Dict[str, Any]:
        """Анализирует настроение сообщений"""
        try:
            if not self.sentiment_analyzer:
                return self._analyze_sentiment_simple(messages)
            
            # Собираем все тексты
            texts = []
            for message in messages:
                text = message.get('text', '')
                if text and len(text.strip()) > 3:  # Игнорируем очень короткие сообщения
                    texts.append(text)
            
            if not texts:
                return {'error': 'Нет текстовых сообщений для анализа'}
            
            # Анализируем настроение
            sentiments = []
            for text in texts[:50]:  # Ограничиваем количество для производительности
                try:
                    result = self.sentiment_analyzer(text)
                    if result and len(result) > 0:
                        sentiments.append(result[0])
                except Exception as e:
                    self.logger.warning(f"Ошибка анализа настроения для текста: {e}")
                    continue
            
            if not sentiments:
                return {'error': 'Не удалось проанализировать настроение'}
            
            # Агрегируем результаты
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            
            for sentiment in sentiments:
                label = sentiment['label'].lower()
                if 'positive' in label or 'позитив' in label:
                    positive_count += 1
                elif 'negative' in label or 'негатив' in label:
                    negative_count += 1
                else:
                    neutral_count += 1
            
            total = len(sentiments)
            
            return {
                'positive_percentage': (positive_count / total) * 100,
                'negative_percentage': (negative_count / total) * 100,
                'neutral_percentage': (neutral_count / total) * 100,
                'overall_sentiment': 'positive' if positive_count > negative_count else 'negative' if negative_count > positive_count else 'neutral',
                'confidence': max(positive_count, negative_count, neutral_count) / total,
                'analyzed_messages': total
            }
        
        except Exception as e:
            self.logger.error(f"Ошибка анализа настроения: {e}")
            return {'error': str(e)}
    
    def _analyze_sentiment_simple(self, messages: List[Dict]) -> Dict[str, Any]:
        """Простой анализ настроения по ключевым словам"""
        try:
            positive_words = [
                'хорошо', 'отлично', 'супер', 'класс', 'спасибо', 'спасибо большое',
                '👍', '😊', '😄', '❤️', '💕', '😍', '🤗', '🎉', '✅', 'отлично',
                'прекрасно', 'замечательно', 'великолепно', 'потрясающе'
            ]
            
            negative_words = [
                'плохо', 'ужасно', 'проблема', 'ошибка', 'не работает', 'не получается',
                '😞', '😢', '😡', '👎', '❌', 'плохо', 'ужасно', 'кошмар', 'беда',
                'проблема', 'ошибка', 'сломалось', 'не работает'
            ]
            
            positive_count = 0
            negative_count = 0
            total_messages = 0
            
            for message in messages:
                text = message.get('text', '').lower()
                if not text:
                    continue
                
                total_messages += 1
                
                for word in positive_words:
                    if word in text:
                        positive_count += 1
                        break
                
                for word in negative_words:
                    if word in text:
                        negative_count += 1
                        break
            
            if total_messages == 0:
                return {'error': 'Нет сообщений для анализа'}
            
            return {
                'positive_percentage': (positive_count / total_messages) * 100,
                'negative_percentage': (negative_count / total_messages) * 100,
                'neutral_percentage': ((total_messages - positive_count - negative_count) / total_messages) * 100,
                'overall_sentiment': 'positive' if positive_count > negative_count else 'negative' if negative_count > positive_count else 'neutral',
                'analyzed_messages': total_messages
            }
        
        except Exception as e:
            self.logger.error(f"Ошибка простого анализа настроения: {e}")
            return {'error': str(e)}
    
    async def _extract_entities(self, messages: List[Dict]) -> Dict[str, List[Dict]]:
        """Извлекает именованные сущности из сообщений"""
        try:
            entities = {
                'persons': [],
                'organizations': [],
                'locations': [],
                'misc': []
            }
            
            if not self.ner_pipeline:
                return self._extract_entities_simple(messages)
            
            # Собираем тексты для анализа
            texts = []
            for message in messages:
                text = message.get('text', '')
                if text and len(text.strip()) > 5:
                    texts.append(text)
            
            if not texts:
                return entities
            
            # Анализируем первые 20 сообщений для производительности
            for text in texts[:20]:
                try:
                    result = self.ner_pipeline(text)
                    for entity in result:
                        entity_type = entity['entity_group'].lower()
                        entity_text = entity['word']
                        confidence = entity['score']
                        
                        if confidence > 0.7:  # Фильтруем по уверенности
                            if entity_type in ['per', 'person']:
                                entities['persons'].append({
                                    'text': entity_text,
                                    'confidence': confidence
                                })
                            elif entity_type in ['org', 'organization']:
                                entities['organizations'].append({
                                    'text': entity_text,
                                    'confidence': confidence
                                })
                            elif entity_type in ['loc', 'location']:
                                entities['locations'].append({
                                    'text': entity_text,
                                    'confidence': confidence
                                })
                            else:
                                entities['misc'].append({
                                    'text': entity_text,
                                    'type': entity_type,
                                    'confidence': confidence
                                })
                
                except Exception as e:
                    self.logger.warning(f"Ошибка извлечения сущностей: {e}")
                    continue
            
            # Удаляем дубликаты
            for key in entities:
                seen = set()
                unique_entities = []
                for entity in entities[key]:
                    text = entity['text'].lower()
                    if text not in seen:
                        seen.add(text)
                        unique_entities.append(entity)
                entities[key] = unique_entities
            
            return entities
        
        except Exception as e:
            self.logger.error(f"Ошибка извлечения сущностей: {e}")
            return {'persons': [], 'organizations': [], 'locations': [], 'misc': []}
    
    def _extract_entities_simple(self, messages: List[Dict]) -> Dict[str, List[Dict]]:
        """Простое извлечение сущностей по паттернам"""
        try:
            entities = {
                'persons': [],
                'organizations': [],
                'locations': [],
                'misc': []
            }
            
            # Паттерны для извлечения
            name_pattern = r'\b[А-Я][а-я]+\s+[А-Я][а-я]+\b'  # Имя Фамилия
            org_pattern = r'\b(?:ООО|ИП|ЗАО|ОАО|ПАО|АО|ТОО|ИП)\s+[А-Яа-я\s]+'  # Организации
            city_pattern = r'\b(?:г\.|город|м\.|место)\s*([А-Я][а-я]+)'  # Города
            
            for message in messages:
                text = message.get('text', '')
                if not text:
                    continue
                
                # Имена
                names = re.findall(name_pattern, text)
                for name in names:
                    entities['persons'].append({'text': name, 'confidence': 0.8})
                
                # Организации
                orgs = re.findall(org_pattern, text)
                for org in orgs:
                    entities['organizations'].append({'text': org, 'confidence': 0.8})
                
                # Города
                cities = re.findall(city_pattern, text)
                for city in cities:
                    entities['locations'].append({'text': city, 'confidence': 0.7})
            
            return entities
        
        except Exception as e:
            self.logger.error(f"Ошибка простого извлечения сущностей: {e}")
            return {'persons': [], 'organizations': [], 'locations': [], 'misc': []}
    
    async def _analyze_topics(self, messages: List[Dict]) -> Dict[str, Any]:
        """Анализирует темы разговора"""
        try:
            # Собираем все тексты
            texts = []
            for message in messages:
                text = message.get('text', '')
                if text and len(text.strip()) > 10:
                    texts.append(text)
            
            if not texts:
                return {'error': 'Нет текстов для анализа тем'}
            
            # Объединяем тексты для анализа
            combined_text = ' '.join(texts[:20])  # Ограничиваем для производительности
            
            # Ключевые слова и темы
            topics = self._extract_topics_simple(combined_text)
            
            return {
                'main_topics': topics,
                'analyzed_messages': len(texts)
            }
        
        except Exception as e:
            self.logger.error(f"Ошибка анализа тем: {e}")
            return {'error': str(e)}
    
    def _extract_topics_simple(self, text: str) -> List[Dict[str, Any]]:
        """Простое извлечение тем по ключевым словам"""
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
            topic_scores = {}
            
            for topic, keywords in topic_keywords.items():
                score = 0
                for keyword in keywords:
                    score += text_lower.count(keyword)
                if score > 0:
                    topic_scores[topic] = score
            
            # Сортируем по количеству упоминаний
            sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
            
            return [
                {'topic': topic, 'mentions': count, 'percentage': (count / sum(topic_scores.values())) * 100}
                for topic, count in sorted_topics[:5]  # Топ-5 тем
            ]
        
        except Exception as e:
            self.logger.error(f"Ошибка извлечения тем: {e}")
            return []
    
    async def _extract_contacts(self, messages: List[Dict]) -> List[Dict[str, Any]]:
        """Извлекает контактную информацию из сообщений"""
        try:
            contacts = []
            
            for message in messages:
                text = message.get('text', '')
                if not text:
                    continue
                
                # Извлекаем по паттернам
                for contact_type, pattern in self.patterns.items():
                    matches = re.findall(pattern, text)
                    for match in matches:
                        contacts.append({
                            'type': contact_type,
                            'value': match,
                            'message_id': message.get('message_id'),
                            'date': message.get('date'),
                            'user_id': message.get('from', {}).get('id')
                        })
            
            # Удаляем дубликаты
            seen = set()
            unique_contacts = []
            for contact in contacts:
                key = (contact['type'], contact['value'].lower())
                if key not in seen:
                    seen.add(key)
                    unique_contacts.append(contact)
            
            return unique_contacts
        
        except Exception as e:
            self.logger.error(f"Ошибка извлечения контактов: {e}")
            return []
    
    def _analyze_activity_patterns(self, messages: List[Dict]) -> Dict[str, Any]:
        """Анализирует паттерны активности в чате"""
        try:
            if not messages:
                return {}
            
            # Группируем сообщения по часам и дням
            hourly_activity = {}
            daily_activity = {}
            user_activity = {}
            
            for message in messages:
                date = message.get('date')
                if not date:
                    continue
                
                dt = datetime.fromtimestamp(date)
                hour = dt.hour
                day = dt.weekday()  # 0 = понедельник
                user_id = message.get('from', {}).get('id')
                
                # Активность по часам
                hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
                
                # Активность по дням
                daily_activity[day] = daily_activity.get(day, 0) + 1
                
                # Активность пользователей
                if user_id:
                    user_activity[user_id] = user_activity.get(user_id, 0) + 1
            
            # Находим пики активности
            peak_hour = max(hourly_activity.items(), key=lambda x: x[1])[0] if hourly_activity else 0
            peak_day = max(daily_activity.items(), key=lambda x: x[1])[0] if daily_activity else 0
            
            # Самый активный пользователь
            most_active_user = max(user_activity.items(), key=lambda x: x[1])[0] if user_activity else None
            
            return {
                'peak_hour': peak_hour,
                'peak_day': peak_day,
                'most_active_user': most_active_user,
                'hourly_distribution': hourly_activity,
                'daily_distribution': daily_activity,
                'user_activity': user_activity
            }
        
        except Exception as e:
            self.logger.error(f"Ошибка анализа активности: {e}")
            return {}
    
    async def _classify_messages(self, messages: List[Dict]) -> Dict[str, Any]:
        """Классифицирует сообщения по типам"""
        try:
            if not self.text_classifier:
                return self._classify_messages_simple(messages)
            
            # Категории для классификации
            categories = [
                "вопрос", "ответ", "просьба", "жалоба", "благодарность", 
                "приветствие", "прощание", "информация", "мнение", "шутка"
            ]
            
            classifications = {}
            
            for message in messages:
                text = message.get('text', '')
                if not text or len(text.strip()) < 5:
                    continue
                
                try:
                    result = self.text_classifier(text, categories)
                    if result and 'labels' in result:
                        best_label = result['labels'][0]
                        best_score = result['scores'][0]
                        
                        if best_score > 0.5:  # Фильтруем по уверенности
                            classifications[best_label] = classifications.get(best_label, 0) + 1
                
                except Exception as e:
                    self.logger.warning(f"Ошибка классификации сообщения: {e}")
                    continue
            
            return classifications
        
        except Exception as e:
            self.logger.error(f"Ошибка классификации сообщений: {e}")
            return {}
    
    def _classify_messages_simple(self, messages: List[Dict]) -> Dict[str, int]:
        """Простая классификация сообщений по ключевым словам"""
        try:
            categories = {
                'вопрос': ['?', 'как', 'что', 'где', 'когда', 'почему', 'зачем', 'кто'],
                'просьба': ['пожалуйста', 'можно', 'помоги', 'сделай', 'отправь', 'пришли'],
                'благодарность': ['спасибо', 'благодарю', 'спасибо большое', 'спасибочки'],
                'приветствие': ['привет', 'здравствуй', 'добро пожаловать', 'hi', 'hello'],
                'прощание': ['пока', 'до свидания', 'увидимся', 'bye', 'goodbye'],
                'информация': ['информация', 'данные', 'сведения', 'факт', 'статистика']
            }
            
            classifications = {}
            
            for message in messages:
                text = message.get('text', '').lower()
                if not text:
                    continue
                
                for category, keywords in categories.items():
                    for keyword in keywords:
                        if keyword in text:
                            classifications[category] = classifications.get(category, 0) + 1
                            break
            
            return classifications
        
        except Exception as e:
            self.logger.error(f"Ошибка простой классификации: {e}")
            return {}
    
    async def generate_chat_summary(self, messages: List[Dict]) -> str:
        """Генерирует краткое резюме чата"""
        try:
            analysis = await self.analyze_chat_comprehensive(messages, "full")
            
            if not analysis.get('success'):
                return f"Ошибка анализа: {analysis.get('error', 'Неизвестная ошибка')}"
            
            basic_stats = analysis.get('basic_stats', {})
            sentiment = analysis.get('sentiment', {})
            topics = analysis.get('topics', {})
            entities = analysis.get('entities', {})
            
            summary_parts = []
            
            # Основная статистика
            summary_parts.append(f"📊 Всего сообщений: {basic_stats.get('total_messages', 0)}")
            summary_parts.append(f"👥 Участников: {basic_stats.get('unique_users', 0)}")
            
            # Настроение
            if sentiment and 'overall_sentiment' in sentiment:
                sentiment_emoji = {
                    'positive': '😊',
                    'negative': '😞',
                    'neutral': '😐'
                }
                emoji = sentiment_emoji.get(sentiment['overall_sentiment'], '😐')
                summary_parts.append(f"{emoji} Настроение: {sentiment['overall_sentiment']}")
            
            # Основные темы
            if topics and 'main_topics' in topics:
                main_topics = topics['main_topics'][:3]  # Топ-3 темы
                if main_topics:
                    topics_text = ', '.join([topic['topic'] for topic in main_topics])
                    summary_parts.append(f"💬 Основные темы: {topics_text}")
            
            # Контакты
            contacts = analysis.get('contacts', [])
            if contacts:
                contact_types = {}
                for contact in contacts:
                    contact_type = contact['type']
                    contact_types[contact_type] = contact_types.get(contact_type, 0) + 1
                
                contact_summary = ', '.join([f"{count} {type}" for type, count in contact_types.items()])
                summary_parts.append(f"📞 Найдено контактов: {contact_summary}")
            
            return '\n'.join(summary_parts)
        
        except Exception as e:
            self.logger.error(f"Ошибка генерации резюме: {e}")
            return f"Ошибка генерации резюме: {e}"
    
    def clear_cache(self):
        """Очищает кэш анализа"""
        self.analysis_cache.clear()
        self.logger.info("Кэш анализа очищен")

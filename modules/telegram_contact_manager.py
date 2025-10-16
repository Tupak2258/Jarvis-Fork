"""
Модуль для управления контактами и чатами в Telegram
Обеспечивает сохранение, поиск и управление контактной информацией
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import re


class TelegramContactManager:
    """Класс для управления контактами и чатами Telegram"""
    
    def __init__(self, data_dir: str = "data"):
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Файлы для хранения данных
        self.contacts_file = self.data_dir / "telegram_contacts.json"
        self.chats_file = self.data_dir / "telegram_chats.json"
        self.conversations_file = self.data_dir / "telegram_conversations.json"
        
        # Кэш данных
        self.contacts = {}
        self.chats = {}
        self.conversations = {}
        
        # Загружаем данные
        self._load_data()
        
        self.logger.info("TelegramContactManager инициализирован")
    
    def _load_data(self):
        """Загружает данные из файлов"""
        try:
            # Загружаем контакты
            if self.contacts_file.exists():
                with open(self.contacts_file, 'r', encoding='utf-8') as f:
                    self.contacts = json.load(f)
            
            # Загружаем чаты
            if self.chats_file.exists():
                with open(self.chats_file, 'r', encoding='utf-8') as f:
                    self.chats = json.load(f)
            
            # Загружаем разговоры
            if self.conversations_file.exists():
                with open(self.conversations_file, 'r', encoding='utf-8') as f:
                    self.conversations = json.load(f)
            
            self.logger.info(f"Загружено: {len(self.contacts)} контактов, {len(self.chats)} чатов, {len(self.conversations)} разговоров")
        
        except Exception as e:
            self.logger.error(f"Ошибка загрузки данных: {e}")
    
    def _save_data(self):
        """Сохраняет данные в файлы"""
        try:
            # Сохраняем контакты
            with open(self.contacts_file, 'w', encoding='utf-8') as f:
                json.dump(self.contacts, f, ensure_ascii=False, indent=2)
            
            # Сохраняем чаты
            with open(self.chats_file, 'w', encoding='utf-8') as f:
                json.dump(self.chats, f, ensure_ascii=False, indent=2)
            
            # Сохраняем разговоры
            with open(self.conversations_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversations, f, ensure_ascii=False, indent=2)
            
            self.logger.info("Данные сохранены")
        
        except Exception as e:
            self.logger.error(f"Ошибка сохранения данных: {e}")
    
    def add_contact(self, contact_data: Dict[str, Any]) -> bool:
        """
        Добавляет контакт
        
        Args:
            contact_data: Данные контакта
        
        Returns:
            True если контакт добавлен успешно
        """
        try:
            contact_id = contact_data.get('id') or contact_data.get('user_id')
            if not contact_id:
                self.logger.error("Не указан ID контакта")
                return False
            
            # Обновляем данные контакта
            if str(contact_id) in self.contacts:
                # Обновляем существующий контакт
                existing_contact = self.contacts[str(contact_id)]
                existing_contact.update(contact_data)
                existing_contact['updated_at'] = datetime.now().isoformat()
            else:
                # Создаем новый контакт
                contact_data['created_at'] = datetime.now().isoformat()
                contact_data['updated_at'] = datetime.now().isoformat()
                self.contacts[str(contact_id)] = contact_data
            
            self._save_data()
            self.logger.info(f"Контакт {contact_id} добавлен/обновлен")
            return True
        
        except Exception as e:
            self.logger.error(f"Ошибка добавления контакта: {e}")
            return False
    
    def get_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Получает контакт по ID"""
        return self.contacts.get(str(contact_id))
    
    def search_contacts(self, query: str) -> List[Dict[str, Any]]:
        """
        Ищет контакты по запросу
        
        Args:
            query: Поисковый запрос
        
        Returns:
            Список найденных контактов
        """
        try:
            query_lower = query.lower()
            results = []
            
            for contact_id, contact in self.contacts.items():
                # Поиск по имени
                first_name = contact.get('first_name', '').lower()
                last_name = contact.get('last_name', '').lower()
                username = contact.get('username', '').lower()
                
                if (query_lower in first_name or 
                    query_lower in last_name or 
                    query_lower in username):
                    results.append(contact)
            
            return results
        
        except Exception as e:
            self.logger.error(f"Ошибка поиска контактов: {e}")
            return []
    
    def add_chat(self, chat_data: Dict[str, Any]) -> bool:
        """
        Добавляет чат
        
        Args:
            chat_data: Данные чата
        
        Returns:
            True если чат добавлен успешно
        """
        try:
            chat_id = chat_data.get('id')
            if not chat_id:
                self.logger.error("Не указан ID чата")
                return False
            
            # Обновляем данные чата
            if str(chat_id) in self.chats:
                # Обновляем существующий чат
                existing_chat = self.chats[str(chat_id)]
                existing_chat.update(chat_data)
                existing_chat['updated_at'] = datetime.now().isoformat()
            else:
                # Создаем новый чат
                chat_data['created_at'] = datetime.now().isoformat()
                chat_data['updated_at'] = datetime.now().isoformat()
                self.chats[str(chat_id)] = chat_data
            
            self._save_data()
            self.logger.info(f"Чат {chat_id} добавлен/обновлен")
            return True
        
        except Exception as e:
            self.logger.error(f"Ошибка добавления чата: {e}")
            return False
    
    def get_chat(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Получает чат по ID"""
        return self.chats.get(str(chat_id))
    
    def search_chats(self, query: str) -> List[Dict[str, Any]]:
        """
        Ищет чаты по запросу
        
        Args:
            query: Поисковый запрос
        
        Returns:
            Список найденных чатов
        """
        try:
            query_lower = query.lower()
            results = []
            
            for chat_id, chat in self.chats.items():
                # Поиск по названию
                title = chat.get('title', '').lower()
                username = chat.get('username', '').lower()
                
                if query_lower in title or query_lower in username:
                    results.append(chat)
            
            return results
        
        except Exception as e:
            self.logger.error(f"Ошибка поиска чатов: {e}")
            return []
    
    def add_conversation(self, conversation_data: Dict[str, Any]) -> bool:
        """
        Добавляет разговор
        
        Args:
            conversation_data: Данные разговора
        
        Returns:
            True если разговор добавлен успешно
        """
        try:
            conversation_id = conversation_data.get('id') or conversation_data.get('chat_id')
            if not conversation_id:
                self.logger.error("Не указан ID разговора")
                return False
            
            # Обновляем данные разговора
            if str(conversation_id) in self.conversations:
                # Обновляем существующий разговор
                existing_conversation = self.conversations[str(conversation_id)]
                existing_conversation.update(conversation_data)
                existing_conversation['updated_at'] = datetime.now().isoformat()
            else:
                # Создаем новый разговор
                conversation_data['created_at'] = datetime.now().isoformat()
                conversation_data['updated_at'] = datetime.now().isoformat()
                self.conversations[str(conversation_id)] = conversation_data
            
            self._save_data()
            self.logger.info(f"Разговор {conversation_id} добавлен/обновлен")
            return True
        
        except Exception as e:
            self.logger.error(f"Ошибка добавления разговора: {e}")
            return False
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Получает разговор по ID"""
        return self.conversations.get(str(conversation_id))
    
    def extract_contacts_from_text(self, text: str) -> List[Dict[str, str]]:
        """
        Извлекает контакты из текста
        
        Args:
            text: Текст для анализа
        
        Returns:
            Список найденных контактов
        """
        try:
            contacts = []
            
            # Паттерны для поиска контактов
            patterns = {
                'phone': r'(\+?[1-9]\d{1,14})',
                'email': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                'url': r'(https?://[^\s]+)',
                'username': r'@([a-zA-Z0-9_]{5,32})',
                'hashtag': r'#([a-zA-Z0-9_]+)'
            }
            
            for contact_type, pattern in patterns.items():
                matches = re.findall(pattern, text)
                for match in matches:
                    contacts.append({
                        'type': contact_type,
                        'value': match,
                        'extracted_at': datetime.now().isoformat()
                    })
            
            return contacts
        
        except Exception as e:
            self.logger.error(f"Ошибка извлечения контактов: {e}")
            return []
    
    def get_contact_statistics(self) -> Dict[str, Any]:
        """Получает статистику контактов"""
        try:
            total_contacts = len(self.contacts)
            total_chats = len(self.chats)
            total_conversations = len(self.conversations)
            
            # Статистика по типам контактов
            contact_types = {}
            for contact in self.contacts.values():
                contact_type = contact.get('type', 'unknown')
                contact_types[contact_type] = contact_types.get(contact_type, 0) + 1
            
            # Статистика по типам чатов
            chat_types = {}
            for chat in self.chats.values():
                chat_type = chat.get('type', 'unknown')
                chat_types[chat_type] = chat_types.get(chat_type, 0) + 1
            
            return {
                'total_contacts': total_contacts,
                'total_chats': total_chats,
                'total_conversations': total_conversations,
                'contact_types': contact_types,
                'chat_types': chat_types,
                'last_updated': datetime.now().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    def export_contacts(self, format: str = 'json') -> str:
        """
        Экспортирует контакты в указанном формате
        
        Args:
            format: Формат экспорта (json, csv)
        
        Returns:
            Путь к файлу экспорта
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if format.lower() == 'json':
                export_file = self.data_dir / f"contacts_export_{timestamp}.json"
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(self.contacts, f, ensure_ascii=False, indent=2)
            
            elif format.lower() == 'csv':
                import csv
                export_file = self.data_dir / f"contacts_export_{timestamp}.csv"
                with open(export_file, 'w', newline='', encoding='utf-8') as f:
                    if self.contacts:
                        writer = csv.DictWriter(f, fieldnames=list(self.contacts.values())[0].keys())
                        writer.writeheader()
                        writer.writerows(self.contacts.values())
            
            else:
                raise ValueError(f"Неподдерживаемый формат: {format}")
            
            self.logger.info(f"Контакты экспортированы в {export_file}")
            return str(export_file)
        
        except Exception as e:
            self.logger.error(f"Ошибка экспорта контактов: {e}")
            return ""
    
    def cleanup_old_data(self, days: int = 30):
        """
        Очищает старые данные
        
        Args:
            days: Количество дней для хранения данных
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_iso = cutoff_date.isoformat()
            
            # Очищаем старые разговоры
            old_conversations = []
            for conv_id, conv in self.conversations.items():
                if conv.get('updated_at', '') < cutoff_iso:
                    old_conversations.append(conv_id)
            
            for conv_id in old_conversations:
                del self.conversations[conv_id]
            
            if old_conversations:
                self._save_data()
                self.logger.info(f"Удалено {len(old_conversations)} старых разговоров")
        
        except Exception as e:
            self.logger.error(f"Ошибка очистки данных: {e}")
    
    def get_recent_contacts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает недавние контакты"""
        try:
            sorted_contacts = sorted(
                self.contacts.values(),
                key=lambda x: x.get('updated_at', ''),
                reverse=True
            )
            return sorted_contacts[:limit]
        
        except Exception as e:
            self.logger.error(f"Ошибка получения недавних контактов: {e}")
            return []
    
    def get_recent_chats(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает недавние чаты"""
        try:
            sorted_chats = sorted(
                self.chats.values(),
                key=lambda x: x.get('updated_at', ''),
                reverse=True
            )
            return sorted_chats[:limit]
        
        except Exception as e:
            self.logger.error(f"Ошибка получения недавних чатов: {e}")
            return []
    
    def search_all(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Ищет по всем данным
        
        Args:
            query: Поисковый запрос
        
        Returns:
            Словарь с результатами поиска
        """
        try:
            return {
                'contacts': self.search_contacts(query),
                'chats': self.search_chats(query),
                'conversations': self.search_conversations(query)
            }
        
        except Exception as e:
            self.logger.error(f"Ошибка поиска: {e}")
            return {'contacts': [], 'chats': [], 'conversations': []}
    
    def search_conversations(self, query: str) -> List[Dict[str, Any]]:
        """Ищет разговоры по запросу"""
        try:
            query_lower = query.lower()
            results = []
            
            for conv_id, conv in self.conversations.items():
                # Поиск по содержимому разговора
                content = conv.get('content', '').lower()
                if query_lower in content:
                    results.append(conv)
            
            return results
        
        except Exception as e:
            self.logger.error(f"Ошибка поиска разговоров: {e}")
            return []

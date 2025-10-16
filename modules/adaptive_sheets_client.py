"""
Адаптивный клиент для работы с данными
Автоматически переключается между Google Sheets и локальным хранилищем
"""

import logging
from typing import List, Dict, Optional, Any
from .sheets_client import GoogleSheetsClient
from .local_sheets_client import LocalSheetsClient


class AdaptiveSheetsClient:
    """Адаптивный клиент, который использует Google Sheets или локальное хранилище"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.google_client = None
        self.local_client = LocalSheetsClient()
        self.using_google = False
        
        # Пытаемся подключиться к Google Sheets
        try:
            from config import GOOGLE_SHEETS_ENABLED
            if GOOGLE_SHEETS_ENABLED:
                self.google_client = GoogleSheetsClient()
                if self.google_client.is_available():
                    self.using_google = True
                    self.logger.info("Используется Google Sheets")
                else:
                    self.logger.warning("Google Sheets недоступен, переключаемся на локальное хранилище")
            else:
                self.logger.info("Google Sheets отключен в настройках, используется локальное хранилище")
        except Exception as e:
            self.logger.warning(f"Ошибка инициализации Google Sheets: {e}")
            self.logger.info("Используется локальное хранилище")
    
    def _get_client(self):
        """Возвращает активный клиент"""
        if self.using_google and self.google_client:
            return self.google_client
        return self.local_client
    
    def is_available(self) -> bool:
        """Проверяет доступность хранилища данных"""
        return True  # Локальное хранилище всегда доступно
    
    def get_storage_type(self) -> str:
        """Возвращает тип используемого хранилища"""
        return "Google Sheets" if self.using_google else "Локальное хранилище"
    
    def log_conversation(self, user_input: str, ai_response: str, command: str = None):
        """Логирует разговор"""
        try:
            client = self._get_client()
            client.log_conversation(user_input, ai_response, command)
        except Exception as e:
            self.logger.error(f"Ошибка логирования разговора: {e}")
            # Fallback на локальное хранилище
            if self.using_google:
                self.local_client.log_conversation(user_input, ai_response, command)
    
    def add_task(self, task: str, priority: str = "Medium", notes: str = "") -> bool:
        """Добавляет задачу"""
        try:
            client = self._get_client()
            return client.add_task(task, priority, notes)
        except Exception as e:
            self.logger.error(f"Ошибка добавления задачи: {e}")
            # Fallback на локальное хранилище
            if self.using_google:
                return self.local_client.add_task(task, priority, notes)
            return False
    
    def get_tasks(self, status: str = None) -> List[Dict[str, Any]]:
        """Получает список задач"""
        try:
            client = self._get_client()
            return client.get_tasks(status)
        except Exception as e:
            self.logger.error(f"Ошибка получения задач: {e}")
            # Fallback на локальное хранилище
            if self.using_google:
                return self.local_client.get_tasks(status)
            return []
    
    def update_task_status(self, task_description: str, new_status: str) -> bool:
        """Обновляет статус задачи"""
        try:
            client = self._get_client()
            return client.update_task_status(task_description, new_status)
        except Exception as e:
            self.logger.error(f"Ошибка обновления статуса задачи: {e}")
            # Fallback на локальное хранилище
            if self.using_google:
                return self.local_client.update_task_status(task_description, new_status)
            return False
    
    def add_note(self, note: str, category: str = "General") -> bool:
        """Добавляет заметку"""
        try:
            client = self._get_client()
            return client.add_note(note, category)
        except Exception as e:
            self.logger.error(f"Ошибка добавления заметки: {e}")
            # Fallback на локальное хранилище
            if self.using_google:
                return self.local_client.add_note(note, category)
            return False
    
    def log_command(self, command: str, result: str, error: str = None):
        """Логирует выполнение команды"""
        try:
            client = self._get_client()
            client.log_command(command, result, error)
        except Exception as e:
            self.logger.error(f"Ошибка логирования команды: {e}")
            # Fallback на локальное хранилище
            if self.using_google:
                self.local_client.log_command(command, result, error)
    
    def search_data(self, query: str, sheet_name: str = "conversations") -> List[Dict]:
        """Поиск данных"""
        try:
            client = self._get_client()
            return client.search_data(query, sheet_name)
        except Exception as e:
            self.logger.error(f"Ошибка поиска данных: {e}")
            # Fallback на локальное хранилище
            if self.using_google:
                return self.local_client.search_data(query, sheet_name)
            return []
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict]:
        """Получает историю разговоров"""
        try:
            client = self._get_client()
            return client.get_conversation_history(limit)
        except Exception as e:
            self.logger.error(f"Ошибка получения истории: {e}")
            # Fallback на локальное хранилище
            if self.using_google:
                return self.local_client.get_conversation_history(limit)
            return []
    
    def export_data(self, sheet_name: str) -> Optional[str]:
        """Экспортирует данные"""
        try:
            client = self._get_client()
            return client.export_data(sheet_name)
        except Exception as e:
            self.logger.error(f"Ошибка экспорта данных: {e}")
            # Fallback на локальное хранилище
            if self.using_google:
                return self.local_client.export_data(sheet_name)
            return None
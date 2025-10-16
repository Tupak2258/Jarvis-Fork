"""
Модуль для работы с Google Sheets API
"""

import gspread
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from google.auth.exceptions import GoogleAuthError
from config import GOOGLE_CREDENTIALS_PATH, SPREADSHEET_NAME, GOOGLE_SPREADSHEET_ID


class GoogleSheetsClient:
    """Клиент для работы с Google Sheets"""
    
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self.logger = logging.getLogger(__name__)
        self._authenticate()
    
    def _authenticate(self):
        """Аутентификация с Google Sheets API"""
        try:
            # Проверяем, включен ли Google Sheets
            from config import GOOGLE_SHEETS_ENABLED
            if not GOOGLE_SHEETS_ENABLED:
                self.logger.info("Google Sheets отключен в настройках")
                return
            
            if not GOOGLE_CREDENTIALS_PATH.exists():
                self.logger.warning(f"Файл credentials не найден: {GOOGLE_CREDENTIALS_PATH}")
                return
            
            self.client = gspread.service_account(filename=str(GOOGLE_CREDENTIALS_PATH))
            self.logger.info("Успешная аутентификация с Google Sheets")
            
        except GoogleAuthError as e:
            self.logger.error(f"Ошибка аутентификации Google: {e}")
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка аутентификации: {e}")
    
    def _get_or_create_spreadsheet(self) -> Optional[gspread.Spreadsheet]:
        """Получает или создает таблицу"""
        if not self.client:
            self.logger.error("Клиент не аутентифицирован")
            return None
        
        try:
            # Сначала пробуем открыть по ID если он указан
            if GOOGLE_SPREADSHEET_ID:
                try:
                    spreadsheet = self.client.open_by_key(GOOGLE_SPREADSHEET_ID)
                    self.logger.info(f"Открыта таблица по ID: {GOOGLE_SPREADSHEET_ID}")
                    
                    # Проверяем и создаем необходимые листы
                    self._ensure_required_sheets(spreadsheet)
                    return spreadsheet
                except Exception as e:
                    self.logger.warning(f"Не удалось открыть таблицу по ID {GOOGLE_SPREADSHEET_ID}: {e}")
            
            # Если ID не указан или не сработал, пробуем по названию
            try:
                spreadsheet = self.client.open(SPREADSHEET_NAME)
                self.logger.info(f"Открыта существующая таблица: {SPREADSHEET_NAME}")
                self._ensure_required_sheets(spreadsheet)
                return spreadsheet
            except gspread.SpreadsheetNotFound:
                # Создание новой таблицы
                spreadsheet = self.client.create(SPREADSHEET_NAME)
                self.logger.info(f"Создана новая таблица: {SPREADSHEET_NAME}")
                
                # Создание базовых листов
                self._setup_default_sheets(spreadsheet)
                return spreadsheet
                
        except Exception as e:
            self.logger.error(f"Ошибка работы с таблицей: {e}")
            return None
    
    def _setup_default_sheets(self, spreadsheet: gspread.Spreadsheet):
        """Настройка базовых листов в новой таблице"""
        try:
            # Лист для логов разговоров
            conversations_sheet = spreadsheet.sheet1
            conversations_sheet.update_title("Conversations")
            conversations_sheet.update('A1:D1', [['Timestamp', 'User Input', 'AI Response', 'Command']])
            
            # Лист для задач и заметок
            tasks_sheet = spreadsheet.add_worksheet(title="Tasks", rows=100, cols=5)
            tasks_sheet.update('A1:E1', [['Date', 'Task', 'Status', 'Priority', 'Notes']])
            
            # Лист для системных команд
            commands_sheet = spreadsheet.add_worksheet(title="Commands", rows=100, cols=4)
            commands_sheet.update('A1:D1', [['Timestamp', 'Command', 'Result', 'Error']])
            
            self.logger.info("Базовые листы созданы")
            
        except Exception as e:
            self.logger.error(f"Ошибка создания базовых листов: {e}")
    
    def _ensure_required_sheets(self, spreadsheet: gspread.Spreadsheet):
        """Проверяет и создает необходимые листы если их нет"""
        try:
            existing_sheets = [ws.title for ws in spreadsheet.worksheets()]
            
            required_sheets = {
                'Conversations': ['Timestamp', 'User Input', 'AI Response', 'Command'],
                'Tasks': ['Date', 'Task', 'Status', 'Priority', 'Notes'],
                'Commands': ['Timestamp', 'Command', 'Result', 'Error'],
                'Work_Reports': ['Дата', 'Время начала', 'Время окончания', 'Задача/Проект', 
                               'Описание работы', 'Статус', 'Время работы (мин)', 
                               'Категория', 'Приоритет', 'Заметки']
            }
            
            for sheet_name, headers in required_sheets.items():
                if sheet_name not in existing_sheets:
                    self.logger.info(f"Создаю лист '{sheet_name}'...")
                    worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=len(headers))
                    worksheet.update('1:1', [headers])
                    
                    # Форматирование заголовков
                    worksheet.format('1:1', {
                        'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
                        'textFormat': {'bold': True}
                    })
                    
                    self.logger.info(f"Лист '{sheet_name}' создан")
                else:
                    self.logger.info(f"Лист '{sheet_name}' уже существует")
                    
        except Exception as e:
            self.logger.error(f"Ошибка проверки/создания листов: {e}")
    
    def is_available(self) -> bool:
        """Проверяет доступность Google Sheets API"""
        return self.client is not None
    
    def log_conversation(self, user_input: str, ai_response: str, command: str = None):
        """
        Логирует разговор в Google Sheets
        
        Args:
            user_input: Ввод пользователя
            ai_response: Ответ ассистента
            command: Выполненная команда (если есть)
        """
        if not self.client:
            return
        
        try:
            spreadsheet = self._get_or_create_spreadsheet()
            if not spreadsheet:
                return
            
            sheet = spreadsheet.worksheet("Conversations")
            
            # Добавление записи
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [timestamp, user_input, ai_response, command or ""]
            
            sheet.append_row(row)
            self.logger.info("Разговор записан в Google Sheets")
            
        except Exception as e:
            self.logger.error(f"Ошибка записи разговора: {e}")
    
    def add_task(self, task: str, priority: str = "Medium", notes: str = "") -> bool:
        """
        Добавляет задачу в таблицу
        
        Args:
            task: Описание задачи
            priority: Приоритет (Low, Medium, High)
            notes: Дополнительные заметки
            
        Returns:
            True если задача добавлена успешно
        """
        if not self.client:
            return False
        
        try:
            spreadsheet = self._get_or_create_spreadsheet()
            if not spreadsheet:
                return False
            
            sheet = spreadsheet.worksheet("Tasks")
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [timestamp, task, "New", priority, notes]
            
            sheet.append_row(row)
            self.logger.info(f"Задача добавлена: {task}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка добавления задачи: {e}")
            return False
    
    def get_tasks(self, status: str = None) -> List[Dict[str, Any]]:
        """
        Получает список задач
        
        Args:
            status: Фильтр по статусу (New, In Progress, Done)
            
        Returns:
            Список задач
        """
        if not self.client:
            return []
        
        try:
            spreadsheet = self._get_or_create_spreadsheet()
            if not spreadsheet:
                return []
            
            sheet = spreadsheet.worksheet("Tasks")
            records = sheet.get_all_records()
            
            tasks = []
            for record in records:
                if status is None or record.get('Status', '').lower() == status.lower():
                    tasks.append(record)
            
            return tasks
            
        except Exception as e:
            self.logger.error(f"Ошибка получения задач: {e}")
            return []
    
    def update_task_status(self, task_description: str, new_status: str) -> bool:
        """
        Обновляет статус задачи
        
        Args:
            task_description: Описание задачи для поиска
            new_status: Новый статус
            
        Returns:
            True если статус обновлен
        """
        if not self.client:
            return False
        
        try:
            spreadsheet = self._get_or_create_spreadsheet()
            if not spreadsheet:
                return False
            
            sheet = spreadsheet.worksheet("Tasks")
            
            # Поиск задачи
            cell = sheet.find(task_description)
            if cell:
                # Обновление статуса (колонка C)
                sheet.update_cell(cell.row, 3, new_status)
                self.logger.info(f"Статус задачи обновлен: {task_description} -> {new_status}")
                return True
            else:
                self.logger.warning(f"Задача не найдена: {task_description}")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления статуса задачи: {e}")
            return False
    
    def log_command(self, command: str, result: str, error: str = None):
        """
        Логирует выполнение системной команды
        
        Args:
            command: Выполненная команда
            result: Результат выполнения
            error: Ошибка (если есть)
        """
        if not self.client:
            return
        
        try:
            spreadsheet = self._get_or_create_spreadsheet()
            if not spreadsheet:
                return
            
            sheet = spreadsheet.worksheet("Commands")
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [timestamp, command, result, error or ""]
            
            sheet.append_row(row)
            self.logger.info("Команда записана в Google Sheets")
            
        except Exception as e:
            self.logger.error(f"Ошибка записи команды: {e}")
    
    def search_data(self, query: str, sheet_name: str = "Conversations") -> List[Dict]:
        """
        Поиск данных в таблице
        
        Args:
            query: Поисковый запрос
            sheet_name: Имя листа для поиска
            
        Returns:
            Список найденных записей
        """
        if not self.client:
            return []
        
        try:
            spreadsheet = self._get_or_create_spreadsheet()
            if not spreadsheet:
                return []
            
            sheet = spreadsheet.worksheet(sheet_name)
            records = sheet.get_all_records()
            
            # Простой поиск по содержанию
            results = []
            for record in records:
                for value in record.values():
                    if query.lower() in str(value).lower():
                        results.append(record)
                        break
            
            return results
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска данных: {e}")
            return []
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict]:
        """
        Получает историю разговоров
        
        Args:
            limit: Количество последних записей
            
        Returns:
            Список записей разговоров
        """
        if not self.client:
            return []
        
        try:
            spreadsheet = self._get_or_create_spreadsheet()
            if not spreadsheet:
                return []
            
            sheet = spreadsheet.worksheet("Conversations")
            records = sheet.get_all_records()
            
            # Возвращаем последние записи
            return records[-limit:] if len(records) > limit else records
            
        except Exception as e:
            self.logger.error(f"Ошибка получения истории: {e}")
            return []
    
    def add_note(self, note: str, category: str = "General") -> bool:
        """
        Добавляет заметку в таблицу
        
        Args:
            note: Текст заметки
            category: Категория заметки
            
        Returns:
            True если заметка добавлена
        """
        return self.add_task(f"[Заметка] {note}", priority="Low", notes=f"Категория: {category}")
    
    def export_data(self, sheet_name: str) -> Optional[str]:
        """
        Экспортирует данные листа в CSV формате
        
        Args:
            sheet_name: Имя листа
            
        Returns:
            CSV данные как строка
        """
        if not self.client:
            return None
        
        try:
            spreadsheet = self._get_or_create_spreadsheet()
            if not spreadsheet:
                return None
            
            sheet = spreadsheet.worksheet(sheet_name)
            return sheet.export(format='csv')
            
        except Exception as e:
            self.logger.error(f"Ошибка экспорта данных: {e}")
            return None
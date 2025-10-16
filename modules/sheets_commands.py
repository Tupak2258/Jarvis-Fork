"""
Модуль обработки голосовых команд для работы с Google Sheets и отчетами
"""

import re
import logging
from typing import Tuple, Optional
from .sheets_client import GoogleSheetsClient
from .reports_manager import ReportsManager


class SheetsCommandProcessor:
    """Класс для обработки команд работы с Google Sheets"""
    
    def __init__(self, sheets_client: GoogleSheetsClient):
        self.sheets_client = sheets_client
        self.reports_manager = ReportsManager(sheets_client)
        self.logger = logging.getLogger(__name__)
        
        # Паттерны команд для Google Sheets
        self.command_patterns = {
            'add_task': [
                r'добавь\s+задачу\s+(.+)',
                r'создай\s+задачу\s+(.+)',
                r'новая\s+задача\s+(.+)',
                r'запиши\s+задачу\s+(.+)',
            ],
            'add_note': [
                r'добавь\s+заметку\s+(.+)',
                r'запиши\s+заметку\s+(.+)',
                r'создай\s+заметку\s+(.+)',
                r'заметка\s+(.+)',
            ],
            'get_tasks': [
                r'покажи\s+задачи',
                r'список\s+задач',
                r'мои\s+задачи',
                r'что\s+у\s+меня\s+в\s+задачах',
            ],
            'update_task': [
                r'задача\s+(.+)\s+выполнена',
                r'завершить\s+задачу\s+(.+)',
                r'закрыть\s+задачу\s+(.+)',
                r'выполнил\s+(.+)',
            ],
            'start_work': [
                r'начинаю\s+работу\s+над\s+(.+)',
                r'начать\s+работу\s+(.+)',
                r'работаю\s+над\s+(.+)',
                r'старт\s+работы\s+(.+)',
            ],
            'end_work': [
                r'заканчиваю\s+работу\s*(.+)?',
                r'завершить\s+работу\s*(.+)?',
                r'стоп\s+работа\s*(.+)?',
                r'конец\s+работы\s*(.+)?',
            ],
            'add_work_entry': [
                r'работал\s+(.+)\s+(\d+)\s+минут',
                r'потратил\s+(\d+)\s+минут\s+на\s+(.+)',
                r'добавь\s+работу\s+(.+)\s+(\d+)\s+минут',
            ],
            'daily_report': [
                r'отчет\s+за\s+день',
                r'дневной\s+отчет',
                r'что\s+я\s+делал\s+сегодня',
                r'отчет\s+за\s+сегодня',
            ],
            'weekly_report': [
                r'отчет\s+за\s+неделю',
                r'недельный\s+отчет',
                r'что\s+я\s+делал\s+на\s+неделе',
            ],
            'current_session': [
                r'текущая\s+работа',
                r'что\s+я\s+сейчас\s+делаю',
                r'активная\s+сессия',
                r'сколько\s+работаю',
            ],
            'search_sheets': [
                r'найди\s+в\s+таблице\s+(.+)',
                r'поиск\s+в\s+sheets\s+(.+)',
                r'найти\s+(.+)\s+в\s+таблице',
            ]
        }
    
    def process_command(self, command: str) -> Tuple[bool, str]:
        """
        Обрабатывает команду для работы с Google Sheets
        
        Args:
            command: Текст команды
            
        Returns:
            Tuple[handled, response]
        """
        if not self.sheets_client.is_available():
            return False, "Google Sheets недоступен. Проверьте настройки."
        
        command = command.lower().strip()
        
        # Проверяем каждый тип команды
        for command_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    return self._execute_command(command_type, match, command)
        
        return False, "Команда не распознана как команда для Google Sheets"
    
    def _execute_command(self, command_type: str, match: re.Match, full_command: str) -> Tuple[bool, str]:
        """Выполняет конкретную команду"""
        
        try:
            if command_type == 'add_task':
                task_text = match.group(1).strip()
                # Определяем приоритет из текста
                priority = self._extract_priority(task_text)
                success = self.sheets_client.add_task(task_text, priority=priority)
                if success:
                    return True, f"Задача добавлена: {task_text}"
                else:
                    return True, "Не удалось добавить задачу"
            
            elif command_type == 'add_note':
                note_text = match.group(1).strip()
                success = self.sheets_client.add_note(note_text)
                if success:
                    return True, f"Заметка добавлена: {note_text}"
                else:
                    return True, "Не удалось добавить заметку"
            
            elif command_type == 'get_tasks':
                tasks = self.sheets_client.get_tasks(status="New")
                if tasks:
                    task_list = "\n".join([f"• {task.get('Task', 'Без названия')}" for task in tasks[:5]])
                    return True, f"Ваши задачи:\n{task_list}"
                else:
                    return True, "У вас нет новых задач"
            
            elif command_type == 'update_task':
                task_description = match.group(1).strip()
                success = self.sheets_client.update_task_status(task_description, "Done")
                if success:
                    return True, f"Задача отмечена как выполненная: {task_description}"
                else:
                    return True, f"Не удалось найти задачу: {task_description}"
            
            elif command_type == 'start_work':
                task = match.group(1).strip()
                category = self._extract_category(task)
                success, message = self.reports_manager.start_work_session(task, category=category)
                return True, message
            
            elif command_type == 'end_work':
                description = match.group(1).strip() if match.group(1) else ""
                success, message = self.reports_manager.end_work_session(description=description)
                return True, message
            
            elif command_type == 'add_work_entry':
                # Два варианта: "работал X Y минут" или "потратил Y минут на X"
                if "потратил" in full_command:
                    duration = int(match.group(1))
                    task = match.group(2).strip()
                else:
                    task = match.group(1).strip()
                    duration = int(match.group(2))
                
                success, message = self.reports_manager.add_work_entry(
                    task=task, 
                    description=f"Работа над: {task}", 
                    duration_minutes=duration
                )
                return True, message
            
            elif command_type == 'daily_report':
                success, report = self.reports_manager.get_daily_report()
                return True, report
            
            elif command_type == 'weekly_report':
                success, report = self.reports_manager.get_weekly_report()
                return True, report
            
            elif command_type == 'current_session':
                success, info = self.reports_manager.get_current_session_info()
                return True, info
            
            elif command_type == 'search_sheets':
                query = match.group(1).strip()
                results = self.sheets_client.search_data(query)
                if results:
                    return True, f"Найдено {len(results)} записей по запросу '{query}'"
                else:
                    return True, f"По запросу '{query}' ничего не найдено"
            
            return False, f"Неизвестный тип команды: {command_type}"
            
        except Exception as e:
            error_msg = f"Ошибка выполнения команды '{command_type}': {e}"
            self.logger.error(error_msg)
            return True, error_msg
    
    def _extract_priority(self, text: str) -> str:
        """Извлекает приоритет из текста задачи"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['срочно', 'важно', 'критично', 'высокий']):
            return "High"
        elif any(word in text_lower for word in ['низкий', 'потом', 'когда-нибудь']):
            return "Low"
        else:
            return "Medium"
    
    def _extract_category(self, text: str) -> str:
        """Извлекает категорию из текста задачи"""
        text_lower = text.lower()
        
        categories = {
            'разработка': ['код', 'программ', 'разработ', 'баг', 'фича', 'api'],
            'документация': ['документ', 'описание', 'инструкц', 'readme'],
            'встречи': ['встреча', 'созвон', 'совещание', 'митинг'],
            'обучение': ['изучение', 'курс', 'обучение', 'чтение'],
            'тестирование': ['тест', 'проверка', 'отладка'],
            'планирование': ['план', 'стратегия', 'анализ']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category.title()
        
        return "Общее"
    
    def get_help_text(self) -> str:
        """Возвращает справку по командам Google Sheets"""
        
        help_text = """
📊 Команды для Google Sheets и отчетов:

📋 Задачи:
• "Добавь задачу исправить баг" - создать задачу
• "Покажи задачи" - список активных задач
• "Задача исправить баг выполнена" - отметить как выполненную

📝 Заметки:
• "Добавь заметку встреча в 15:00" - создать заметку
• "Запиши заметку купить молоко" - быстрая заметка

⏰ Учет времени:
• "Начинаю работу над проектом X" - начать сессию
• "Заканчиваю работу сделал API" - завершить сессию
• "Работал над багом 30 минут" - добавить запись

📊 Отчеты:
• "Отчет за день" - дневная статистика
• "Отчет за неделю" - недельный отчет
• "Что я сейчас делаю" - текущая сессия

🔍 Поиск:
• "Найди в таблице проект X" - поиск по таблицам
        """.strip()
        
        return help_text
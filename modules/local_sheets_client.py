"""
Локальная версия клиента для работы с данными (CSV файлы)
Используется когда Google Sheets недоступен
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any


class LocalSheetsClient:
    """Локальный клиент для работы с данными в CSV файлах"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path("data/local_sheets")
        self.data_dir.mkdir(exist_ok=True)
        
        # Файлы для разных типов данных
        self.files = {
            'conversations': self.data_dir / 'conversations.csv',
            'tasks': self.data_dir / 'tasks.csv',
            'commands': self.data_dir / 'commands.csv',
            'work_reports': self.data_dir / 'work_reports.csv'
        }
        
        self._ensure_files_exist()
        self.logger.info("Локальный клиент данных инициализирован")
    
    def _ensure_files_exist(self):
        """Создает CSV файлы если они не существуют"""
        
        headers = {
            'conversations': ['Timestamp', 'User Input', 'AI Response', 'Command'],
            'tasks': ['Date', 'Task', 'Status', 'Priority', 'Notes'],
            'commands': ['Timestamp', 'Command', 'Result', 'Error'],
            'work_reports': ['Дата', 'Время начала', 'Время окончания', 'Задача/Проект',
                           'Описание работы', 'Статус', 'Время работы (мин)', 
                           'Категория', 'Приоритет', 'Заметки']
        }
        
        for file_type, filepath in self.files.items():
            if not filepath.exists():
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers[file_type])
                self.logger.info(f"Создан файл: {filepath}")
    
    def is_available(self) -> bool:
        """Проверяет доступность локального хранилища"""
        return True
    
    def log_conversation(self, user_input: str, ai_response: str, command: str = None):
        """Логирует разговор в CSV файл"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [timestamp, user_input, ai_response, command or ""]
            
            with open(self.files['conversations'], 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
            
            self.logger.info("Разговор записан в локальный файл")
        except Exception as e:
            self.logger.error(f"Ошибка записи разговора: {e}")
    
    def add_task(self, task: str, priority: str = "Medium", notes: str = "") -> bool:
        """Добавляет задачу в CSV файл"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [timestamp, task, "New", priority, notes]
            
            with open(self.files['tasks'], 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
            
            self.logger.info(f"Задача добавлена: {task}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка добавления задачи: {e}")
            return False
    
    def get_tasks(self, status: str = None) -> List[Dict[str, Any]]:
        """Получает список задач из CSV файла"""
        try:
            tasks = []
            with open(self.files['tasks'], 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if status is None or row.get('Status', '').lower() == status.lower():
                        tasks.append(row)
            return tasks
        except Exception as e:
            self.logger.error(f"Ошибка получения задач: {e}")
            return []
    
    def update_task_status(self, task_description: str, new_status: str) -> bool:
        """Обновляет статус задачи в CSV файле"""
        try:
            # Читаем все задачи
            tasks = []
            with open(self.files['tasks'], 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                tasks = list(reader)
            
            # Ищем и обновляем задачу
            updated = False
            for task in tasks:
                if task_description.lower() in task.get('Task', '').lower():
                    task['Status'] = new_status
                    updated = True
                    break
            
            if updated:
                # Записываем обратно
                with open(self.files['tasks'], 'w', newline='', encoding='utf-8') as f:
                    if tasks:
                        writer = csv.DictWriter(f, fieldnames=tasks[0].keys())
                        writer.writeheader()
                        writer.writerows(tasks)
                
                self.logger.info(f"Статус задачи обновлен: {task_description} -> {new_status}")
                return True
            else:
                self.logger.warning(f"Задача не найдена: {task_description}")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления статуса задачи: {e}")
            return False
    
    def add_note(self, note: str, category: str = "General") -> bool:
        """Добавляет заметку как задачу с низким приоритетом"""
        return self.add_task(f"[Заметка] {note}", priority="Low", notes=f"Категория: {category}")
    
    def log_command(self, command: str, result: str, error: str = None):
        """Логирует выполнение команды"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [timestamp, command, result, error or ""]
            
            with open(self.files['commands'], 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
            
            self.logger.info("Команда записана в локальный файл")
        except Exception as e:
            self.logger.error(f"Ошибка записи команды: {e}")
    
    def search_data(self, query: str, sheet_name: str = "conversations") -> List[Dict]:
        """Поиск данных в CSV файлах"""
        try:
            file_mapping = {
                'conversations': 'conversations',
                'tasks': 'tasks',
                'commands': 'commands',
                'work_reports': 'work_reports'
            }
            
            file_key = file_mapping.get(sheet_name.lower(), 'conversations')
            results = []
            
            with open(self.files[file_key], 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    for value in row.values():
                        if query.lower() in str(value).lower():
                            results.append(row)
                            break
            
            return results
        except Exception as e:
            self.logger.error(f"Ошибка поиска данных: {e}")
            return []
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict]:
        """Получает историю разговоров"""
        try:
            conversations = []
            with open(self.files['conversations'], 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                conversations = list(reader)
            
            return conversations[-limit:] if len(conversations) > limit else conversations
        except Exception as e:
            self.logger.error(f"Ошибка получения истории: {e}")
            return []
    
    def add_work_report(self, data: List) -> bool:
        """Добавляет запись в отчет о работе"""
        try:
            with open(self.files['work_reports'], 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(data)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка добавления записи в отчет: {e}")
            return False
    
    def get_work_reports(self) -> List[Dict]:
        """Получает все записи отчетов о работе"""
        try:
            reports = []
            with open(self.files['work_reports'], 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                reports = list(reader)
            return reports
        except Exception as e:
            self.logger.error(f"Ошибка получения отчетов: {e}")
            return []
    
    def export_data(self, sheet_name: str) -> Optional[str]:
        """Экспортирует данные в CSV формате"""
        try:
            file_mapping = {
                'conversations': 'conversations',
                'tasks': 'tasks', 
                'commands': 'commands',
                'work_reports': 'work_reports'
            }
            
            file_key = file_mapping.get(sheet_name.lower())
            if not file_key or not self.files[file_key].exists():
                return None
            
            with open(self.files[file_key], 'r', encoding='utf-8') as f:
                return f.read()
                
        except Exception as e:
            self.logger.error(f"Ошибка экспорта данных: {e}")
            return None
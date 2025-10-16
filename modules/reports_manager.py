"""
Модуль для создания и управления отчетами в Google Sheets
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import gspread
from .sheets_client import GoogleSheetsClient


class ReportsManager:
    """Класс для управления отчетами о работе"""
    
    def __init__(self, sheets_client: GoogleSheetsClient):
        self.sheets_client = sheets_client
        self.logger = logging.getLogger(__name__)
        self.reports_sheet_name = "Work_Reports"
        self._ensure_reports_sheet()
    
    def _ensure_reports_sheet(self):
        """Создает лист отчетов если он не существует"""
        if not self.sheets_client.is_available():
            return
        
        try:
            spreadsheet = self.sheets_client._get_or_create_spreadsheet()
            if not spreadsheet:
                return
            
            # Проверяем существование листа отчетов
            try:
                spreadsheet.worksheet(self.reports_sheet_name)
                self.logger.info("Лист отчетов найден")
            except gspread.WorksheetNotFound:
                # Создаем лист отчетов
                reports_sheet = spreadsheet.add_worksheet(
                    title=self.reports_sheet_name, 
                    rows=1000, 
                    cols=10
                )
                
                # Настраиваем заголовки
                headers = [
                    'Дата', 'Время начала', 'Время окончания', 'Задача/Проект',
                    'Описание работы', 'Статус', 'Время работы (мин)', 
                    'Категория', 'Приоритет', 'Заметки'
                ]
                reports_sheet.update('A1:J1', [headers])
                
                # Форматирование заголовков
                reports_sheet.format('A1:J1', {
                    'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
                    'textFormat': {'bold': True}
                })
                
                self.logger.info("Лист отчетов создан")
                
        except Exception as e:
            self.logger.error(f"Ошибка создания листа отчетов: {e}")
    
    def start_work_session(self, task: str, category: str = "Общее", priority: str = "Средний") -> Tuple[bool, str]:
        """
        Начинает рабочую сессию
        
        Args:
            task: Название задачи/проекта
            category: Категория работы
            priority: Приоритет задачи
            
        Returns:
            Tuple[success, message]
        """
        if not self.sheets_client.is_available():
            return False, "Google Sheets недоступен"
        
        try:
            spreadsheet = self.sheets_client._get_or_create_spreadsheet()
            if not spreadsheet:
                return False, "Не удалось получить доступ к таблице"
            
            sheet = spreadsheet.worksheet(self.reports_sheet_name)
            
            # Добавляем запись о начале работы
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")
            
            row = [
                date_str,           # Дата
                time_str,           # Время начала
                "",                 # Время окончания (пустое)
                task,               # Задача/Проект
                "",                 # Описание (заполнится при завершении)
                "В процессе",       # Статус
                "",                 # Время работы (вычислится при завершении)
                category,           # Категория
                priority,           # Приоритет
                f"Начато в {time_str}"  # Заметки
            ]
            
            sheet.append_row(row)
            
            self.logger.info(f"Начата рабочая сессия: {task}")
            return True, f"Рабочая сессия начата: {task} ({category})"
            
        except Exception as e:
            error_msg = f"Ошибка начала рабочей сессии: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def end_work_session(self, description: str = "", notes: str = "") -> Tuple[bool, str]:
        """
        Завершает текущую рабочую сессию
        
        Args:
            description: Описание выполненной работы
            notes: Дополнительные заметки
            
        Returns:
            Tuple[success, message]
        """
        if not self.sheets_client.is_available():
            return False, "Google Sheets недоступен"
        
        try:
            spreadsheet = self.sheets_client._get_or_create_spreadsheet()
            if not spreadsheet:
                return False, "Не удалось получить доступ к таблице"
            
            sheet = spreadsheet.worksheet(self.reports_sheet_name)
            
            # Находим последнюю незавершенную сессию
            records = sheet.get_all_records()
            last_active_row = None
            
            for i, record in enumerate(records, start=2):  # Начинаем с 2 (после заголовка)
                if record.get('Статус') == 'В процессе':
                    last_active_row = i
            
            if not last_active_row:
                return False, "Нет активных рабочих сессий для завершения"
            
            # Вычисляем время работы
            start_time_str = sheet.cell(last_active_row, 2).value  # Время начала
            start_time = datetime.strptime(f"{datetime.now().strftime('%Y-%m-%d')} {start_time_str}", "%Y-%m-%d %H:%M:%S")
            end_time = datetime.now()
            work_duration = int((end_time - start_time).total_seconds() / 60)  # в минутах
            
            # Обновляем запись
            end_time_str = end_time.strftime("%H:%M:%S")
            
            # Обновляем ячейки
            sheet.update_cell(last_active_row, 3, end_time_str)  # Время окончания
            sheet.update_cell(last_active_row, 5, description)   # Описание работы
            sheet.update_cell(last_active_row, 6, "Завершено")   # Статус
            sheet.update_cell(last_active_row, 7, work_duration) # Время работы
            
            # Обновляем заметки
            current_notes = sheet.cell(last_active_row, 10).value or ""
            updated_notes = f"{current_notes}. Завершено в {end_time_str}. {notes}".strip(". ")
            sheet.update_cell(last_active_row, 10, updated_notes)
            
            task_name = sheet.cell(last_active_row, 4).value
            
            self.logger.info(f"Завершена рабочая сессия: {task_name} ({work_duration} мин)")
            return True, f"Рабочая сессия завершена: {task_name} ({work_duration} минут)"
            
        except Exception as e:
            error_msg = f"Ошибка завершения рабочей сессии: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def add_work_entry(self, task: str, description: str, duration_minutes: int, 
                      category: str = "Общее", priority: str = "Средний", 
                      date: str = None) -> Tuple[bool, str]:
        """
        Добавляет запись о работе (без отслеживания времени)
        
        Args:
            task: Название задачи
            description: Описание работы
            duration_minutes: Продолжительность в минутах
            category: Категория
            priority: Приоритет
            date: Дата (если не указана, используется текущая)
            
        Returns:
            Tuple[success, message]
        """
        if not self.sheets_client.is_available():
            return False, "Google Sheets недоступен"
        
        try:
            spreadsheet = self.sheets_client._get_or_create_spreadsheet()
            if not spreadsheet:
                return False, "Не удалось получить доступ к таблице"
            
            sheet = spreadsheet.worksheet(self.reports_sheet_name)
            
            # Используем текущую дату если не указана
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            # Вычисляем примерное время начала и окончания
            now = datetime.now()
            start_time = (now - timedelta(minutes=duration_minutes)).strftime("%H:%M:%S")
            end_time = now.strftime("%H:%M:%S")
            
            row = [
                date,               # Дата
                start_time,         # Время начала
                end_time,           # Время окончания
                task,               # Задача/Проект
                description,        # Описание работы
                "Завершено",        # Статус
                duration_minutes,   # Время работы
                category,           # Категория
                priority,           # Приоритет
                f"Добавлено вручную в {now.strftime('%H:%M:%S')}"  # Заметки
            ]
            
            sheet.append_row(row)
            
            self.logger.info(f"Добавлена запись о работе: {task} ({duration_minutes} мин)")
            return True, f"Запись добавлена: {task} ({duration_minutes} минут)"
            
        except Exception as e:
            error_msg = f"Ошибка добавления записи: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_daily_report(self, date: str = None) -> Tuple[bool, str]:
        """
        Генерирует отчет за день
        
        Args:
            date: Дата в формате YYYY-MM-DD (если не указана, используется текущая)
            
        Returns:
            Tuple[success, report_text]
        """
        if not self.sheets_client.is_available():
            return False, "Google Sheets недоступен"
        
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            spreadsheet = self.sheets_client._get_or_create_spreadsheet()
            if not spreadsheet:
                return False, "Не удалось получить доступ к таблице"
            
            sheet = spreadsheet.worksheet(self.reports_sheet_name)
            records = sheet.get_all_records()
            
            # Фильтруем записи за указанную дату
            daily_records = [r for r in records if r.get('Дата') == date]
            
            if not daily_records:
                return True, f"За {date} записей о работе не найдено"
            
            # Генерируем отчет
            total_time = sum(int(r.get('Время работы (мин)', 0) or 0) for r in daily_records)
            completed_tasks = len([r for r in daily_records if r.get('Статус') == 'Завершено'])
            in_progress_tasks = len([r for r in daily_records if r.get('Статус') == 'В процессе'])
            
            # Группируем по категориям
            categories = {}
            for record in daily_records:
                cat = record.get('Категория', 'Общее')
                if cat not in categories:
                    categories[cat] = {'time': 0, 'tasks': 0}
                categories[cat]['time'] += int(record.get('Время работы (мин)', 0) or 0)
                categories[cat]['tasks'] += 1
            
            report = f"""
📊 Отчет за {date}:

⏱️ Общее время работы: {total_time} минут ({total_time//60}ч {total_time%60}м)
✅ Завершенных задач: {completed_tasks}
🔄 Задач в процессе: {in_progress_tasks}

📋 По категориям:"""
            
            for cat, data in categories.items():
                report += f"\n• {cat}: {data['time']} мин ({data['tasks']} задач)"
            
            if daily_records:
                report += "\n\n📝 Задачи:"
                for record in daily_records:
                    task = record.get('Задача/Проект', 'Без названия')
                    time_spent = record.get('Время работы (мин)', 0) or 0
                    status = record.get('Статус', 'Неизвестно')
                    report += f"\n• {task}: {time_spent} мин ({status})"
            
            return True, report.strip()
            
        except Exception as e:
            error_msg = f"Ошибка генерации отчета: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_weekly_report(self) -> Tuple[bool, str]:
        """Генерирует отчет за неделю"""
        if not self.sheets_client.is_available():
            return False, "Google Sheets недоступен"
        
        try:
            # Вычисляем даты недели
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            
            spreadsheet = self.sheets_client._get_or_create_spreadsheet()
            if not spreadsheet:
                return False, "Не удалось получить доступ к таблице"
            
            sheet = spreadsheet.worksheet(self.reports_sheet_name)
            records = sheet.get_all_records()
            
            # Фильтруем записи за неделю
            week_records = []
            for i in range(7):
                date = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
                day_records = [r for r in records if r.get('Дата') == date]
                week_records.extend(day_records)
            
            if not week_records:
                return True, "За эту неделю записей о работе не найдено"
            
            # Статистика
            total_time = sum(int(r.get('Время работы (мин)', 0) or 0) for r in week_records)
            total_tasks = len(week_records)
            completed_tasks = len([r for r in week_records if r.get('Статус') == 'Завершено'])
            
            # По дням
            daily_stats = {}
            for i in range(7):
                date = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
                day_name = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][i]
                day_records = [r for r in records if r.get('Дата') == date]
                day_time = sum(int(r.get('Время работы (мин)', 0) or 0) for r in day_records)
                daily_stats[f"{day_name} ({date})"] = {'time': day_time, 'tasks': len(day_records)}
            
            report = f"""
📊 Недельный отчет ({week_start.strftime('%Y-%m-%d')} - {(week_start + timedelta(days=6)).strftime('%Y-%m-%d')}):

⏱️ Общее время: {total_time} минут ({total_time//60}ч {total_time%60}м)
📋 Всего задач: {total_tasks}
✅ Завершено: {completed_tasks}
📈 Эффективность: {(completed_tasks/total_tasks*100):.1f}%

📅 По дням:"""
            
            for day, stats in daily_stats.items():
                if stats['time'] > 0:
                    report += f"\n• {day}: {stats['time']} мин ({stats['tasks']} задач)"
            
            return True, report.strip()
            
        except Exception as e:
            error_msg = f"Ошибка генерации недельного отчета: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_current_session_info(self) -> Tuple[bool, str]:
        """Получает информацию о текущей рабочей сессии"""
        if not self.sheets_client.is_available():
            return False, "Google Sheets недоступен"
        
        try:
            spreadsheet = self.sheets_client._get_or_create_spreadsheet()
            if not spreadsheet:
                return False, "Не удалось получить доступ к таблице"
            
            sheet = spreadsheet.worksheet(self.reports_sheet_name)
            records = sheet.get_all_records()
            
            # Ищем активную сессию
            active_session = None
            for record in records:
                if record.get('Статус') == 'В процессе':
                    active_session = record
                    break
            
            if not active_session:
                return True, "Нет активных рабочих сессий"
            
            # Вычисляем время работы
            start_time_str = active_session.get('Время начала', '')
            if start_time_str:
                start_time = datetime.strptime(f"{datetime.now().strftime('%Y-%m-%d')} {start_time_str}", "%Y-%m-%d %H:%M:%S")
                current_time = datetime.now()
                work_duration = int((current_time - start_time).total_seconds() / 60)
                
                task = active_session.get('Задача/Проект', 'Без названия')
                category = active_session.get('Категория', 'Общее')
                
                info = f"""
🔄 Активная рабочая сессия:
📋 Задача: {task}
📂 Категория: {category}
⏰ Начало: {start_time_str}
⏱️ Время работы: {work_duration} минут ({work_duration//60}ч {work_duration%60}м)
                """.strip()
                
                return True, info
            else:
                return True, "Активная сессия найдена, но время начала не определено"
                
        except Exception as e:
            error_msg = f"Ошибка получения информации о сессии: {e}"
            self.logger.error(error_msg)
            return False, error_msg
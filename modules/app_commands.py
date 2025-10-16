"""
Модуль обработки голосовых команд для управления приложениями
"""

import re
import logging
from typing import Tuple, Optional
from .app_manager import AppManager


class AppCommandProcessor:
    """Класс для обработки голосовых команд управления приложениями"""
    
    def __init__(self, app_manager: AppManager):
        self.app_manager = app_manager
        self.logger = logging.getLogger(__name__)
        
        # Паттерны команд
        self.command_patterns = {
            'open_app': [
                r'открой\s+(.+)',
                r'запусти\s+(.+)',
                r'включи\s+(.+)',
                r'открыть\s+(.+)',
                r'запустить\s+(.+)',
            ],
            'close_app': [
                r'закрой\s+(.+)',
                r'выключи\s+(.+)',
                r'завершить?\s+(.+)',
                r'остановить?\s+(.+)',
                r'закрыть\s+(.+)',
                r'убей\s+(.+)',
                r'выйти\s+из\s+(.+)',
                r'выход\s+из\s+(.+)',
                r'стоп\s+(.+)',
            ],
            'type_text': [
                r'напиши\s+(?!в\s+чат)(.+)',  # Исключаем "напиши в чат"
                r'введи\s+(?!в\s+чат)(.+)',   # Исключаем "введи в чат"
                r'печатай\s+(.+)',
                r'набери\s+(.+)',
                r'вставь\s+текст\s+(.+)',
            ],
            'send_keys': [
                r'нажми\s+(.+)',
                r'клавиши\s+(.+)',
                r'комбинация\s+(.+)',
                r'сочетание\s+(.+)',
            ],
            'focus_window': [
                r'переключись\s+на\s+(.+)',
                r'перейди\s+к\s+(.+)',
                r'активируй\s+(.+)',
                r'фокус\s+на\s+(.+)',
            ],
            'list_apps': [
                r'покажи\s+приложения',
                r'список\s+программ',
                r'что\s+запущено',
                r'какие\s+программы\s+открыты',
            ],
            'save_file': [
                r'сохрани\s+файл',
                r'сохранить',
                r'ctrl\s*\+\s*s',
            ],
            'copy_text': [
                r'скопируй',
                r'копировать',
                r'ctrl\s*\+\s*c',
            ],
            'paste_text': [
                r'вставь',
                r'вставить',
                r'ctrl\s*\+\s*v',
            ],
            'select_all': [
                r'выдели\s+всё',
                r'выделить\s+всё',
                r'ctrl\s*\+\s*a',
            ],
            'undo': [
                r'отмени',
                r'отменить',
                r'ctrl\s*\+\s*z',
            ],
            'new_file': [
                r'новый\s+файл',
                r'создай\s+файл',
                r'ctrl\s*\+\s*n',
            ]
        }
        
        # Маппинг клавиш
        self.key_mapping = {
            'энтер': 'enter',
            'ввод': 'enter',
            'пробел': 'space',
            'таб': 'tab',
            'эскейп': 'esc',
            'бэкспейс': 'backspace',
            'удалить': 'delete',
            'стрелка вверх': 'up',
            'стрелка вниз': 'down',
            'стрелка влево': 'left',
            'стрелка вправо': 'right',
            'контрол': 'ctrl',
            'альт': 'alt',
            'шифт': 'shift',
            'виндовс': 'win',
        }
    
    def process_command(self, command: str) -> Tuple[bool, str]:
        """
        Обрабатывает голосовую команду
        
        Args:
            command: Текст команды
            
        Returns:
            Tuple[handled, response]
        """
        command = command.lower().strip()
        
        # Проверяем каждый тип команды
        for command_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    return self._execute_command(command_type, match, command)
        
        return False, "Команда не распознана как команда управления приложениями"
    
    def _execute_command(self, command_type: str, match: re.Match, full_command: str) -> Tuple[bool, str]:
        """Выполняет конкретную команду"""
        
        try:
            if command_type == 'open_app':
                app_name = match.group(1).strip()
                self.logger.info(f"Обработка команды открытия: '{app_name}'")
                success, message = self.app_manager.open_app(app_name)
                
                # Если не удалось найти, предлагаем помощь
                if not success and "не найдено" in message.lower():
                    # Добавляем дополнительную информацию
                    help_message = message + "\n💡 Попробуйте использовать точное название программы или проверьте, установлена ли она."
                    return True, help_message
                
                return True, message
            
            elif command_type == 'close_app':
                app_name = match.group(1).strip()
                success, message = self.app_manager.close_app(app_name)
                return True, message
            
            elif command_type == 'type_text':
                text = match.group(1).strip()
                success, message = self.app_manager.type_text(text)
                return True, message
            
            elif command_type == 'send_keys':
                keys = self._translate_keys(match.group(1).strip())
                success, message = self.app_manager.send_keys(keys)
                return True, message
            
            elif command_type == 'focus_window':
                window_title = match.group(1).strip()
                success, message = self.app_manager.focus_window(window_title)
                return True, message
            
            elif command_type == 'list_apps':
                return self._list_running_apps()
            
            elif command_type == 'save_file':
                success, message = self.app_manager.send_keys('ctrl+s')
                return True, "Файл сохранен"
            
            elif command_type == 'copy_text':
                success, message = self.app_manager.send_keys('ctrl+c')
                return True, "Текст скопирован"
            
            elif command_type == 'paste_text':
                success, message = self.app_manager.send_keys('ctrl+v')
                return True, "Текст вставлен"
            
            elif command_type == 'select_all':
                success, message = self.app_manager.send_keys('ctrl+a')
                return True, "Весь текст выделен"
            
            elif command_type == 'undo':
                success, message = self.app_manager.send_keys('ctrl+z')
                return True, "Действие отменено"
            
            elif command_type == 'new_file':
                success, message = self.app_manager.send_keys('ctrl+n')
                return True, "Создан новый файл"
            
            return False, f"Неизвестный тип команды: {command_type}"
            
        except Exception as e:
            error_msg = f"Ошибка выполнения команды '{command_type}': {e}"
            self.logger.error(error_msg)
            return True, error_msg
    
    def _translate_keys(self, keys_text: str) -> str:
        """Переводит русские названия клавиш в английские"""
        
        keys_text = keys_text.lower()
        
        # Заменяем русские названия
        for russian, english in self.key_mapping.items():
            keys_text = keys_text.replace(russian, english)
        
        # Обрабатываем комбинации
        keys_text = keys_text.replace(' плюс ', '+')
        keys_text = keys_text.replace(' и ', '+')
        keys_text = keys_text.replace('контрол с', 'ctrl+s')
        keys_text = keys_text.replace('контрол а', 'ctrl+a')
        keys_text = keys_text.replace('контрол в', 'ctrl+v')
        keys_text = keys_text.replace('контрол с', 'ctrl+c')
        keys_text = keys_text.replace('контрол з', 'ctrl+z')
        keys_text = keys_text.replace('контрол н', 'ctrl+n')
        
        return keys_text.strip()
    
    def _list_running_apps(self) -> Tuple[bool, str]:
        """Возвращает список запущенных приложений"""
        try:
            running_apps = self.app_manager.get_running_apps()
            
            if not running_apps:
                return True, "Нет запущенных приложений"
            
            # Группируем по именам и считаем
            app_counts = {}
            for app in running_apps:
                name = app['name'].replace('.exe', '')
                app_counts[name] = app_counts.get(name, 0) + 1
            
            # Формируем ответ
            app_list = []
            for name, count in sorted(app_counts.items()):
                if count > 1:
                    app_list.append(f"{name} ({count} процесса)")
                else:
                    app_list.append(name)
            
            # Берем только первые 10 для краткости
            if len(app_list) > 10:
                response = f"Запущено {len(app_list)} приложений. Основные: " + ", ".join(app_list[:10])
            else:
                response = "Запущенные приложения: " + ", ".join(app_list)
            
            return True, response
            
        except Exception as e:
            error_msg = f"Ошибка получения списка приложений: {e}"
            self.logger.error(error_msg)
            return True, error_msg
    
    def get_help_text(self) -> str:
        """Возвращает справку по командам"""
        
        help_text = """
🖥️ Команды управления приложениями:

📂 Открытие/закрытие:
• "Открой блокнот" - открыть приложение
• "Запусти браузер" - запустить программу  
• "Закрой калькулятор" - закрыть приложение

⌨️ Ввод текста:
• "Напиши привет мир" - ввести текст
• "Введи мой email" - напечатать текст

🎯 Управление клавишами:
• "Нажми энтер" - нажать клавишу
• "Сохрани файл" - Ctrl+S
• "Скопируй" - Ctrl+C
• "Вставь" - Ctrl+V
• "Выдели всё" - Ctrl+A

🔄 Переключение окон:
• "Переключись на блокнот" - активировать окно
• "Перейди к браузеру" - фокус на приложение

📋 Информация:
• "Покажи приложения" - список запущенных программ
• "Что запущено" - активные процессы
        """.strip()
        
        return help_text
"""
Модуль обработки голосовых команд для работы с Telegram
Улучшенная версия с поддержкой Bot API и AI-анализа
"""

import re
import logging
import asyncio
import json
from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path

# Импорты модулей
from .telegram_manager import TelegramManager
from .vision_analyzer import VisionAnalyzer
from .adaptive_sheets_client import AdaptiveSheetsClient

# Новые модули
try:
    from .telegram_bot_api import TelegramBotAPI
    from .telegram_ai_analyzer import TelegramAIAnalyzer
    TELEGRAM_API_AVAILABLE = True
except ImportError:
    TELEGRAM_API_AVAILABLE = False


class TelegramCommandProcessor:
    """Класс для обработки команд работы с Telegram"""
    
    def __init__(self, sheets_client: AdaptiveSheetsClient):
        self.telegram_manager = TelegramManager()
        self.vision_analyzer = VisionAnalyzer()
        self.sheets_client = sheets_client
        self.logger = logging.getLogger(__name__)
        
        # Инициализация новых компонентов
        self.bot_api = None
        self.ai_analyzer = None
        self.telegram_api_available = TELEGRAM_API_AVAILABLE
        
        if self.telegram_api_available:
            try:
                self.bot_api = TelegramBotAPI()
                self.ai_analyzer = TelegramAIAnalyzer()
                self.logger.info("Telegram Bot API и AI анализатор инициализированы")
            except Exception as e:
                self.logger.warning(f"Не удалось инициализировать Telegram API: {e}")
                self.telegram_api_available = False
        
        # Кэш для чатов и контактов
        self.chats_cache = {}
        self.contacts_cache = {}
        self.conversation_memory = {}
        
        # Настройки
        self.max_messages_for_analysis = 100
        self.analysis_cache_ttl = 3600  # 1 час
        
        # Паттерны команд для Telegram
        self.command_patterns = {
            'open_telegram': [
                r'открой\s+телеграм',
                r'запусти\s+telegram',
                r'включи\s+телеграм',
                r'открыть\s+telegram',
            ],
            'open_chat': [
                r'открой\s+чат\s+(.+)',
                r'перейди\s+к\s+чату\s+(.+)',
                r'найди\s+чат\s+(.+)',
                r'открыть\s+диалог\s+(.+)',
            ],
            'read_chat': [
                r'прочитай\s+чат',
                r'что\s+в\s+чате',
                r'покажи\s+сообщения',
                r'анализируй\s+чат',
                r'что\s+пишут',
            ],
            'send_message': [
                r'напиши\s+в\s+чат\s+(.+)',
                r'отправь\s+сообщение\s+(.+)',
                r'отправь\s+в\s+чат\s+(.+)',
                r'пошли\s+в\s+чат\s+(.+)',
                r'написать\s+в\s+чат\s+(.+)',
                r'сообщение\s+в\s+чат\s+(.+)',
                r'текст\s+в\s+чат\s+(.+)',
            ],
            'send_message_to_chat': [
                r'напиши\s+в\s+чат\s+([^:]+):\s*(.+)',
                r'отправь\s+в\s+чат\s+([^:]+):\s*(.+)',
                r'напиши\s+(.+)\s+в\s+чат\s+(.+)',
                r'отправь\s+сообщение\s+(.+)\s+в\s+чат\s+(.+)',
            ],
            'extract_data': [
                r'извлеки\s+данные\s+из\s+чата',
                r'перенеси\s+(.+)\s+в\s+таблицу',
                r'сохрани\s+(.+)\s+в\s+sheets',
                r'экспортируй\s+(.+)',
            ],
            'analyze_chat': [
                r'анализируй\s+чат\s+(.+)',
                r'что\s+происходит\s+в\s+чате',
                r'настроение\s+в\s+чате',
                r'анализ\s+переписки',
            ],
            'scroll_chat': [
                r'прокрути\s+чат\s+(вверх|вниз)',
                r'листай\s+(вверх|вниз)',
                r'скролл\s+(up|down|вверх|вниз)',
            ],
            'take_screenshot': [
                r'сделай\s+скриншот\s+телеграма',
                r'скриншот\s+чата',
                r'сфотографируй\s+экран',
            ],
            'find_contacts': [
                r'найди\s+контакты\s+в\s+чате',
                r'извлеки\s+номера\s+телефонов',
                r'покажи\s+участников',
            ],
            'send_message_api': [
                r'отправь\s+через\s+бота\s+(.+)',
                r'напиши\s+через\s+api\s+(.+)',
                r'бот\s+отправь\s+(.+)',
            ],
            'analyze_chat_ai': [
                r'анализируй\s+чат\s+с\s+ии',
                r'полный\s+анализ\s+чата',
                r'умный\s+анализ\s+переписки',
                r'анализ\s+с\s+искусственным\s+интеллектом',
            ],
            'get_chat_summary': [
                r'резюме\s+чата',
                r'краткое\s+описание\s+переписки',
                r'суть\s+разговора',
                r'что\s+обсуждалось',
            ],
            'search_messages': [
                r'найди\s+сообщения\s+(.+)',
                r'поиск\s+в\s+чате\s+(.+)',
                r'ищи\s+(.+)',
            ],
            'get_chat_info': [
                r'информация\s+о\s+чате',
                r'статистика\s+чата',
                r'данные\s+о\s+переписке',
            ],
            'schedule_message': [
                r'запланируй\s+сообщение\s+(.+)',
                r'отложить\s+отправку\s+(.+)',
                r'написать\s+позже\s+(.+)',
            ],
            'manage_contacts': [
                r'управление\s+контактами',
                r'список\s+контактов',
                r'сохранить\s+контакт',
            ]
        }
    
    def process_command(self, command: str) -> Tuple[bool, str]:
        """
        Обрабатывает команду для работы с Telegram
        
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
        
        return False, "Команда не распознана как команда для Telegram"
    
    def _execute_command(self, command_type: str, match: re.Match, full_command: str) -> Tuple[bool, str]:
        """Выполняет конкретную команду"""
        
        try:
            if command_type == 'open_telegram':
                return self._open_telegram()
            
            elif command_type == 'open_chat':
                chat_name = match.group(1).strip()
                return self._open_chat(chat_name)
            
            elif command_type == 'read_chat':
                return self._read_chat()
            
            elif command_type == 'send_message':
                message = match.group(1).strip()
                return self._send_message(message)
            
            elif command_type == 'send_message_to_chat':
                # Определяем, какой шаблон сработал: с двоеточием или без
                if match.lastindex and match.lastindex >= 2:
                    first = match.group(1).strip()
                    second = match.group(2).strip()
                    # Если первый аргумент содержит пробелы и нет двоеточия, это может быть сообщение
                    # Проверяем эвристически: если второй короче и без пробелов — вероятно это имя чата
                    if ':' in full_command or (len(first) < len(second) and ' ' not in second):
                        chat_name = first
                        message = second
                    else:
                        message = first
                        chat_name = second
                else:
                    return False, 'Не удалось распознать чат и сообщение'
                open_ok, open_msg = self._open_chat(chat_name)
                if not open_ok:
                    return False, open_msg
                return self._send_message(message)
            
            elif command_type == 'extract_data':
                data_type = match.group(1).strip() if match.groups() else "все данные"
                return self._extract_data(data_type)
            
            elif command_type == 'analyze_chat':
                analysis_type = match.group(1).strip() if match.groups() else "общий"
                return self._analyze_chat(analysis_type)
            
            elif command_type == 'scroll_chat':
                direction = match.group(1).strip()
                return self._scroll_chat(direction)
            
            elif command_type == 'take_screenshot':
                return self._take_screenshot()
            
            elif command_type == 'find_contacts':
                return self._find_contacts()
            
            elif command_type == 'send_message_api':
                message = match.group(1).strip()
                return self._send_message_api(message)
            
            elif command_type == 'analyze_chat_ai':
                return self._analyze_chat_ai()
            
            elif command_type == 'get_chat_summary':
                return self._get_chat_summary()
            
            elif command_type == 'search_messages':
                query = match.group(1).strip()
                return self._search_messages(query)
            
            elif command_type == 'get_chat_info':
                return self._get_chat_info()
            
            elif command_type == 'schedule_message':
                message = match.group(1).strip()
                return self._schedule_message(message)
            
            elif command_type == 'manage_contacts':
                return self._manage_contacts()
            
            return False, f"Неизвестный тип команды: {command_type}"
            
        except Exception as e:
            error_msg = f"Ошибка выполнения команды '{command_type}': {e}"
            self.logger.error(error_msg)
            return True, error_msg
    
    def _open_telegram(self) -> Tuple[bool, str]:
        """Открывает Telegram"""
        try:
            if self.telegram_manager.is_telegram_running():
                if self.telegram_manager.activate_telegram():
                    return True, "Telegram активирован"
                else:
                    return True, "Telegram запущен, но не удалось активировать окно"
            else:
                # Пытаемся запустить Telegram через app_manager
                try:
                    from .app_manager import AppManager
                    app_manager = AppManager()
                    success, message = app_manager.open_app("telegram")
                    if success:
                        # Ждем запуска и ищем окно
                        import time
                        time.sleep(3)
                        if self.telegram_manager.find_telegram_window():
                            return True, "Telegram запущен и готов к работе"
                        else:
                            return True, "Telegram запущен, но окно не найдено"
                    else:
                        return False, f"Не удалось запустить Telegram: {message}"
                except ImportError:
                    return False, "Telegram не запущен и не удалось его запустить"
        except Exception as e:
            return False, f"Ошибка открытия Telegram: {e}"
    
    def _open_chat(self, chat_name: str) -> Tuple[bool, str]:
        """Открывает чат по имени"""
        try:
            if not self.telegram_manager.is_telegram_running():
                open_result = self._open_telegram()
                if not open_result[0]:
                    return False, f"Не удалось открыть Telegram: {open_result[1]}"
            
            if self.telegram_manager.open_chat(chat_name):
                return True, f"Чат '{chat_name}' открыт"
            else:
                return False, f"Не удалось открыть чат '{chat_name}'"
                
        except Exception as e:
            return False, f"Ошибка открытия чата: {e}"
    
    def _read_chat(self) -> Tuple[bool, str]:
        """Читает и анализирует текущий чат"""
        try:
            if not self.telegram_manager.is_telegram_running():
                return False, "Telegram не запущен"
            
            # Делаем скриншот
            screenshot_path = self.telegram_manager.take_screenshot()
            if not screenshot_path:
                return False, "Не удалось сделать скриншот"
            
            # Анализируем с помощью QwenVL
            analysis = self.vision_analyzer.analyze_telegram_screenshot(
                screenshot_path, 
                analysis_type="messages"
            )
            
            if analysis.get('success'):
                response = analysis['response']
                # Сохраняем анализ в таблицу
                self._save_analysis_to_sheets("Анализ чата", response, screenshot_path)
                return True, f"Анализ чата:\n{response}"
            else:
                return False, f"Ошибка анализа: {analysis.get('error', 'Неизвестная ошибка')}"
                
        except Exception as e:
            return False, f"Ошибка чтения чата: {e}"
    
    def _send_message(self, message: str) -> Tuple[bool, str]:
        """Отправляет сообщение в активный чат"""
        try:
            self.logger.info(f"Начинаем отправку сообщения: {message}")
            
            # Проверяем, запущен ли Telegram (улучшенная проверка)
            if not self.telegram_manager.is_telegram_running():
                error_msg = "Telegram не запущен или недоступен"
                self.logger.error(error_msg)
                return False, error_msg
            
            self.logger.info("Telegram найден и запущен")
            
            # Активируем Telegram
            if not self.telegram_manager.activate_telegram():
                error_msg = "Не удалось активировать окно Telegram"
                self.logger.error(error_msg)
                return False, error_msg
            
            self.logger.info("Окно Telegram активировано")
            
            # Отправляем сообщение
            if self.telegram_manager.send_message(message):
                success_msg = f"Сообщение отправлено в Telegram: {message}"
                self.logger.info(success_msg)
                return True, success_msg
            else:
                error_msg = "Не удалось отправить сообщение в Telegram"
                self.logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Ошибка отправки сообщения в Telegram: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _extract_data(self, data_type: str) -> Tuple[bool, str]:
        """Извлекает данные из чата и сохраняет в таблицу"""
        try:
            if not self.telegram_manager.is_telegram_running():
                return False, "Telegram не запущен"
            
            # Делаем скриншот
            screenshot_path = self.telegram_manager.take_screenshot()
            if not screenshot_path:
                return False, "Не удалось сделать скриншот"
            
            # Определяем типы данных для извлечения
            data_types = self._parse_data_types(data_type)
            
            # Извлекаем структурированные данные
            structured_data = self.vision_analyzer.extract_structured_data(
                screenshot_path, 
                data_types
            )
            
            if structured_data:
                # Сохраняем в Google Sheets
                saved_count = self._save_structured_data_to_sheets(structured_data, data_type)
                
                # Формируем отчет
                report = self._format_extraction_report(structured_data, saved_count)
                return True, report
            else:
                return False, "Не удалось извлечь данные из чата"
                
        except Exception as e:
            return False, f"Ошибка извлечения данных: {e}"
    
    def _analyze_chat(self, analysis_type: str) -> Tuple[bool, str]:
        """Анализирует чат по заданному типу"""
        try:
            if not self.telegram_manager.is_telegram_running():
                return False, "Telegram не запущен"
            
            screenshot_path = self.telegram_manager.take_screenshot()
            if not screenshot_path:
                return False, "Не удалось сделать скриншот"
            
            # Определяем тип анализа
            if any(word in analysis_type.lower() for word in ['настроение', 'эмоции', 'sentiment']):
                analysis = self.vision_analyzer.analyze_chat_sentiment(screenshot_path)
            else:
                analysis = self.vision_analyzer.analyze_telegram_screenshot(
                    screenshot_path, 
                    analysis_type="general"
                )
            
            if analysis.get('success'):
                response = analysis.get('sentiment_analysis') or analysis.get('response', '')
                self._save_analysis_to_sheets(f"Анализ чата: {analysis_type}", response, screenshot_path)
                return True, f"Анализ завершен:\n{response}"
            else:
                return False, f"Ошибка анализа: {analysis.get('error', 'Неизвестная ошибка')}"
                
        except Exception as e:
            return False, f"Ошибка анализа чата: {e}"
    
    def _scroll_chat(self, direction: str) -> Tuple[bool, str]:
        """Прокручивает чат"""
        try:
            if not self.telegram_manager.is_telegram_running():
                return False, "Telegram не запущен"
            
            # Переводим направление
            scroll_direction = 'up' if direction in ['вверх', 'up'] else 'down'
            
            if self.telegram_manager.scroll_chat(scroll_direction, count=3):
                return True, f"Чат прокручен {direction}"
            else:
                return False, "Не удалось прокрутить чат"
                
        except Exception as e:
            return False, f"Ошибка прокрутки: {e}"
    
    def _take_screenshot(self) -> Tuple[bool, str]:
        """Делает скриншот Telegram"""
        try:
            if not self.telegram_manager.is_telegram_running():
                return False, "Telegram не запущен"
            
            screenshot_path = self.telegram_manager.take_screenshot()
            if screenshot_path:
                return True, f"Скриншот сохранен: {screenshot_path}"
            else:
                return False, "Не удалось сделать скриншот"
                
        except Exception as e:
            return False, f"Ошибка создания скриншота: {e}"
    
    def _find_contacts(self) -> Tuple[bool, str]:
        """Находит контакты в чате"""
        try:
            if not self.telegram_manager.is_telegram_running():
                return False, "Telegram не запущен"
            
            screenshot_path = self.telegram_manager.take_screenshot()
            if not screenshot_path:
                return False, "Не удалось сделать скриншот"
            
            # Извлекаем контакты
            contacts_data = self.vision_analyzer.extract_structured_data(
                screenshot_path, 
                ['contacts']
            )
            
            if contacts_data.get('contacts'):
                contacts = contacts_data['contacts']
                # Сохраняем в таблицу
                self._save_contacts_to_sheets(contacts)
                
                contacts_list = '\n'.join([f"• {contact}" for contact in contacts])
                return True, f"Найденные контакты:\n{contacts_list}"
            else:
                return True, "Контакты в чате не найдены"
                
        except Exception as e:
            return False, f"Ошибка поиска контактов: {e}"
    
    def _parse_data_types(self, data_type_str: str) -> list:
        """Парсит строку типов данных"""
        data_type_str = data_type_str.lower()
        
        type_mapping = {
            'контакты': 'contacts',
            'даты': 'dates', 
            'числа': 'numbers',
            'задачи': 'tasks',
            'ссылки': 'links',
            'все': ['contacts', 'dates', 'numbers', 'tasks', 'links']
        }
        
        for key, value in type_mapping.items():
            if key in data_type_str:
                return value if isinstance(value, list) else [value]
        
        return ['contacts', 'dates', 'numbers', 'tasks']  # По умолчанию
    
    def _save_structured_data_to_sheets(self, structured_data: Dict, data_type: str) -> int:
        """Сохраняет структурированные данные в Google Sheets"""
        try:
            saved_count = 0
            timestamp = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            for data_category, items in structured_data.items():
                if items:  # Если есть данные этого типа
                    for item in items:
                        # Добавляем как задачу с категорией
                        success = self.sheets_client.add_task(
                            task=f"[Telegram {data_category}] {item}",
                            priority="Medium",
                            notes=f"Извлечено из Telegram чата в {timestamp}"
                        )
                        if success:
                            saved_count += 1
            
            return saved_count
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения данных в таблицу: {e}")
            return 0
    
    def _save_analysis_to_sheets(self, title: str, analysis: str, screenshot_path: str):
        """Сохраняет анализ в Google Sheets"""
        try:
            timestamp = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.sheets_client.add_task(
                task=f"[Анализ Telegram] {title}",
                priority="Low",
                notes=f"Анализ: {analysis[:500]}... Скриншот: {screenshot_path} Время: {timestamp}"
            )
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения анализа: {e}")
    
    def _save_contacts_to_sheets(self, contacts: list):
        """Сохраняет контакты в Google Sheets"""
        try:
            timestamp = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            for contact in contacts:
                self.sheets_client.add_task(
                    task=f"[Контакт Telegram] {contact}",
                    priority="Low",
                    notes=f"Найден в Telegram чате {timestamp}"
                )
                
        except Exception as e:
            self.logger.error(f"Ошибка сохранения контактов: {e}")
    
    def _format_extraction_report(self, structured_data: Dict, saved_count: int) -> str:
        """Форматирует отчет об извлечении данных"""
        report_lines = [f"📊 Извлечение данных завершено. Сохранено записей: {saved_count}\n"]
        
        for data_type, items in structured_data.items():
            if items:
                type_names = {
                    'contacts': '👥 Контакты',
                    'dates': '📅 Даты',
                    'numbers': '🔢 Числа',
                    'tasks': '✅ Задачи',
                    'links': '🔗 Ссылки'
                }
                
                type_name = type_names.get(data_type, data_type.title())
                report_lines.append(f"{type_name} ({len(items)}):")
                
                for item in items[:3]:  # Показываем первые 3
                    report_lines.append(f"  • {item}")
                
                if len(items) > 3:
                    report_lines.append(f"  ... и еще {len(items) - 3}")
                
                report_lines.append("")
        
        return '\n'.join(report_lines)
    
    def _send_message_api(self, message: str) -> Tuple[bool, str]:
        """Отправляет сообщение через Telegram Bot API"""
        try:
            if not self.telegram_api_available or not self.bot_api:
                return False, "Telegram Bot API недоступен"
            
            # Получаем ID чата из кэша или запрашиваем у пользователя
            chat_id = self._get_current_chat_id()
            if not chat_id:
                return False, "Не указан ID чата. Сначала откройте чат"
            
            # Отправляем сообщение асинхронно
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success = loop.run_until_complete(
                    self.bot_api.send_message(chat_id, message)
                )
                if success:
                    return True, f"Сообщение отправлено через Bot API: {message}"
                else:
                    return False, "Не удалось отправить сообщение через Bot API"
            finally:
                loop.close()
        
        except Exception as e:
            return False, f"Ошибка отправки через Bot API: {e}"
    
    def _analyze_chat_ai(self) -> Tuple[bool, str]:
        """Анализирует чат с использованием AI"""
        try:
            if not self.telegram_api_available or not self.ai_analyzer:
                return False, "AI анализатор недоступен"
            
            # Получаем ID чата
            chat_id = self._get_current_chat_id()
            if not chat_id:
                return False, "Не указан ID чата. Сначала откройте чат"
            
            # Получаем сообщения через Bot API
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                messages = loop.run_until_complete(
                    self.bot_api.get_chat_history(chat_id, self.max_messages_for_analysis)
                )
                
                if not messages:
                    return False, "Не удалось получить сообщения для анализа"
                
                # Анализируем с помощью AI
                analysis = loop.run_until_complete(
                    self.ai_analyzer.analyze_chat_comprehensive(messages, "full")
                )
                
                if analysis.get('success'):
                    # Форматируем результат
                    result = self._format_ai_analysis(analysis)
                    return True, result
                else:
                    return False, f"Ошибка AI анализа: {analysis.get('error', 'Неизвестная ошибка')}"
            
            finally:
                loop.close()
        
        except Exception as e:
            return False, f"Ошибка AI анализа: {e}"
    
    def _get_chat_summary(self) -> Tuple[bool, str]:
        """Получает краткое резюме чата"""
        try:
            if not self.telegram_api_available or not self.ai_analyzer:
                return False, "AI анализатор недоступен"
            
            chat_id = self._get_current_chat_id()
            if not chat_id:
                return False, "Не указан ID чата"
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                messages = loop.run_until_complete(
                    self.bot_api.get_chat_history(chat_id, self.max_messages_for_analysis)
                )
                
                if not messages:
                    return False, "Нет сообщений для анализа"
                
                summary = loop.run_until_complete(
                    self.ai_analyzer.generate_chat_summary(messages)
                )
                
                return True, f"📋 Резюме чата:\n{summary}"
            
            finally:
                loop.close()
        
        except Exception as e:
            return False, f"Ошибка получения резюме: {e}"
    
    def _search_messages(self, query: str) -> Tuple[bool, str]:
        """Ищет сообщения в чате"""
        try:
            if not self.telegram_api_available or not self.bot_api:
                return False, "Telegram Bot API недоступен"
            
            chat_id = self._get_current_chat_id()
            if not chat_id:
                return False, "Не указан ID чата"
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                messages = loop.run_until_complete(
                    self.bot_api.search_messages(chat_id, query, 20)
                )
                
                if not messages:
                    return True, f"По запросу '{query}' ничего не найдено"
                
                # Форматируем результаты
                results = []
                for i, msg in enumerate(messages[:10], 1):  # Показываем первые 10
                    text = msg.get('text', '')[:100] + '...' if len(msg.get('text', '')) > 100 else msg.get('text', '')
                    date = datetime.fromtimestamp(msg.get('date', 0)).strftime('%d.%m.%Y %H:%M')
                    results.append(f"{i}. {text} ({date})")
                
                return True, f"🔍 Найдено {len(messages)} сообщений по запросу '{query}':\n\n" + '\n'.join(results)
            
            finally:
                loop.close()
        
        except Exception as e:
            return False, f"Ошибка поиска: {e}"
    
    def _get_chat_info(self) -> Tuple[bool, str]:
        """Получает информацию о чате"""
        try:
            if not self.telegram_api_available or not self.bot_api:
                return False, "Telegram Bot API недоступен"
            
            chat_id = self._get_current_chat_id()
            if not chat_id:
                return False, "Не указан ID чата"
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                chat_info = loop.run_until_complete(
                    self.bot_api.get_chat_info(chat_id)
                )
                
                if not chat_info:
                    return False, "Не удалось получить информацию о чате"
                
                # Форматируем информацию
                info_lines = [
                    f"📊 Информация о чате:",
                    f"• Название: {chat_info.get('title', 'Не указано')}",
                    f"• Тип: {chat_info.get('type', 'Неизвестно')}",
                    f"• ID: {chat_info.get('id')}",
                ]
                
                if 'username' in chat_info:
                    info_lines.append(f"• Username: @{chat_info['username']}")
                
                # Получаем количество участников
                members_count = loop.run_until_complete(
                    self.bot_api.get_chat_members_count(chat_id)
                )
                if members_count:
                    info_lines.append(f"• Участников: {members_count}")
                
                return True, '\n'.join(info_lines)
            
            finally:
                loop.close()
        
        except Exception as e:
            return False, f"Ошибка получения информации: {e}"
    
    def _schedule_message(self, message: str) -> Tuple[bool, str]:
        """Планирует отправку сообщения (заглушка)"""
        try:
            # Это базовая реализация - в реальном проекте нужна система планирования
            return True, f"📅 Планирование сообщений пока не реализовано. Сообщение: '{message}'"
        
        except Exception as e:
            return False, f"Ошибка планирования: {e}"
    
    def _manage_contacts(self) -> Tuple[bool, str]:
        """Управляет контактами"""
        try:
            if not self.telegram_api_available or not self.bot_api:
                return False, "Telegram Bot API недоступен"
            
            chat_id = self._get_current_chat_id()
            if not chat_id:
                return False, "Не указан ID чата"
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                contacts = loop.run_until_complete(
                    self.bot_api.extract_contacts_from_chat(chat_id, 50)
                )
                
                if not contacts:
                    return True, "Контакты в чате не найдены"
                
                # Группируем по типам
                contact_types = {}
                for contact in contacts:
                    contact_type = contact['type']
                    if contact_type not in contact_types:
                        contact_types[contact_type] = []
                    contact_types[contact_type].append(contact['value'])
                
                # Форматируем результат
                result_lines = ["📞 Найденные контакты:"]
                for contact_type, values in contact_types.items():
                    type_names = {
                        'phone': '📱 Телефоны',
                        'email': '📧 Email',
                        'username': '👤 Usernames',
                        'url': '🔗 Ссылки'
                    }
                    type_name = type_names.get(contact_type, contact_type.title())
                    result_lines.append(f"\n{type_name}:")
                    for value in values[:5]:  # Показываем первые 5
                        result_lines.append(f"  • {value}")
                    if len(values) > 5:
                        result_lines.append(f"  ... и еще {len(values) - 5}")
                
                return True, '\n'.join(result_lines)
            
            finally:
                loop.close()
        
        except Exception as e:
            return False, f"Ошибка управления контактами: {e}"
    
    def _get_current_chat_id(self) -> Optional[str]:
        """Получает ID текущего чата из кэша"""
        # В реальной реализации это должно быть более сложно
        # Пока возвращаем None - нужно будет реализовать логику определения чата
        return None
    
    def _format_ai_analysis(self, analysis: Dict[str, Any]) -> str:
        """Форматирует результат AI анализа"""
        try:
            result_lines = ["🤖 Результат AI анализа чата:"]
            
            # Базовая статистика
            basic_stats = analysis.get('basic_stats', {})
            if basic_stats:
                result_lines.extend([
                    f"\n📊 Статистика:",
                    f"• Сообщений: {basic_stats.get('total_messages', 0)}",
                    f"• Участников: {basic_stats.get('unique_users', 0)}",
                    f"• Средняя длина: {basic_stats.get('average_message_length', 0):.1f} символов"
                ])
            
            # Настроение
            sentiment = analysis.get('sentiment', {})
            if sentiment and 'overall_sentiment' in sentiment:
                sentiment_emoji = {
                    'positive': '😊',
                    'negative': '😞',
                    'neutral': '😐'
                }
                emoji = sentiment_emoji.get(sentiment['overall_sentiment'], '😐')
                result_lines.extend([
                    f"\n{emoji} Настроение: {sentiment['overall_sentiment']}",
                    f"• Позитивных: {sentiment.get('positive_percentage', 0):.1f}%",
                    f"• Негативных: {sentiment.get('negative_percentage', 0):.1f}%"
                ])
            
            # Темы
            topics = analysis.get('topics', {})
            if topics and 'main_topics' in topics:
                main_topics = topics['main_topics'][:3]
                if main_topics:
                    topics_text = ', '.join([f"{topic['topic']} ({topic['percentage']:.1f}%)" for topic in main_topics])
                    result_lines.append(f"\n💬 Основные темы: {topics_text}")
            
            # Контакты
            contacts = analysis.get('contacts', [])
            if contacts:
                contact_types = {}
                for contact in contacts:
                    contact_type = contact['type']
                    contact_types[contact_type] = contact_types.get(contact_type, 0) + 1
                
                contact_summary = ', '.join([f"{count} {type}" for type, count in contact_types.items()])
                result_lines.append(f"\n📞 Контакты: {contact_summary}")
            
            return '\n'.join(result_lines)
        
        except Exception as e:
            return f"Ошибка форматирования анализа: {e}"
    
    def get_help_text(self) -> str:
        """Возвращает справку по командам Telegram"""
        
        help_text = """
📱 Команды для работы с Telegram:

🚀 Основные команды:
• "Открой Telegram" - запустить мессенджер
• "Открой чат Иван" - найти и открыть чат
• "Прочитай чат" - анализ текущего чата

💬 Работа с сообщениями:
• "Напиши в чат привет" - отправить сообщение
• "Отправь через бота привет" - отправить через Bot API
• "Что в чате" - анализ переписки
• "Настроение в чате" - эмоциональный анализ

🤖 AI-анализ (новое):
• "Анализируй чат с ИИ" - полный AI анализ
• "Резюме чата" - краткое описание переписки
• "Найди сообщения ключевое слово" - поиск в чате
• "Информация о чате" - статистика чата

📊 Извлечение данных:
• "Извлеки данные из чата" - все типы данных
• "Перенеси контакты в таблицу" - только контакты
• "Найди контакты в чате" - поиск участников
• "Управление контактами" - работа с контактами

🔍 Анализ и скриншоты:
• "Анализируй чат" - общий анализ
• "Сделай скриншот Telegram" - снимок экрана
• "Прокрути чат вверх/вниз" - навигация

🎯 Возможности AI:
• Анализ настроения с помощью нейросетей
• Извлечение именованных сущностей
• Классификация сообщений
• Определение тем разговора
• Умный поиск по контексту

📅 Планирование (в разработке):
• "Запланируй сообщение текст" - отложенная отправка
        """.strip()
        
        return help_text
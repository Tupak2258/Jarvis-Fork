"""
Главный файл Jarvis Assistant - Локальный голосовой ассистент
"""

import logging
import sys
import time
import threading
from pathlib import Path
from colorama import init, Fore, Style
from rich.console import Console
from rich.logging import RichHandler

# Локальные модули
from config import (
    LOGS_DIR, LOG_LEVEL, LOG_FORMAT, ASSISTANT_NAME, 
    USER_NAME, WAKE_WORD, OLLAMA_MODEL
)
from modules import (
    OllamaClient, SpeechRecognizer, TextToSpeech, 
    GoogleSheetsClient, SystemTools
)


class JarvisAssistant:
    """Основной класс голосового ассистента"""
    
    def __init__(self):
        self.console = Console()
        self.logger = self._setup_logging()
        
        # Инициализация компонентов
        self.llm_client = OllamaClient()
        self.speech_recognizer = SpeechRecognizer()
        # self.speech_recognizer.set_microphone(26)
        self.tts = TextToSpeech()
        # Используем адаптивный клиент для работы с данными
        try:
            from modules.adaptive_sheets_client import AdaptiveSheetsClient
            self.sheets_client = AdaptiveSheetsClient()
            self.logger.info(f"Инициализирован клиент данных: {self.sheets_client.get_storage_type()}")
        except ImportError:
            from modules.sheets_client import GoogleSheetsClient
            self.sheets_client = GoogleSheetsClient()
            self.logger.warning("Используется стандартный Google Sheets клиент")
        self.system_tools = SystemTools()
        
        # Инициализация мониторинга производительности
        try:
            from modules.performance_monitor import PerformanceMonitor
            self.performance_monitor = PerformanceMonitor()
        except ImportError:
            self.performance_monitor = None
            self.logger.warning("Модуль мониторинга производительности недоступен")
        
        # Инициализация управления приложениями
        try:
            from modules.app_manager import AppManager
            from modules.app_commands import AppCommandProcessor
            self.app_manager = AppManager()
            self.app_commands = AppCommandProcessor(self.app_manager)
        except ImportError as e:
            self.app_manager = None
            self.app_commands = None
            self.logger.warning(f"Модуль управления приложениями недоступен: {e}")
        
        # Инициализация веб-команд
        try:
            from modules.web_commands import WebCommandProcessor
            self.web_commands = WebCommandProcessor()
        except ImportError as e:
            self.web_commands = None
            self.logger.warning(f"Модуль веб-команд недоступен: {e}")
        
        # Инициализация команд Google Sheets
        try:
            from modules.sheets_commands import SheetsCommandProcessor
            self.sheets_commands = SheetsCommandProcessor(self.sheets_client)
        except ImportError as e:
            self.sheets_commands = None
            self.logger.warning(f"Модуль команд Google Sheets недоступен: {e}")
        
        # Инициализация команд Telegram
        try:
            from modules.telegram_commands import TelegramCommandProcessor
            self.telegram_commands = TelegramCommandProcessor(self.sheets_client)
        except ImportError as e:
            self.telegram_commands = None
            self.logger.warning(f"Модуль команд Telegram недоступен: {e}")
        
        # Состояние ассистента
        self.is_running = False
        self.is_listening = False
        self.conversation_active = False
        
        # Загрузка сохраненных данных сессии
        self._load_session_data()
        
        self.logger.info(f"{ASSISTANT_NAME} инициализирован")
    
    def _setup_logging(self) -> logging.Logger:
        """Настройка системы логирования"""
        
        # Создание директории для логов
        LOGS_DIR.mkdir(exist_ok=True)
        
        # Настройка логгера
        logger = logging.getLogger("jarvis")
        logger.setLevel(getattr(logging, LOG_LEVEL))
        
        # Обработчик для файла
        file_handler = logging.FileHandler(
            LOGS_DIR / f"jarvis_{time.strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        
        # Rich обработчик для консоли
        console_handler = RichHandler(rich_tracebacks=True)
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _check_dependencies(self) -> bool:
        """Проверка доступности всех компонентов"""
        
        self.console.print("\n🔍 Проверка компонентов...", style="yellow")
        
        # Проверка Ollama
        if self.llm_client.is_available():
            self.console.print("✅ Ollama API доступен", style="green")
        else:
            self.console.print("❌ Ollama API недоступен", style="red")
            self.console.print("💡 Убедитесь, что Ollama запущен: ollama serve", style="blue")
            return False
        
        # Проверка модели
        available_models = self.llm_client.get_available_models()
        if OLLAMA_MODEL in available_models:
            self.console.print(f"✅ Модель {OLLAMA_MODEL} доступна", style="green")
        else:
            self.console.print(f"❌ Модель {OLLAMA_MODEL} не найдена", style="red")
            self.console.print(f"💡 Доступные модели: {', '.join(available_models)}", style="blue")
            return False
        
        # Проверка микрофона
        if self.speech_recognizer.test_microphone():
            self.console.print("✅ Микрофон работает", style="green")
        else:
            self.console.print("⚠️ Проблемы с микрофоном", style="yellow")
        
        # Проверка TTS
        if self.tts.test_speech("Тест синтеза речи"):
            self.console.print("✅ Синтез речи работает", style="green")
        else:
            self.console.print("⚠️ Проблемы с синтезом речи", style="yellow")
        
        # Проверка Google Sheets
        if self.sheets_client.is_available():
            self.console.print("✅ Google Sheets API настроен", style="green")
        else:
            self.console.print("⚠️ Google Sheets API недоступен", style="yellow")
            self.console.print("💡 Поместите google_credentials.json в папку credentials/", style="blue")
        
        return True
    
    def _display_welcome(self):
        """Отображает приветственное сообщение"""
        
        self.console.print("\n" + "="*60, style="cyan")
        self.console.print(f"🤖 {ASSISTANT_NAME} - Локальный голосовой ассистент", style="bold cyan")
        self.console.print("="*60, style="cyan")
        
        self.console.print(f"\n👋 Привет, {USER_NAME}! Я готов к работе.", style="green")
        self.console.print(f"🔊 Скажите '{WAKE_WORD}' для активации", style="blue")
        self.console.print("⌨️ Или нажмите 'q' + Enter для выхода\n", style="yellow")
        
        # Произнесение приветствия
        self.tts.speak_async(f"Привет, {USER_NAME}! Я {ASSISTANT_NAME} и готов помочь вам.")
    
    def _process_user_input(self, user_input: str) -> str:
        """Обрабатывает пользовательский ввод"""
        
        start_time = time.time()
        
        self.logger.info(f"Пользователь: {user_input}")
        self.console.print(f"\n👤 {USER_NAME}: {user_input}", style="blue")
        
        # Проверяем команды в порядке приоритета (специфичные команды первыми)
        
        # 1. Команды Telegram (высокий приоритет для специфичных команд)
        if self.telegram_commands:
            handled, telegram_response = self.telegram_commands.process_command(user_input)
            if handled:
                self.logger.info(f"Команда Telegram обработана: {telegram_response}")
                self.console.print(f"🤖 {ASSISTANT_NAME}: {telegram_response}", style="green")
                
                # Запись времени отклика
                end_time = time.time()
                if self.performance_monitor:
                    self.performance_monitor.record_response_time(start_time, end_time)
                
                return telegram_response
        
        # 2. Команды Google Sheets и отчетов
        if self.sheets_commands:
            handled, sheets_response = self.sheets_commands.process_command(user_input)
            if handled:
                self.logger.info(f"Команда Google Sheets обработана: {sheets_response}")
                self.console.print(f"🤖 {ASSISTANT_NAME}: {sheets_response}", style="green")
                
                # Запись времени отклика
                end_time = time.time()
                if self.performance_monitor:
                    self.performance_monitor.record_response_time(start_time, end_time)
                
                return sheets_response
        
        # 3. Веб-команды и интернет
        if self.web_commands:
            handled, web_response = self.web_commands.process_command(user_input)
            if handled:
                self.logger.info(f"Веб-команда обработана: {web_response}")
                self.console.print(f"🤖 {ASSISTANT_NAME}: {web_response}", style="green")
                
                # Запись времени отклика
                end_time = time.time()
                if self.performance_monitor:
                    self.performance_monitor.record_response_time(start_time, end_time)
                
                return web_response
        
        # 4. Команды управления приложениями (общие команды)
        if self.app_commands:
            handled, app_response = self.app_commands.process_command(user_input)
            if handled:
                self.logger.info(f"Команда приложения обработана: {app_response}")
                self.console.print(f"🤖 {ASSISTANT_NAME}: {app_response}", style="green")
                
                # Запись времени отклика
                end_time = time.time()
                if self.performance_monitor:
                    self.performance_monitor.record_response_time(start_time, end_time)
                
                return app_response
        
        # Генерация ответа от LLM
        ai_response_raw = self.llm_client.generate_response(user_input)
        
        # Парсинг команды и ответа
        command, answer = self.llm_client.parse_command(ai_response_raw)
        
        final_answer = answer
        
        # --- НОВАЯ ЛОГИКА: ВЫПОЛНЯЕМ КОМАНДУ, ТОЛЬКО ЕСЛИ ОНА ЕСТЬ ---
        if command:
            self.console.print(f"🔧 Выполняю команду: {command}", style="yellow")
            success, result = self.system_tools.execute_command(command)
            
            # Добавляем результат к ответу для наглядности
            final_answer += f" ({result})"
            
            # Логирование в Google Sheets (если доступно)
            if self.sheets_client.is_available():
                self.sheets_client.log_command(command, result, None if success else result)
        
        # Логирование всего разговора
        if self.sheets_client.is_available():
            self.sheets_client.log_conversation(user_input, final_answer, command or "none")
        
        self.logger.info(f"Ассистент: {final_answer}")
        self.console.print(f"🤖 {ASSISTANT_NAME}: {final_answer}", style="green")
        
        # Запись времени отклика
        end_time = time.time()
        if self.performance_monitor:
            self.performance_monitor.record_response_time(start_time, end_time)
        
        return final_answer
    
    def _voice_interaction_loop(self):
        """Основной цикл голосового взаимодействия"""
        
        self.is_listening = True
        
        while self.is_running:
            try:
                # Слушаем слово активации
                if self.speech_recognizer.listen_for_wake_word():
                    self.console.print(f"\n🎤 {WAKE_WORD.title()} активирован!", style="bold green")
                    self.tts.speak_async("Слушаю")
                    
                    # Слушаем команду
                    user_input = self.speech_recognizer.listen_for_command(timeout=10)
                    
                    if user_input:
                        # Обработка команды
                        answer = self._process_user_input(user_input)
                        
                        # Произнесение ответа
                        self.tts.speak(answer)
                    else:
                        self.console.print("⚠️ Команда не распознана", style="yellow")
                        self.tts.speak_async("Извините, я вас не понял")
                
                # Небольшая пауза
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Ошибка в голосовом цикле: {e}")
                time.sleep(1)
        
        self.is_listening = False
    
    def _text_interaction_loop(self):
        """Цикл текстового взаимодействия (для отладки)"""
        
        while self.is_running:
            try:
                user_input = input(f"\n{USER_NAME} (текст): ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'выход', 'стоп']:
                    break
                elif user_input.lower() == 'clear':
                    self.llm_client.clear_history()
                    self.console.print("🧹 История очищена", style="yellow")
                    continue
                elif user_input:
                    answer = self._process_user_input(user_input)
                
            except (KeyboardInterrupt, EOFError):
                break
            except Exception as e:
                self.logger.error(f"Ошибка в текстовом цикле: {e}")
    
    def _keyboard_monitor(self):
        """Мониторинг клавиатуры для управления"""
        
        while self.is_running:
            try:
                key = input().strip().lower()
                
                if key == 'q':
                    self.console.print("\n👋 Завершение работы...", style="yellow")
                    self.stop()
                    break
                elif key == 'c':
                    self.llm_client.clear_history()
                    self.console.print("\n🧹 История разговора очищена", style="yellow")
                elif key == 's':
                    self._show_status()
                elif key == 'h':
                    self._show_help()
                elif key == 'p':
                    self._show_performance()
                elif key == 'm':
                    self._toggle_mute()
                elif key == 'r':
                    self._restart_components()
                elif key.startswith('v'):
                    # Команды управления громкостью: v+ v- v50
                    self._handle_volume_command(key)
                elif key == 'a':
                    self._show_available_apps()
                elif key == 'l':
                    self._list_running_apps()
                elif key == 'w':
                    self._show_web_help()
                elif key == 'g':
                    self._show_sheets_help()
                elif key == 't':
                    self._show_current_work_session()
                elif key == 'tg':
                    self._show_telegram_help()
                
            except (KeyboardInterrupt, EOFError):
                self.stop()
                break
    
    def _show_status(self):
        """Показывает статус системы"""
        
        self.console.print("\n📊 Статус системы:", style="bold cyan")
        self.console.print(f"• Режим: {'Голосовой' if self.is_listening else 'Текстовый'}")
        self.console.print(f"• Ollama: {'✅' if self.llm_client.is_available() else '❌'}")
        self.console.print(f"• Google Sheets: {'✅' if self.sheets_client.is_available() else '❌'}")
        self.console.print(f"• Интернет: {'✅' if self.system_tools.is_internet_available() else '❌'}")
        
        # Системная информация
        success, sys_info = self.system_tools._get_system_info()
        if success:
            self.console.print(f"• {sys_info.replace('ОЗУ:', 'Память:')}")
    
    def _show_help(self):
        """Показывает справку по командам"""
        
        self.console.print("\n❓ Доступные команды:", style="bold cyan")
        self.console.print("• 'q' + Enter - Выход из программы")
        self.console.print("• 'c' + Enter - Очистить историю разговора")
        self.console.print("• 's' + Enter - Показать статус системы")
        self.console.print("• 'p' + Enter - Показать производительность")
        self.console.print("• 'm' + Enter - Включить/выключить звук")
        self.console.print("• 'r' + Enter - Перезапустить компоненты")
        self.console.print("• 'v+' + Enter - Увеличить громкость")
        self.console.print("• 'v-' + Enter - Уменьшить громкость")
        self.console.print("• 'v50' + Enter - Установить громкость 50%")
        self.console.print("• 'a' + Enter - Показать доступные приложения")
        self.console.print("• 'l' + Enter - Список запущенных программ")
        self.console.print("• 'w' + Enter - Справка по веб-командам")
        self.console.print("• 'g' + Enter - Справка по Google Sheets")
        self.console.print("• 't' + Enter - Текущая рабочая сессия")
        self.console.print("• 'tg' + Enter - Справка по Telegram")
        self.console.print("• 'h' + Enter - Показать эту справку")
        self.console.print(f"\n🗣️ Голосовые команды:")
        self.console.print(f"• Скажите '{WAKE_WORD}' для активации")
        self.console.print("• Затем произнесите вашу команду или вопрос")
    
    def start(self, voice_mode: bool = True):
        """
        Запускает ассистента
        
        Args:
            voice_mode: Включить ли голосовой режим
        """
        
        # Проверка зависимостей
        if not self._check_dependencies():
            self.console.print("\n❌ Не все компоненты готовы к работе", style="red")
            return False
        
        self.is_running = True
        
        # Отображение приветствия
        self._display_welcome()
        
        try:
            if voice_mode:
                # Запуск голосового режима
                voice_thread = threading.Thread(target=self._voice_interaction_loop, daemon=True)
                voice_thread.start()
                
                # Мониторинг клавиатуры
                self._keyboard_monitor()
                
                voice_thread.join(timeout=1)
            else:
                # Текстовый режим
                self.console.print("📝 Текстовый режим активен", style="blue")
                self._text_interaction_loop()
        
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
        
        return True
    
    def stop(self):
        """Останавливает ассистента с корректной очисткой ресурсов"""
        
        if not self.is_running:
            return
        
        self.logger.info("Завершение работы ассистента")
        self.is_running = False
        
        try:
            # Остановка TTS с таймаутом
            if self.tts:
                self.tts.stop_speaking()
                # Ждем завершения текущего произношения
                timeout = 3
                while self.tts.is_busy() and timeout > 0:
                    time.sleep(0.1)
                    timeout -= 0.1
                self.tts.cleanup()
            
            # Остановка распознавания речи
            if hasattr(self.speech_recognizer, 'cleanup'):
                self.speech_recognizer.cleanup()
            
            # Сохранение состояния перед выходом
            self._save_session_data()
            
            # Прощальное сообщение
            self.console.print(f"\n👋 {ASSISTANT_NAME} завершил работу. До свидания!", style="green")
            
        except Exception as e:
            self.logger.error(f"Ошибка при завершении работы: {e}")
        finally:
            # Небольшая пауза для завершения потоков
            time.sleep(0.5)
    
    def _load_session_data(self):
        """Загружает данные предыдущей сессии"""
        try:
            from pathlib import Path
            import json
            
            session_file = Path("data/session.json")
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # Восстановление настроек TTS
                if 'tts_settings' in session_data:
                    tts_settings = session_data['tts_settings']
                    if 'rate' in tts_settings:
                        self.tts.set_rate(tts_settings['rate'])
                    if 'volume' in tts_settings:
                        self.tts.set_volume(tts_settings['volume'])
                
                self.logger.info("Данные сессии загружены")
        except Exception as e:
            self.logger.warning(f"Не удалось загрузить данные сессии: {e}")
    
    def _save_session_data(self):
        """Сохраняет данные текущей сессии"""
        try:
            from pathlib import Path
            import json
            
            # Создаем директорию если не существует
            Path("data").mkdir(exist_ok=True)
            
            session_data = {
                'last_session': time.strftime('%Y-%m-%d %H:%M:%S'),
                'tts_settings': {
                    'rate': getattr(self.tts.engine, 'getProperty', lambda x: 200)('rate') if self.tts.engine else 200,
                    'volume': getattr(self.tts.engine, 'getProperty', lambda x: 0.8)('volume') if self.tts.engine else 0.8
                }
            }
            
            with open("data/session.json", 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info("Данные сессии сохранены")
        except Exception as e:
            self.logger.warning(f"Не удалось сохранить данные сессии: {e}")
    
    def _show_performance(self):
        """Показывает информацию о производительности"""
        if hasattr(self, 'performance_monitor'):
            report = self.performance_monitor.get_performance_report()
            self.console.print(report, style="cyan")
            
            # Проверка предупреждений
            alerts = self.performance_monitor.check_performance_alerts()
            for alert in alerts:
                self.console.print(alert, style="yellow")
        else:
            self.console.print("⚠️ Мониторинг производительности недоступен", style="yellow")
    
    def _toggle_mute(self):
        """Переключает режим звука"""
        if hasattr(self, '_muted'):
            self._muted = not self._muted
        else:
            self._muted = True
        
        if self._muted:
            self.tts.set_volume(0.0)
            self.console.print("🔇 Звук выключен", style="yellow")
        else:
            self.tts.set_volume(0.8)
            self.console.print("🔊 Звук включен", style="green")
    
    def _restart_components(self):
        """Перезапускает основные компоненты"""
        self.console.print("🔄 Перезапуск компонентов...", style="yellow")
        
        try:
            # Перезапуск TTS
            if self.tts:
                self.tts.cleanup()
                self.tts = TextToSpeech()
            
            # Перезапуск LLM клиента
            if self.llm_client:
                self.llm_client = OllamaClient()
            
            self.console.print("✅ Компоненты перезапущены", style="green")
            
        except Exception as e:
            self.console.print(f"❌ Ошибка перезапуска: {e}", style="red")
            self.logger.error(f"Ошибка перезапуска компонентов: {e}")
    
    def _handle_volume_command(self, command: str):
        """Обрабатывает команды управления громкостью"""
        try:
            if command == 'v+':
                # Увеличить громкость на 10%
                current_volume = getattr(self.tts.engine, 'getProperty', lambda x: 0.8)('volume') if self.tts.engine else 0.8
                new_volume = min(1.0, current_volume + 0.1)
                self.tts.set_volume(new_volume)
                self.console.print(f"🔊 Громкость: {int(new_volume * 100)}%", style="green")
                
            elif command == 'v-':
                # Уменьшить громкость на 10%
                current_volume = getattr(self.tts.engine, 'getProperty', lambda x: 0.8)('volume') if self.tts.engine else 0.8
                new_volume = max(0.0, current_volume - 0.1)
                self.tts.set_volume(new_volume)
                self.console.print(f"🔉 Громкость: {int(new_volume * 100)}%", style="green")
                
            elif command.startswith('v') and len(command) > 1:
                # Установить конкретную громкость
                volume_str = command[1:]
                volume_percent = int(volume_str)
                if 0 <= volume_percent <= 100:
                    new_volume = volume_percent / 100.0
                    self.tts.set_volume(new_volume)
                    self.console.print(f"🔊 Громкость установлена: {volume_percent}%", style="green")
                else:
                    self.console.print("⚠️ Громкость должна быть от 0 до 100", style="yellow")
                    
        except ValueError:
            self.console.print("⚠️ Неверный формат команды громкости", style="yellow")
        except Exception as e:
            self.console.print(f"❌ Ошибка изменения громкости: {e}", style="red")
    
    def _show_available_apps(self):
        """Показывает доступные приложения"""
        if not self.app_manager:
            self.console.print("⚠️ Модуль управления приложениями недоступен", style="yellow")
            return
        
        try:
            available_apps = self.app_manager.get_available_apps()
            
            if not available_apps:
                self.console.print("📱 Доступные приложения не найдены", style="yellow")
                return
            
            self.console.print("\n📱 Доступные приложения:", style="bold cyan")
            
            for app_name, app_info in sorted(available_apps.items()):
                status = "✅" if app_info['found'] else "🔍"
                self.console.print(f"  {status} {app_info['display_name']} ({app_name})")
            
            self.console.print(f"\nВсего найдено: {len(available_apps)} приложений", style="cyan")
            
        except Exception as e:
            self.console.print(f"❌ Ошибка получения списка приложений: {e}", style="red")
    
    def _list_running_apps(self):
        """Показывает запущенные приложения"""
        if not self.app_manager:
            self.console.print("⚠️ Модуль управления приложениями недоступен", style="yellow")
            return
        
        try:
            running_apps = self.app_manager.get_running_apps()
            
            if not running_apps:
                self.console.print("📱 Нет запущенных приложений", style="yellow")
                return
            
            # Группируем по именам
            app_counts = {}
            for app in running_apps:
                name = app['name'].replace('.exe', '')
                if name not in app_counts:
                    app_counts[name] = {'count': 0, 'pids': []}
                app_counts[name]['count'] += 1
                app_counts[name]['pids'].append(app['pid'])
            
            self.console.print("\n🏃 Запущенные приложения:", style="bold cyan")
            
            # Показываем только первые 15 для читаемости
            for i, (name, info) in enumerate(sorted(app_counts.items())):
                if i >= 15:
                    remaining = len(app_counts) - 15
                    self.console.print(f"  ... и еще {remaining} приложений", style="dim")
                    break
                
                if info['count'] > 1:
                    self.console.print(f"  🔹 {name} ({info['count']} процессов)")
                else:
                    self.console.print(f"  🔹 {name}")
            
            self.console.print(f"\nВсего процессов: {len(running_apps)}", style="cyan")
            
        except Exception as e:
            self.console.print(f"❌ Ошибка получения списка процессов: {e}", style="red")
    
    def _show_web_help(self):
        """Показывает справку по веб-командам"""
        if not self.web_commands:
            self.console.print("⚠️ Модуль веб-команд недоступен", style="yellow")
            return
        
        help_text = self.web_commands.get_help_text()
        self.console.print(help_text, style="cyan")
    
    def _show_sheets_help(self):
        """Показывает справку по командам Google Sheets"""
        if not self.sheets_commands:
            self.console.print("⚠️ Модуль Google Sheets недоступен", style="yellow")
            return
        
        help_text = self.sheets_commands.get_help_text()
        self.console.print(help_text, style="cyan")
    
    def _show_current_work_session(self):
        """Показывает информацию о текущей рабочей сессии"""
        if not self.sheets_commands:
            self.console.print("⚠️ Модуль Google Sheets недоступен", style="yellow")
            return
        
        try:
            success, info = self.sheets_commands.reports_manager.get_current_session_info()
            self.console.print(info, style="cyan")
        except Exception as e:
            self.console.print(f"❌ Ошибка получения информации о сессии: {e}", style="red")
    
    def _show_telegram_help(self):
        """Показывает справку по командам Telegram"""
        if not self.telegram_commands:
            self.console.print("⚠️ Модуль команд Telegram недоступен", style="yellow")
            return
        
        help_text = self.telegram_commands.get_help_text()
        self.console.print(help_text, style="cyan")


def main():
    """Главная функция"""
    
    # Инициализация colorama для Windows
    init(autoreset=True)
    
    # Проверка аргументов командной строки
    voice_mode = True
    if len(sys.argv) > 1 and sys.argv[1] == '--text':
        voice_mode = False
    
    try:
        # Создание и запуск ассистента
        assistant = JarvisAssistant()
        assistant.start(voice_mode=voice_mode)
        
    except Exception as e:
        console = Console()
        console.print(f"\n❌ Критическая ошибка: {e}", style="red")
        console.print("📋 Проверьте логи для подробной информации", style="yellow")
        sys.exit(1)


if __name__ == "__main__":
    main()
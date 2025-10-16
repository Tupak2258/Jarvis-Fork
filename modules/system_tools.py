# system_tools.py (обновленная версия)

import os
import sys
import subprocess
import platform
import logging
import psutil
import webbrowser
import time
import pyautogui  # Импортируем новую библиотеку
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from config import ALLOWED_SYSTEM_COMMANDS

class SystemTools:
    """Класс для выполнения системных команд"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.os_type = platform.system().lower()
        self.logger.info(f"Инициализация системных инструментов для {self.os_type}")
    
    def execute_command(self, command_text: str) -> Tuple[bool, str]:
        """Выполняет системную команду на основе текстового описания"""
        command_text = command_text.lower().strip()
        self.logger.info(f"Обработка команды: {command_text}")
        
        try:
            # --- НОВАЯ КОМАНДА: НАПИСАТЬ ТЕКСТ ---
            if command_text.startswith(('написать', 'напечатать')):
                return self._handle_write_command(command_text)

            # Открыть приложение
            if any(word in command_text for word in ['открыть', 'запустить', 'открой', 'запусти']):
                return self._handle_open_command(command_text)
            
            # Закрыть приложение
            elif any(word in command_text for word in ['закрыть', 'закрой', 'завершить']):
                return self._handle_close_command(command_text)
            
            # Создать папку/файл
            elif any(word in command_text for word in ['создать', 'создай', 'новая папка', 'новый файл']):
                return self._handle_create_command(command_text)
            
            # Показать время
            elif any(word in command_text for word in ['время', 'часы', 'который час']):
                return self._get_current_time()
            
            # Показать дату
            elif any(word in command_text for word in ['дата', 'число', 'какая дата']):
                return self._get_current_date()
            
            # Системная информация
            elif any(word in command_text for word in ['система', 'информация', 'характеристики']):
                return self._get_system_info()

            else:
                return False, f"Команда не распознана: {command_text}"
                
        except Exception as e:
            self.logger.error(f"Ошибка выполнения команды: {e}")
            return False, f"Ошибка выполнения: {str(e)}"

    # --- НОВАЯ ФУНКЦИЯ ДЛЯ ПЕЧАТИ ТЕКСТА ---
    def _handle_write_command(self, command_text: str) -> Tuple[bool, str]:
        """Обработка команды для написания текста."""
        try:
            # Извлекаем текст для написания
            if ":" not in command_text:
                return False, "Не могу понять, какой текст нужно написать. Используйте формат 'написать в [приложение]: [текст]'."
            
            parts = command_text.split(":", 1)
            text_to_write = parts[1].strip()

            # Определяем приложение
            if "блокнот" in parts[0]:
                app_name = "notepad"
                # Открываем блокнот
                self._open_application(app_name)
                # Даем окну время появиться
                time.sleep(1.5)
                # Печатаем текст
                pyautogui.write(text_to_write, interval=0.02)
                return True, f"Текст успешно напечатан в '{app_name}'."
            else:
                return False, "Пока я умею печатать только в Блокноте."

        except Exception as e:
            self.logger.error(f"Ошибка при попытке написать текст: {e}")
            return False, f"Не удалось написать текст: {e}"

    
    def _handle_open_command(self, command_text: str) -> Tuple[bool, str]:
        """Обработка команд открытия приложений"""
        # Проверяем на популярные сайты в первую очередь
        if 'youtube' in command_text or 'ютуб' in command_text:
            return self._open_website("https://youtube.com")
        if 'google' in command_text or 'гугл' in command_text:
            return self._open_website("https://google.com")
        if 'telegram' in command_text or 'телеграм' in command_text: 
            return self._open_application(r"D:\spam\Telegram Desktop\Telegram.exe")
        if 'блокнот' in command_text or 'notepad' in command_text:
            return self._open_application('notepad')
        elif 'калькулятор' in command_text or 'calc' in command_text:
            return self._open_application('calc')
        elif 'проводник' in command_text or 'explorer' in command_text:
            return self._open_application('explorer')
        elif 'браузер' in command_text or 'интернет' in command_text:
            return self._open_browser()
        elif 'сайт' in command_text or 'http' in command_text:
            return self._open_website(command_text)
        else:
            app_name = self._extract_app_name(command_text, ['открыть', 'запустить', 'открой', 'запусти'])
            return self._open_application(app_name)
    
    def _handle_close_command(self, command_text: str) -> Tuple[bool, str]:
        """Обработка команд закрытия приложений"""
        app_name = self._extract_app_name(command_text, ['закрыть', 'закрой', 'завершить'])
        # Добавляем .exe для Windows для надежности
        if self.os_type == 'windows' and not app_name.endswith('.exe'):
            app_name += '.exe'
        return self._close_application(app_name)
    
    def _handle_create_command(self, command_text: str) -> Tuple[bool, str]:
        """Обработка команд создания файлов/папок"""
        if 'папку' in command_text or 'папка' in command_text:
            folder_name = self._extract_name_from_command(command_text, 'папка')
            return self._create_folder(folder_name)
        elif 'файл' in command_text:
            file_name = self._extract_name_from_command(command_text, 'файл')
            return self._create_file(file_name)
        else:
            return False, "Не указано, что создавать (папку или файл)"
    
    def _open_application(self, app_name: str) -> Tuple[bool, str]:
        """Открывает приложение по имени"""
        if not app_name or app_name == 'unknown':
            return False, "Не указано название приложения."
        try:
            if self.os_type == 'windows':
                subprocess.Popen([app_name])
            elif self.os_type == 'darwin':  # macOS
                subprocess.Popen(['open', '-a', app_name])
            else:  # Linux
                subprocess.Popen([app_name])
            return True, f"Приложение '{app_name}' запущено."
        except FileNotFoundError:
            return False, f"Приложение или команда '{app_name}' не найдена."
        except Exception as e:
            return False, f"Не удалось открыть '{app_name}': {e}"
    
    def _open_website(self, command_text: str) -> Tuple[bool, str]:
        """Извлекает и открывает веб-сайт"""
        words = command_text.split()
        url = None
        for word in words:
            if word.startswith(('http://', 'https://')):
                url = word
                break
            # Упрощенная проверка на домен
            elif '.' in word and len(word) > 3 and not word.endswith('.'):
                url = f"https://{word}"
                break
        
        if url:
            webbrowser.open(url)
            return True, f"Открываю сайт: {url}"
        else:
            # Если URL не найден, ищем в браузере
            search_query = self._extract_app_name(command_text, ['открыть', 'запустить', 'открой', 'запусти', 'сайт'])
            webbrowser.open(f"https://www.google.com/search?q={search_query}")
            return True, f"Ищу в браузере: '{search_query}'"

    def _close_application(self, app_name: str) -> Tuple[bool, str]:
        """Закрывает приложение по имени процесса"""
        if not app_name or app_name == 'unknown':
            return False, "Не указано название приложения для закрытия."
        
        found = False
        for proc in psutil.process_iter(['pid', 'name']):
            if app_name.lower() in proc.info['name'].lower():
                try:
                    p = psutil.Process(proc.info['pid'])
                    p.terminate() # Мягкое завершение
                    p.wait(timeout=3) # Ждем завершения
                    found = True
                    self.logger.info(f"Процесс {proc.info['name']} (PID: {proc.info['pid']}) завершен.")
                except psutil.NoSuchProcess:
                    continue # Процесс уже мог закрыться
                except psutil.TimeoutExpired:
                    self.logger.warning(f"Процесс {proc.info['name']} не ответил на terminate, убиваю...")
                    p.kill() # Жесткое завершение
                    found = True
        
        if found:
            return True, f"Приложение '{app_name}' закрыто."
        else:
            return False, f"Приложение '{app_name}' не найдено среди запущенных процессов."
    
    def _extract_app_name(self, command_text: str, stop_words: List[str]) -> str:
        """Универсальная функция для извлечения имени из команды."""
        words = command_text.lower().split()
        # Добавляем общие слова, которые могут мешать
        all_stop_words = stop_words + ['приложение', 'программу', 'файл', 'папку', 'в']
        name_words = [word.strip('"\'') for word in words if word not in all_stop_words]
        return ' '.join(name_words) if name_words else 'unknown'

    # --- Остальные функции (создание файлов, время, дата и т.д.) остаются без изменений ---
    # (Я скопирую их для полноты, но они не менялись)
    def _get_current_time(self) -> Tuple[bool, str]:
        current_time = datetime.now().strftime("%H:%M:%S")
        return True, f"Текущее время: {current_time}"
    def _get_current_date(self) -> Tuple[bool, str]:
        current_date = datetime.now().strftime("%d.%m.%Y")
        return True, f"Сегодняшняя дата: {current_date}"
    def _get_system_info(self) -> Tuple[bool, str]:
        info = []
        info.append(f"ОС: {platform.system()} {platform.release()}")
        info.append(f"Процессор: {platform.processor()}")
        memory = psutil.virtual_memory()
        info.append(f"ОЗУ: {memory.total / (1024**3):.2f} ГБ")
        return True, "\n".join(info)
    def _create_folder(self, folder_name: str) -> Tuple[bool, str]:
        try:
            path = Path.home() / "Desktop" / folder_name
            path.mkdir(exist_ok=True)
            return True, f"Папка '{folder_name}' создана на рабочем столе."
        except Exception as e:
            return False, f"Ошибка создания папки: {e}"
    def _create_file(self, file_name: str) -> Tuple[bool, str]:
        try:
            path = Path.home() / "Desktop" / file_name
            path.touch()
            return True, f"Файл '{file_name}' создан на рабочем столе."
        except Exception as e:
            return False, f"Ошибка создания файла: {e}"
    def _extract_name_from_command(self, command_text: str, object_type: str) -> str:
        """Извлекает имя создаваемого объекта из команды"""
        words = command_text.split()
        try:
            index = next(i for i, word in enumerate(words) if object_type in word)
            if index + 1 < len(words):
                return words[index + 1]
        except StopIteration:
            pass
        return f"new_{object_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def is_internet_available(self) -> bool:
        """Проверяет доступность интернета"""
        try:
            import socket
            # Пытаемся подключиться к Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            try:
                # Альтернативная проверка через HTTP запрос
                import urllib.request
                urllib.request.urlopen('http://www.google.com', timeout=3)
                return True
            except:
                return False
        except Exception:
            return False
    
    def _open_browser(self) -> Tuple[bool, str]:
        """Открывает браузер по умолчанию"""
        try:
            webbrowser.open('about:blank')
            return True, "Браузер открыт"
        except Exception as e:
            return False, f"Ошибка открытия браузера: {e}"
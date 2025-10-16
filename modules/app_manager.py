"""
Модуль управления приложениями и автоматизации
"""

import os
import re
import time
import logging
import subprocess
import psutil
import pyautogui
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import winreg


class AppManager:
    """Класс для управления приложениями и автоматизации"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.app_registry = {}
        self.running_apps = {}
        
        # Настройка pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        
        # Инициализация интеллектуального поиска
        try:
            from .smart_app_finder import SmartAppFinder
            self.smart_finder = SmartAppFinder()
        except ImportError as e:
            self.smart_finder = None
            self.logger.warning(f"SmartAppFinder недоступен: {e}")
        
        # Загрузка реестра приложений
        self._build_app_registry()
        
        self.logger.info("AppManager инициализирован")
    
    def _build_app_registry(self):
        """Строит реестр установленных приложений"""
        self.logger.info("Сканирование установленных приложений...")
        
        # Популярные приложения с их возможными именами
        common_apps = {
            'блокнот': ['notepad.exe', 'notepad'],
            'калькулятор': ['calc.exe', 'calculator.exe'],
            'браузер': ['chrome.exe', 'firefox.exe', 'msedge.exe', 'opera.exe'],
            'хром': ['chrome.exe', 'google chrome'],
            'firefox': ['firefox.exe'],
            'edge': ['msedge.exe', 'microsoft edge'],
            'проводник': ['explorer.exe'],
            'командная строка': ['cmd.exe'],
            'powershell': ['powershell.exe'],
            'paint': ['mspaint.exe'],
            'word': ['winword.exe', 'microsoft word'],
            'excel': ['excel.exe', 'microsoft excel'],
            'telegram': ['telegram.exe'],
            'discord': ['discord.exe'],
            'steam': ['steam.exe'],
            'vlc': ['vlc.exe'],
            'spotify': ['spotify.exe'],
            'skype': ['skype.exe'],
            'zoom': ['zoom.exe'],
            'teams': ['teams.exe', 'microsoft teams'],
            'vscode': ['code.exe', 'visual studio code'],
            'photoshop': ['photoshop.exe'],
            'obs': ['obs64.exe', 'obs studio']
        }
        
        # Добавляем в реестр
        for app_name, executables in common_apps.items():
            self.app_registry[app_name] = {
                'executables': executables,
                'found_paths': [],
                'display_name': app_name.title()
            }
        
        # Сканируем системные пути
        self._scan_system_paths()
        
        # Сканируем реестр Windows
        self._scan_windows_registry()
        
        self.logger.info(f"Найдено {len(self.app_registry)} приложений в реестре")
    
    def _scan_system_paths(self):
        """Сканирует системные пути для поиска приложений"""
        system_paths = [
            Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')),
            Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')),
            Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs',
            Path(os.environ.get('APPDATA', '')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs'
        ]
        
        for base_path in system_paths:
            if base_path.exists():
                try:
                    for app_name, app_info in self.app_registry.items():
                        for executable in app_info['executables']:
                            # Поиск исполняемых файлов
                            for exe_file in base_path.rglob(executable):
                                if exe_file.is_file():
                                    app_info['found_paths'].append(str(exe_file))
                except Exception as e:
                    self.logger.warning(f"Ошибка сканирования {base_path}: {e}")
    
    def _scan_windows_registry(self):
        """Сканирует реестр Windows для поиска установленных программ"""
        try:
            registry_paths = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
            ]
            
            for reg_path in registry_paths:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    try:
                                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                        install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                        
                                        # Ищем соответствия в нашем реестре
                                        for app_name in self.app_registry:
                                            if app_name.lower() in display_name.lower():
                                                if install_location and Path(install_location).exists():
                                                    self.app_registry[app_name]['found_paths'].append(install_location)
                                                    self.app_registry[app_name]['display_name'] = display_name
                                    except FileNotFoundError:
                                        continue
                            except Exception:
                                continue
                except Exception as e:
                    self.logger.warning(f"Ошибка чтения реестра {reg_path}: {e}")
        except Exception as e:
            self.logger.error(f"Ошибка сканирования реестра: {e}")
    
    def find_app(self, app_name: str) -> Optional[str]:
        """
        Находит путь к приложению по имени с использованием интеллектуального поиска
        
        Args:
            app_name: Название приложения
            
        Returns:
            Путь к исполняемому файлу или None
        """
        original_app_name = app_name
        app_name = app_name.lower().strip()
        
        self.logger.info(f"Поиск приложения: '{original_app_name}' -> '{app_name}'")
        
        # 1. Используем интеллектуальный поиск если доступен
        if self.smart_finder:
            success, message, executable = self.smart_finder.find_app_intelligently(original_app_name)
            if success and executable:
                self.logger.info(f"Интеллектуальный поиск: {message}")
                
                # Проверяем, можем ли мы найти полный путь
                full_path = self._get_full_path(executable)
                if full_path:
                    return full_path
                else:
                    # Возвращаем имя исполняемого файла
                    return executable
        
        # 2. Специальная обработка для системных приложений Windows
        system_apps = {
            'блокнот': 'notepad.exe',
            'notepad': 'notepad.exe',
            'калькулятор': 'calc.exe',
            'calc': 'calc.exe',
            'calculator': 'calc.exe',
            'проводник': 'explorer.exe',
            'explorer': 'explorer.exe',
            'paint': 'mspaint.exe',
            'cmd': 'cmd.exe',
            'powershell': 'powershell.exe'
        }
        
        # Проверяем системные приложения
        if app_name in system_apps:
            system_exe = system_apps[app_name]
            full_path = self._get_full_path(system_exe)
            return full_path or system_exe
        
        # 3. Прямое совпадение в реестре
        if app_name in self.app_registry:
            app_info = self.app_registry[app_name]
            if app_info['found_paths']:
                return app_info['found_paths'][0]
            
            # Пробуем найти в PATH
            for executable in app_info['executables']:
                full_path = self._get_full_path(executable)
                if full_path:
                    return full_path
        
        # 4. Поиск по частичному совпадению
        for registered_name, app_info in self.app_registry.items():
            if app_name in registered_name or registered_name in app_name:
                if app_info['found_paths']:
                    return app_info['found_paths'][0]
        
        # 5. Поиск в системном PATH
        full_path = self._get_full_path(app_name)
        if full_path:
            return full_path
        
        # 6. Последняя попытка - добавляем .exe если его нет
        if not app_name.endswith('.exe'):
            full_path = self._get_full_path(app_name + '.exe')
            if full_path:
                return full_path
        
        self.logger.warning(f"Приложение '{original_app_name}' не найдено")
        return None
    
    def _get_full_path(self, executable: str) -> Optional[str]:
        """Получает полный путь к исполняемому файлу"""
        try:
            result = subprocess.run(['where', executable], 
                                  capture_output=True, text=True, shell=True, timeout=5)
            if result.returncode == 0:
                paths = result.stdout.strip().split('\n')
                # Выбираем системный путь, а не Git
                for path in paths:
                    if 'system32' in path.lower() or 'windows' in path.lower():
                        return path
                return paths[0]  # Если системный не найден, берем первый
        except Exception as e:
            self.logger.debug(f"Ошибка поиска пути для {executable}: {e}")
        
        return None
    
    def open_app(self, app_name: str) -> Tuple[bool, str]:
        """
        Открывает приложение по имени
        
        Args:
            app_name: Название приложения
            
        Returns:
            Tuple[success, message]
        """
        original_app_name = app_name
        
        try:
            app_path = self.find_app(app_name)
            
            if not app_path:
                # Предлагаем альтернативы если доступен интеллектуальный поиск
                if self.smart_finder:
                    suggestions = self.smart_finder.get_app_suggestions(app_name)
                    if suggestions:
                        suggestion_text = ", ".join(suggestions[:3])
                        return False, f"Приложение '{original_app_name}' не найдено. Возможно, вы имели в виду: {suggestion_text}"
                
                return False, f"Приложение '{original_app_name}' не найдено"
            
            self.logger.info(f"Найден путь к приложению: {app_path}")
            
            # Запускаем приложение
            if os.path.isfile(app_path):
                # Полный путь к файлу
                process = subprocess.Popen([app_path], shell=True)
            elif app_path.endswith('.exe'):
                # Только имя исполняемого файла
                process = subprocess.Popen([app_path], shell=True)
            else:
                # Если это директория, открываем в проводнике
                process = subprocess.Popen(['explorer', app_path], shell=True)
            
            # Сохраняем информацию о запущенном процессе
            self.running_apps[original_app_name.lower()] = {
                'process': process,
                'pid': process.pid,
                'path': app_path,
                'start_time': time.time()
            }
            
            # Добавляем в кэш интеллектуального поиска
            if self.smart_finder and app_path.endswith('.exe'):
                executable_name = os.path.basename(app_path) if os.path.isfile(app_path) else app_path
                self.smart_finder.add_to_cache(original_app_name, executable_name)
            
            success_msg = f"Приложение '{original_app_name}' успешно открыто"
            self.logger.info(f"{success_msg}: {app_path}")
            return True, success_msg
            
        except FileNotFoundError:
            error_msg = f"Исполняемый файл для '{original_app_name}' не найден"
            self.logger.error(error_msg)
            return False, error_msg
        except PermissionError:
            error_msg = f"Недостаточно прав для запуска '{original_app_name}'"
            self.logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Ошибка открытия приложения '{original_app_name}': {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def close_app(self, app_name: str) -> Tuple[bool, str]:
        """
        Закрывает приложение по имени
        
        Args:
            app_name: Название приложения
            
        Returns:
            Tuple[success, message]
        """
        try:
            app_name = app_name.lower().strip()
            closed_count = 0
            
            # Маппинг популярных приложений к их процессам
            app_process_mapping = {
                'блокнот': ['notepad.exe', 'notepad'],
                'notepad': ['notepad.exe'],
                'калькулятор': ['calc.exe', 'calculator.exe', 'calculatorapp.exe'],
                'calc': ['calc.exe', 'calculator.exe'],
                'calculator': ['calc.exe', 'calculator.exe', 'calculatorapp.exe'],
                'браузер': ['chrome.exe', 'firefox.exe', 'msedge.exe', 'opera.exe'],
                'chrome': ['chrome.exe'],
                'firefox': ['firefox.exe'],
                'edge': ['msedge.exe'],
                'telegram': ['telegram.exe'],
                'телеграм': ['telegram.exe'],
                'discord': ['discord.exe'],
                'spotify': ['spotify.exe'],
                'vlc': ['vlc.exe'],
                'paint': ['mspaint.exe'],
                'word': ['winword.exe'],
                'excel': ['excel.exe'],
                'powerpoint': ['powerpnt.exe'],
                'teams': ['teams.exe'],
                'skype': ['skype.exe'],
                'zoom': ['zoom.exe']
            }
            
            # Определяем список процессов для поиска
            target_processes = []
            if app_name in app_process_mapping:
                target_processes = app_process_mapping[app_name]
            else:
                # Если нет точного соответствия, используем исходное имя
                target_processes = [app_name, f"{app_name}.exe"]
            
            self.logger.info(f"Ищем процессы для закрытия '{app_name}': {target_processes}")
            
            # Закрываем отслеживаемые процессы
            if app_name in self.running_apps:
                try:
                    process = self.running_apps[app_name]['process']
                    process.terminate()
                    process.wait(timeout=5)
                    del self.running_apps[app_name]
                    closed_count += 1
                    self.logger.info(f"Закрыт отслеживаемый процесс: {app_name}")
                except Exception as e:
                    self.logger.warning(f"Ошибка закрытия отслеживаемого процесса: {e}")
            
            # Ищем и закрываем все процессы
            processes_to_close = []
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    proc_name = proc.info['name'].lower()
                    proc_exe = proc.info['exe']
                    
                    # Проверяем точные совпадения с целевыми процессами
                    match_found = False
                    for target in target_processes:
                        target = target.lower()
                        if (proc_name == target or 
                            proc_name.startswith(target.replace('.exe', '')) or
                            (proc_exe and target in Path(proc_exe).name.lower())):
                            match_found = True
                            break
                    
                    if match_found:
                        processes_to_close.append(proc)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception as e:
                    self.logger.warning(f"Ошибка при проверке процесса: {e}")
            
            # Закрываем найденные процессы
            for proc in processes_to_close:
                try:
                    proc_name = proc.info['name']
                    proc_pid = proc.info['pid']
                    
                    # Сначала пробуем мягкое завершение
                    proc.terminate()
                    
                    # Ждем завершения
                    try:
                        proc.wait(timeout=3)
                        closed_count += 1
                        self.logger.info(f"Мягко закрыт процесс: {proc_name} (PID: {proc_pid})")
                    except psutil.TimeoutExpired:
                        # Если не закрылся, принудительно завершаем
                        proc.kill()
                        closed_count += 1
                        self.logger.info(f"Принудительно закрыт процесс: {proc_name} (PID: {proc_pid})")
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Процесс уже закрыт или нет доступа
                    continue
                except Exception as e:
                    self.logger.warning(f"Ошибка закрытия процесса: {e}")
            
            if closed_count > 0:
                return True, f"Закрыто {closed_count} процесс(ов) '{app_name}'"
            else:
                # Попробуем найти процессы для отладки
                all_processes = []
                for proc in psutil.process_iter(['name']):
                    try:
                        all_processes.append(proc.info['name'].lower())
                    except:
                        continue
                
                matching_processes = [p for p in all_processes if app_name in p or any(target.replace('.exe', '') in p for target in target_processes)]
                
                if matching_processes:
                    self.logger.info(f"Найдены похожие процессы: {matching_processes}")
                    return False, f"Найдены похожие процессы, но не удалось закрыть: {', '.join(matching_processes[:3])}"
                else:
                    return False, f"Приложение '{app_name}' не найдено среди запущенных процессов"
                
        except Exception as e:
            error_msg = f"Ошибка закрытия приложения '{app_name}': {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def type_text(self, text: str, delay: float = 0.1) -> Tuple[bool, str]:
        """
        Вводит текст в активное окно
        
        Args:
            text: Текст для ввода
            delay: Задержка между символами
            
        Returns:
            Tuple[success, message]
        """
        try:
            # Небольшая пауза для переключения на нужное окно
            time.sleep(1)
            
            # Вводим текст
            pyautogui.typewrite(text, interval=delay)
            
            self.logger.info(f"Введен текст: {text[:50]}...")
            return True, f"Текст успешно введен ({len(text)} символов)"
            
        except Exception as e:
            error_msg = f"Ошибка ввода текста: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def send_keys(self, keys: str) -> Tuple[bool, str]:
        """
        Отправляет комбинацию клавиш
        
        Args:
            keys: Комбинация клавиш (например, 'ctrl+s', 'enter')
            
        Returns:
            Tuple[success, message]
        """
        try:
            time.sleep(0.5)
            
            if '+' in keys:
                # Комбинация клавиш
                key_parts = [k.strip() for k in keys.split('+')]
                pyautogui.hotkey(*key_parts)
            else:
                # Одиночная клавиша
                pyautogui.press(keys)
            
            self.logger.info(f"Отправлена комбинация клавиш: {keys}")
            return True, f"Комбинация клавиш '{keys}' отправлена"
            
        except Exception as e:
            error_msg = f"Ошибка отправки клавиш '{keys}': {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_running_apps(self) -> List[Dict]:
        """Возвращает список запущенных приложений"""
        running = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'create_time']):
                try:
                    proc_info = proc.info
                    if proc_info['exe']:  # Только процессы с исполняемыми файлами
                        running.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'exe': proc_info['exe'],
                            'start_time': proc_info['create_time']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.logger.error(f"Ошибка получения списка процессов: {e}")
        
        return running
    
    def focus_window(self, window_title: str) -> Tuple[bool, str]:
        """
        Переключается на окно по заголовку
        
        Args:
            window_title: Заголовок окна или его часть
            
        Returns:
            Tuple[success, message]
        """
        try:
            import win32gui
            import win32con
            
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title and window_title.lower() in title.lower():
                        windows.append((hwnd, title))
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            if windows:
                hwnd, title = windows[0]
                win32gui.SetForegroundWindow(hwnd)
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                return True, f"Переключено на окно: {title}"
            else:
                return False, f"Окно с заголовком '{window_title}' не найдено"
                
        except ImportError:
            return False, "Модуль win32gui не установлен"
        except Exception as e:
            error_msg = f"Ошибка переключения на окно: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_available_apps(self) -> Dict[str, Dict]:
        """Возвращает список доступных приложений"""
        available = {}
        
        for app_name, app_info in self.app_registry.items():
            if app_info['found_paths'] or any(self.find_app(exe) for exe in app_info['executables']):
                available[app_name] = {
                    'display_name': app_info['display_name'],
                    'executables': app_info['executables'],
                    'found': len(app_info['found_paths']) > 0
                }
        
        return available
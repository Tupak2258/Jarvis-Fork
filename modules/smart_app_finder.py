"""
Модуль интеллектуального поиска приложений с использованием LLM
"""

import re
import logging
import requests
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import psutil


class SmartAppFinder:
    """Класс для интеллектуального поиска приложений"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "qwen2.5vl:7b"):
        self.logger = logging.getLogger(__name__)
        self.ollama_url = ollama_url
        self.model = model
        
        # Кэш для уже найденных соответствий
        self.app_name_cache = {}
        
        # Кэш для реальных путей к приложениям
        self.real_paths_cache = {}
        
        # Расширенная база популярных приложений
        self.known_apps = {
            # Мессенджеры
            'телеграм': ['telegram.exe', 'telegram desktop', r'D:\spam\Telegram Desktop\Telegram.exe'],
            'telegram': ['telegram.exe', r'D:\spam\Telegram Desktop\Telegram.exe'],
            'дискорд': ['discord.exe'],
            'discord': ['discord.exe'],
            'скайп': ['skype.exe'],
            'skype': ['skype.exe'],
            'teams': ['teams.exe', 'microsoft teams'],
            'тимс': ['teams.exe'],
            'whatsapp': ['whatsapp.exe'],
            'ватсап': ['whatsapp.exe'],
            'viber': ['viber.exe'],
            'вайбер': ['viber.exe'],
            
            # Браузеры
            'браузер': ['chrome.exe', 'firefox.exe', 'msedge.exe', 'opera.exe'],
            'хром': ['chrome.exe'],
            'chrome': ['chrome.exe'],
            'firefox': ['firefox.exe'],
            'фаерфокс': ['firefox.exe'],
            'edge': ['msedge.exe'],
            'эдж': ['msedge.exe'],
            'opera': ['opera.exe'],
            'опера': ['opera.exe'],
            
            # Офисные
            'word': ['winword.exe', 'microsoft word'],
            'ворд': ['winword.exe'],
            'excel': ['excel.exe', 'microsoft excel'],
            'эксель': ['excel.exe'],
            'powerpoint': ['powerpnt.exe'],
            'повер поинт': ['powerpnt.exe'],
            'outlook': ['outlook.exe'],
            'аутлук': ['outlook.exe'],
            
            # Системные
            'блокнот': ['notepad.exe'],
            'notepad': ['notepad.exe'],
            'калькулятор': ['calc.exe', 'calculator.exe'],
            'calculator': ['calc.exe'],
            'calc': ['calc.exe'],
            'проводник': ['explorer.exe'],
            'explorer': ['explorer.exe'],
            'paint': ['mspaint.exe'],
            'пейнт': ['mspaint.exe'],
            'cmd': ['cmd.exe'],
            'командная строка': ['cmd.exe'],
            'powershell': ['powershell.exe'],
            'павершелл': ['powershell.exe'],
            
            # Медиа
            'vlc': ['vlc.exe'],
            'влс': ['vlc.exe'],
            'spotify': ['spotify.exe'],
            'спотифай': ['spotify.exe'],
            'itunes': ['itunes.exe'],
            'айтюнс': ['itunes.exe'],
            'windows media player': ['wmplayer.exe'],
            'медиа плеер': ['wmplayer.exe'],
            
            # Разработка
            'visual studio code': ['code.exe'],
            'vscode': ['code.exe'],
            'код': ['code.exe'],
            'visual studio': ['devenv.exe'],
            'notepad++': ['notepad++.exe'],
            'блокнот плюс': ['notepad++.exe'],
            'git bash': ['git-bash.exe'],
            'гит баш': ['git-bash.exe'],
            
            # Игры и развлечения
            'steam': ['steam.exe'],
            'стим': ['steam.exe'],
            'epic games': ['epicgameslauncher.exe'],
            'эпик геймс': ['epicgameslauncher.exe'],
            
            # Графика
            'photoshop': ['photoshop.exe'],
            'фотошоп': ['photoshop.exe'],
            'gimp': ['gimp.exe'],
            'гимп': ['gimp.exe'],
            
            # Архиваторы
            'winrar': ['winrar.exe'],
            'винрар': ['winrar.exe'],
            '7zip': ['7zfm.exe'],
            'семь зип': ['7zfm.exe'],
        }
        
        # Сканируем систему после инициализации базы приложений
        self._scan_system_for_apps()
        
        self.logger.info("SmartAppFinder инициализирован")
    
    def _scan_system_for_apps(self):
        """Сканирует систему для поиска реальных путей к приложениям"""
        try:
            self.logger.info("Сканирование системы для поиска приложений...")
            
            # Сканируем запущенные процессы
            for proc in psutil.process_iter(['name', 'exe']):
                try:
                    proc_name = proc.info['name'].lower()
                    proc_exe = proc.info['exe']
                    
                    if proc_exe and Path(proc_exe).exists():
                        # Сохраняем реальные пути к популярным приложениям
                        for app_key in self.known_apps.keys():
                            if app_key in proc_name or any(exe.lower().replace('.exe', '') in proc_name for exe in self.known_apps[app_key]):
                                self.real_paths_cache[app_key] = proc_exe
                                self.logger.debug(f"Найден реальный путь: {app_key} -> {proc_exe}")
                                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self.logger.info(f"Найдено {len(self.real_paths_cache)} реальных путей к приложениям")
            
        except Exception as e:
            self.logger.error(f"Ошибка сканирования системы: {e}")
    
    def find_app_intelligently(self, user_request: str) -> Tuple[bool, str, Optional[str]]:
        """
        Интеллектуально находит приложение по пользовательскому запросу
        
        Args:
            user_request: Запрос пользователя (например, "открой телеграм")
            
        Returns:
            Tuple[success, message, executable_name]
        """
        try:
            # Очищаем запрос от лишних слов
            app_name = self._extract_app_name_from_request(user_request)
            
            self.logger.info(f"Ищем приложение: '{app_name}' из запроса: '{user_request}'")
            
            # 1. Проверяем кэш
            if app_name in self.app_name_cache:
                cached_result = self.app_name_cache[app_name]
                self.logger.info(f"Найдено в кэше: {app_name} -> {cached_result}")
                return True, f"Найдено в кэше: {cached_result}", cached_result
            
            # 2. Проверяем известные приложения
            known_result = self._check_known_apps(app_name)
            if known_result:
                self.app_name_cache[app_name] = known_result
                return True, f"Найдено среди известных: {known_result}", known_result
            
            # 3. Проверяем запущенные процессы
            running_result = self._check_running_processes(app_name)
            if running_result:
                self.app_name_cache[app_name] = running_result
                return True, f"Найдено среди запущенных: {running_result}", running_result
            
            # 4. Используем LLM для поиска
            llm_result = self._ask_llm_for_app_name(app_name)
            if llm_result:
                # Проверяем, существует ли предложенное приложение
                if self._verify_app_exists(llm_result):
                    self.app_name_cache[app_name] = llm_result
                    return True, f"Найдено через LLM: {llm_result}", llm_result
                else:
                    self.logger.warning(f"LLM предложил несуществующее приложение: {llm_result}")
            
            # 5. Последняя попытка - поиск по частичному совпадению
            partial_result = self._find_by_partial_match(app_name)
            if partial_result:
                self.app_name_cache[app_name] = partial_result
                return True, f"Найдено по частичному совпадению: {partial_result}", partial_result
            
            return False, f"Приложение '{app_name}' не найдено", None
            
        except Exception as e:
            error_msg = f"Ошибка интеллектуального поиска: {e}"
            self.logger.error(error_msg)
            return False, error_msg, None
    
    def _extract_app_name_from_request(self, request: str) -> str:
        """Извлекает название приложения из запроса"""
        request = request.lower().strip()
        
        # Удаляем команды открытия
        stop_words = [
            'открой', 'запусти', 'включи', 'открыть', 'запустить', 'включить',
            'open', 'start', 'launch', 'run'
        ]
        
        words = request.split()
        filtered_words = []
        
        for word in words:
            # Убираем точки в конце
            clean_word = word.rstrip('.,!?')
            if clean_word not in stop_words:
                filtered_words.append(clean_word)
        
        return ' '.join(filtered_words)
    
    def _check_known_apps(self, app_name: str) -> Optional[str]:
        """Проверяет известные приложения"""
        app_name = app_name.lower()
        
        # Сначала проверяем реальные пути
        if app_name in self.real_paths_cache:
            real_path = self.real_paths_cache[app_name]
            if Path(real_path).exists():
                return real_path
        
        # Прямое совпадение
        if app_name in self.known_apps:
            executables = self.known_apps[app_name]
            for exe in executables:
                if self._verify_app_exists(exe):
                    return exe
        
        # Поиск по частичному совпадению в ключах
        for known_name, executables in self.known_apps.items():
            if app_name in known_name or known_name in app_name:
                # Сначала проверяем реальный путь
                if known_name in self.real_paths_cache:
                    real_path = self.real_paths_cache[known_name]
                    if Path(real_path).exists():
                        return real_path
                
                # Затем проверяем стандартные исполняемые файлы
                for exe in executables:
                    if self._verify_app_exists(exe):
                        return exe
        
        return None
    
    def _check_running_processes(self, app_name: str) -> Optional[str]:
        """Проверяет запущенные процессы"""
        try:
            app_name = app_name.lower()
            
            for proc in psutil.process_iter(['name', 'exe']):
                try:
                    proc_name = proc.info['name'].lower()
                    proc_exe = proc.info['exe']
                    
                    # Проверяем имя процесса
                    if app_name in proc_name or proc_name.startswith(app_name):
                        return proc.info['name']
                    
                    # Проверяем путь к исполняемому файлу
                    if proc_exe:
                        exe_name = Path(proc_exe).name.lower()
                        if app_name in exe_name:
                            return proc.info['name']
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.logger.error(f"Ошибка проверки процессов: {e}")
        
        return None
    
    def _ask_llm_for_app_name(self, app_name: str) -> Optional[str]:
        """Спрашивает LLM о правильном названии приложения"""
        try:
            prompt = f"""Пользователь хочет открыть приложение "{app_name}". 

Определи правильное название исполняемого файла (.exe) для этого приложения в Windows.

Примеры:
- "телеграм" -> "telegram.exe"
- "хром" -> "chrome.exe"
- "ворд" -> "winword.exe"
- "блокнот" -> "notepad.exe"
- "калькулятор" -> "calc.exe"

Ответь ТОЛЬКО названием .exe файла, без дополнительных объяснений.
Если не уверен, ответь "unknown".

Приложение: "{app_name}"
Ответ:"""

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get('response', '').strip().lower()
                
                # Очищаем ответ от лишнего текста
                llm_response = self._clean_llm_response(llm_response)
                
                if llm_response and llm_response != 'unknown' and '.exe' in llm_response:
                    self.logger.info(f"LLM предложил: {app_name} -> {llm_response}")
                    return llm_response
                else:
                    self.logger.warning(f"LLM не смог определить приложение: {llm_response}")
            else:
                self.logger.error(f"Ошибка LLM API: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Ошибка запроса к LLM: {e}")
        
        return None
    
    def _clean_llm_response(self, response: str) -> str:
        """Очищает ответ LLM от лишнего текста"""
        response = response.strip().lower()
        
        # Ищем .exe файл в ответе
        exe_match = re.search(r'(\w+\.exe)', response)
        if exe_match:
            return exe_match.group(1)
        
        # Если нет .exe, но есть название программы
        if response and response != 'unknown':
            # Добавляем .exe если его нет
            if not response.endswith('.exe'):
                response += '.exe'
            return response
        
        return response
    
    def _verify_app_exists(self, executable: str) -> bool:
        """Проверяет, существует ли приложение в системе"""
        try:
            import subprocess
            
            # Пробуем найти через where
            result = subprocess.run(
                ['where', executable], 
                capture_output=True, 
                text=True, 
                shell=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return True
            
            # Проверяем среди запущенных процессов
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() == executable.lower():
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки существования {executable}: {e}")
            return False
    
    def _find_by_partial_match(self, app_name: str) -> Optional[str]:
        """Поиск по частичному совпадению среди всех процессов"""
        try:
            app_name = app_name.lower()
            matches = []
            
            for proc in psutil.process_iter(['name', 'exe']):
                try:
                    proc_name = proc.info['name'].lower()
                    
                    # Ищем частичные совпадения
                    if any(part in proc_name for part in app_name.split() if len(part) > 2):
                        matches.append(proc.info['name'])
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Возвращаем первое найденное совпадение
            if matches:
                return matches[0]
                
        except Exception as e:
            self.logger.error(f"Ошибка поиска по частичному совпадению: {e}")
        
        return None
    
    def get_app_suggestions(self, partial_name: str) -> List[str]:
        """Возвращает список предложений приложений"""
        suggestions = []
        partial_name = partial_name.lower()
        
        # Ищем в известных приложениях
        for app_name, executables in self.known_apps.items():
            if partial_name in app_name:
                suggestions.extend(executables)
        
        # Ищем среди запущенных процессов
        try:
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info['name'].lower()
                    if partial_name in proc_name:
                        suggestions.append(proc.info['name'])
                except:
                    continue
        except:
            pass
        
        return list(set(suggestions))[:5]  # Возвращаем первые 5 уникальных
    
    def add_to_cache(self, user_name: str, executable: str):
        """Добавляет соответствие в кэш"""
        self.app_name_cache[user_name.lower()] = executable
        self.logger.info(f"Добавлено в кэш: {user_name} -> {executable}")
    
    def clear_cache(self):
        """Очищает кэш"""
        self.app_name_cache.clear()
        self.logger.info("Кэш приложений очищен")
"""
Модуль для работы с Telegram Desktop
Использует автоматизацию GUI и скриншоты для анализа
"""

import os
import time
import logging
import pyautogui
import pygetwindow as gw
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import cv2
import numpy as np
from PIL import Image, ImageGrab
import pytesseract
import psutil
import subprocess

# Win32 API для работы со скрытыми окнами
try:
    import win32gui
    import win32con
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


class TelegramManager:
    """Класс для управления Telegram Desktop"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.telegram_window = None
        self.telegram_win32_info = None  # Информация о Win32 окне
        self.screenshots_dir = Path("data/telegram_screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
        
        # Настройки для распознавания текста
        self.tesseract_config = '--oem 3 --psm 6 -l rus+eng'
        
        # Координаты элементов интерфейса (будут калиброваться)
        self.ui_elements = {
            'search_box': None,
            'chat_list': None,
            'message_area': None,
            'input_field': None
        }
        
        # Проверяем доступность Win32 API
        if WIN32_AVAILABLE:
            self.logger.info("TelegramManager инициализирован с поддержкой Win32 API")
        else:
            self.logger.info("TelegramManager инициализирован без Win32 API")
            self.logger.warning("Для работы со скрытыми окнами установите: pip install pywin32")
    
    def find_telegram_window(self) -> bool:
        """Находит окно Telegram Desktop"""
        try:
            # Метод 1: Умный поиск по характеристикам окна
            telegram_windows = []
            all_windows = gw.getAllWindows()
            
            for window in all_windows:
                window_title = window.title.lower()
                
                # Проверяем размер окна (Telegram обычно большое)
                if window.width < 400 or window.height < 300:
                    continue
                
                is_telegram = False
                
                # Вариант 1: Прямые индикаторы Telegram
                telegram_indicators = [
                    'telegram',
                    'телеграм', 
                    'telegram desktop',
                    'telegram.exe'
                ]
                
                for indicator in telegram_indicators:
                    if (indicator in window_title or 
                        window_title.startswith(indicator) or
                        window_title.endswith(indicator)):
                        is_telegram = True
                        break
                
                # Вариант 2: Окно с русскими именами/чатами (характерно для Telegram)
                if not is_telegram and window_title:
                    # Проверяем наличие символа @ (характерно для Telegram чатов)
                    if '@' in window_title:
                        is_telegram = True
                    
                    # Проверяем наличие русских символов в больших окнах
                    elif any(char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя' for char in window_title):
                        # Дополнительная проверка размера для русских названий
                        if window.width > 800 and window.height > 600:
                            is_telegram = True
                
                if is_telegram:
                    telegram_windows.append(window)
                    self.logger.debug(f"Найден кандидат Telegram: '{window.title}' ({window.width}x{window.height})")
            
            if telegram_windows:
                # Выбираем лучшее окно (самое большое среди подходящих)
                self.telegram_window = max(telegram_windows, key=lambda w: w.width * w.height)
                self.logger.info(f"Найдено окно Telegram: '{self.telegram_window.title}' ({self.telegram_window.width}x{self.telegram_window.height})")
                return True
            
            # Метод 2: Поиск через Win32 API (включая скрытые окна)
            if WIN32_AVAILABLE:
                self.logger.info("Ищем окна Telegram через Win32 API...")
                win32_windows = self._find_telegram_windows_win32()
                
                if win32_windows:
                    # Выбираем лучшее окно
                    best_window = self._select_best_telegram_window(win32_windows)
                    if best_window:
                        # Создаем объект-заглушку для совместимости
                        self.telegram_window = self._create_window_wrapper(best_window)
                        self.telegram_win32_info = best_window
                        self.logger.info(f"Найдено окно Telegram через Win32: '{best_window['title']}'")
                        return True
            
            self.logger.warning("Окно Telegram не найдено")
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска окна Telegram: {e}")
            return False
    
    def _find_telegram_windows_win32(self) -> List[Dict]:
        """Находит окна Telegram через Win32 API"""
        if not WIN32_AVAILABLE:
            return []
        
        telegram_windows = []
        
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindow(hwnd):
                try:
                    window_text = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    
                    # Проверяем различные варианты
                    if (window_text and 'telegram' in window_text.lower()) or \
                       (class_name and 'telegram' in class_name.lower()) or \
                       class_name.startswith('Qt') and 'telegram' in class_name.lower():
                        
                        rect = win32gui.GetWindowRect(hwnd)
                        is_visible = win32gui.IsWindowVisible(hwnd)
                        
                        windows.append({
                            'hwnd': hwnd,
                            'title': window_text or 'TelegramDesktop',
                            'class': class_name,
                            'rect': rect,
                            'visible': is_visible,
                            'width': rect[2] - rect[0],
                            'height': rect[3] - rect[1]
                        })
                except Exception:
                    pass
            return True
        
        try:
            win32gui.EnumWindows(enum_windows_callback, telegram_windows)
        except Exception as e:
            self.logger.error(f"Ошибка поиска окон Win32: {e}")
        
        return telegram_windows
    
    def _select_best_telegram_window(self, windows: List[Dict]) -> Optional[Dict]:
        """Выбирает лучшее окно Telegram из списка"""
        if not windows:
            return None
        
        # Приоритет: видимые окна с размером > 100x100
        visible_windows = [w for w in windows if w['visible'] and w['width'] > 100 and w['height'] > 100]
        if visible_windows:
            return max(visible_windows, key=lambda w: w['width'] * w['height'])
        
        # Затем: невидимые окна с размером > 100x100
        large_windows = [w for w in windows if w['width'] > 100 and w['height'] > 100]
        if large_windows:
            return max(large_windows, key=lambda w: w['width'] * w['height'])
        
        # В крайнем случае: любое окно
        return windows[0]
    
    def _create_window_wrapper(self, win32_info: Dict):
        """Создает объект-обертку для Win32 окна"""
        class Win32WindowWrapper:
            def __init__(self, info):
                self.title = info['title']
                self.left = info['rect'][0]
                self.top = info['rect'][1]
                self.right = info['rect'][2]
                self.bottom = info['rect'][3]
                self.width = info['width']
                self.height = info['height']
                self.hwnd = info['hwnd']
                self.visible = info['visible']
                self.isActive = False  # Будем определять динамически
            
            def activate(self):
                """Активирует окно через Win32 API"""
                try:
                    if not self.visible:
                        win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
                        time.sleep(0.5)
                    
                    win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
                    time.sleep(0.5)
                    
                    win32gui.SetForegroundWindow(self.hwnd)
                    time.sleep(0.5)
                    
                    win32gui.SetActiveWindow(self.hwnd)
                    self.isActive = True
                    return True
                except Exception as e:
                    return False
        
        return Win32WindowWrapper(win32_info)
    
    def _try_activate_from_tray(self) -> bool:
        """Пытается активировать Telegram из системного трея"""
        try:
            self.logger.info("Пытаемся активировать Telegram из системного трея")
            
            # Метод 1: Двойной клик по иконке в трее
            try:
                # Ищем иконку Telegram в трее
                import win32gui
                import win32con
                
                def enum_windows_callback(hwnd, windows):
                    if win32gui.IsWindowVisible(hwnd):
                        window_text = win32gui.GetWindowText(hwnd)
                        class_name = win32gui.GetClassName(hwnd)
                        if 'telegram' in window_text.lower() or 'telegram' in class_name.lower():
                            windows.append((hwnd, window_text, class_name))
                    return True
                
                windows = []
                win32gui.EnumWindows(enum_windows_callback, windows)
                
                if windows:
                    # Активируем первое найденное окно
                    hwnd = windows[0][0]
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
                    self.logger.info("Telegram активирован через Win32 API")
                    return True
                    
            except ImportError:
                self.logger.warning("win32gui недоступен, используем альтернативный метод")
            except Exception as e:
                self.logger.warning(f"Не удалось активировать через Win32 API: {e}")
            
            # Метод 2: Горячие клавиши (если настроены)
            try:
                # Некоторые пользователи настраивают Ctrl+Shift+T для Telegram
                pyautogui.hotkey('ctrl', 'shift', 't')
                time.sleep(1)
                return True
            except Exception as e:
                self.logger.warning(f"Горячие клавиши не сработали: {e}")
            
            # Метод 3: Клик по области трея
            try:
                # Кликаем в область системного трея
                screen_width, screen_height = pyautogui.size()
                tray_x = screen_width - 50
                tray_y = screen_height - 30
                
                # Правый клик по трею для открытия контекстного меню
                pyautogui.rightClick(tray_x, tray_y)
                time.sleep(0.5)
                
                # Ищем Telegram в меню (приблизительно)
                pyautogui.click(tray_x - 100, tray_y - 50)
                time.sleep(1)
                
                return True
                
            except Exception as e:
                self.logger.warning(f"Клик по трею не сработал: {e}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка активации из трея: {e}")
            return False
    
    def activate_telegram(self) -> bool:
        """Активирует окно Telegram"""
        try:
            if not self.telegram_window:
                if not self.find_telegram_window():
                    return False
            
            # Активируем окно
            if hasattr(self.telegram_window, 'hwnd'):
                # Win32 окно
                success = self.telegram_window.activate()
                if success:
                    self.logger.info("Окно Telegram активировано через Win32 API")
                    return True
            else:
                # Обычное окно через pygetwindow
                try:
                    # Простая активация
                    self.telegram_window.activate()
                    time.sleep(0.5)
                    
                    # Дополнительно выводим на передний план
                    self.telegram_window.restore()  # На случай если свернуто
                    time.sleep(0.5)
                    
                    self.logger.info("Окно Telegram активировано")
                    return True
                    
                except Exception as e:
                    self.logger.warning(f"Стандартная активация не сработала: {e}")
                    
                    # Альтернативный способ - через клик
                    try:
                        center_x = self.telegram_window.left + self.telegram_window.width // 2
                        center_y = self.telegram_window.top + self.telegram_window.height // 2
                        
                        # Отключаем fail-safe временно
                        original_failsafe = pyautogui.FAILSAFE
                        pyautogui.FAILSAFE = False
                        
                        pyautogui.click(center_x, center_y)
                        time.sleep(0.5)
                        
                        # Восстанавливаем fail-safe
                        pyautogui.FAILSAFE = original_failsafe
                        
                        self.logger.info("Окно Telegram активировано через клик")
                        return True
                        
                    except Exception as e2:
                        self.logger.error(f"Активация через клик не сработала: {e2}")
                        # Восстанавливаем fail-safe в случае ошибки
                        pyautogui.FAILSAFE = original_failsafe
                        return False
            
            return False
                
        except Exception as e:
            self.logger.error(f"Ошибка активации Telegram: {e}")
            return False
    
    def take_screenshot(self, region: Optional[Tuple[int, int, int, int]] = None) -> Optional[str]:
        """
        Делает скриншот Telegram или его части
        
        Args:
            region: Область для скриншота (x, y, width, height)
            
        Returns:
            Путь к файлу скриншота
        """
        try:
            timestamp = int(time.time())
            screenshot_path = self.screenshots_dir / f"telegram_{timestamp}.png"
            
            if region:
                # Скриншот определенной области
                screenshot = ImageGrab.grab(bbox=region)
            elif self.telegram_window:
                # Скриншот окна Telegram
                left, top, right, bottom = (
                    self.telegram_window.left,
                    self.telegram_window.top,
                    self.telegram_window.right,
                    self.telegram_window.bottom
                )
                screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
            else:
                # Скриншот всего экрана
                screenshot = ImageGrab.grab()
            
            screenshot.save(screenshot_path)
            self.logger.info(f"Скриншот сохранен: {screenshot_path}")
            return str(screenshot_path)
            
        except Exception as e:
            self.logger.error(f"Ошибка создания скриншота: {e}")
            return None
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Извлекает текст из изображения с помощью OCR"""
        try:
            # Загружаем изображение
            image = cv2.imread(image_path)
            
            # Предобработка изображения для лучшего распознавания
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Увеличиваем контрастность
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            # Распознаем текст
            text = pytesseract.image_to_string(enhanced, config=self.tesseract_config)
            
            # Очищаем текст
            cleaned_text = self._clean_extracted_text(text)
            
            self.logger.info(f"Извлечен текст из {image_path}: {len(cleaned_text)} символов")
            return cleaned_text
            
        except Exception as e:
            self.logger.error(f"Ошибка извлечения текста из изображения: {e}")
            return ""
    
    def _clean_extracted_text(self, text: str) -> str:
        """Очищает извлеченный текст от артефактов OCR"""
        if not text:
            return ""
        
        # Удаляем лишние пробелы и переносы
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Фильтруем очень короткие строки (вероятно, артефакты)
        filtered_lines = [line for line in lines if len(line) > 2]
        
        return '\n'.join(filtered_lines)
    
    def search_chat(self, chat_name: str) -> bool:
        """
        Ищет чат по имени
        
        Args:
            chat_name: Имя чата для поиска
            
        Returns:
            True если чат найден и открыт
        """
        try:
            if not self.activate_telegram():
                return False
            
            # Нажимаем Ctrl+F для открытия поиска
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(0.5)
            
            # Вводим имя чата
            pyautogui.typewrite(chat_name, interval=0.05)
            time.sleep(1)
            
            # Нажимаем Enter для перехода к чату
            pyautogui.press('enter')
            time.sleep(1)
            
            self.logger.info(f"Выполнен поиск чата: {chat_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка поиска чата '{chat_name}': {e}")
            return False
    
    def open_chat(self, chat_name: str) -> bool:
        """
        Открывает чат по имени
        
        Args:
            chat_name: Имя чата
            
        Returns:
            True если чат открыт успешно
        """
        try:
            if self.search_chat(chat_name):
                # Делаем скриншот для подтверждения
                screenshot_path = self.take_screenshot()
                if screenshot_path:
                    self.logger.info(f"Чат '{chat_name}' открыт, скриншот: {screenshot_path}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка открытия чата '{chat_name}': {e}")
            return False
    
    def send_message(self, message: str) -> bool:
        """
        Отправляет сообщение в активный чат
        
        Args:
            message: Текст сообщения
            
        Returns:
            True если сообщение отправлено
        """
        try:
            # Отключаем fail-safe временно для отправки сообщения
            original_failsafe = pyautogui.FAILSAFE
            pyautogui.FAILSAFE = False
            
            if not self.activate_telegram():
                self.logger.error("Не удалось активировать Telegram")
                return False
            
            self.logger.info(f"Отправляем сообщение: {message}")
            
            # Метод 1: Умный поиск поля ввода
            try:
                # Получаем размеры окна
                if hasattr(self.telegram_window, 'left'):
                    # Обычное окно
                    window_left = self.telegram_window.left
                    window_top = self.telegram_window.top
                    window_width = self.telegram_window.width
                    window_height = self.telegram_window.height
                else:
                    # Win32 окно
                    window_left = self.telegram_window.left
                    window_top = self.telegram_window.top
                    window_width = self.telegram_window.width
                    window_height = self.telegram_window.height
                
                # Кликаем в область поля ввода (внизу окна)
                input_x = window_left + window_width // 2
                input_y = window_top + window_height - 60  # Поле ввода обычно внизу
                
                self.logger.info(f"Кликаем в поле ввода: ({input_x}, {input_y})")
                pyautogui.click(input_x, input_y)
                time.sleep(0.5)
                
                # Очищаем поле ввода
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.2)
                
                # Вводим сообщение
                pyautogui.typewrite(message, interval=0.02)
                time.sleep(0.5)
                
                # Отправляем сообщение
                pyautogui.press('enter')
                time.sleep(0.3)
                
                self.logger.info(f"Сообщение отправлено: {message[:50]}...")
                return True
                
            except Exception as e1:
                self.logger.warning(f"Основной метод не сработал: {e1}")
                
                # Метод 2: Альтернативный способ через центр окна
                try:
                    center_x = window_left + window_width // 2
                    center_y = window_top + window_height // 2
                    
                    # Кликаем в центр окна
                    pyautogui.click(center_x, center_y)
                    time.sleep(0.3)
                    
                    # Используем Ctrl+End чтобы перейти в конец чата (к полю ввода)
                    pyautogui.hotkey('ctrl', 'end')
                    time.sleep(0.3)
                    
                    # Вводим сообщение
                    pyautogui.typewrite(message, interval=0.02)
                    time.sleep(0.5)
                    
                    # Отправляем
                    pyautogui.press('enter')
                    
                    self.logger.info(f"Сообщение отправлено альтернативным методом: {message[:50]}...")
                    return True
                    
                except Exception as e2:
                    self.logger.error(f"Альтернативный метод тоже не сработал: {e2}")
                    return False
            
        except Exception as e:
            self.logger.error(f"Критическая ошибка отправки сообщения: {e}")
            return False
        finally:
            # Восстанавливаем fail-safe
            pyautogui.FAILSAFE = original_failsafe
    
    def read_chat_messages(self, count: int = 10) -> List[Dict[str, str]]:
        """
        Читает последние сообщения из активного чата
        
        Args:
            count: Количество сообщений для чтения
            
        Returns:
            Список сообщений с метаданными
        """
        try:
            if not self.activate_telegram():
                return []
            
            # Делаем скриншот области чата
            screenshot_path = self.take_screenshot()
            if not screenshot_path:
                return []
            
            # Извлекаем текст из скриншота
            extracted_text = self.extract_text_from_image(screenshot_path)
            
            # Парсим сообщения (упрощенная версия)
            messages = self._parse_messages_from_text(extracted_text)
            
            self.logger.info(f"Прочитано {len(messages)} сообщений")
            return messages[:count]
            
        except Exception as e:
            self.logger.error(f"Ошибка чтения сообщений: {e}")
            return []
    
    def _parse_messages_from_text(self, text: str) -> List[Dict[str, str]]:
        """Парсит сообщения из извлеченного текста"""
        messages = []
        
        if not text:
            return messages
        
        # Простой парсинг - разделяем по строкам
        lines = text.split('\n')
        
        current_message = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Если строка похожа на время (содержит :)
            if ':' in line and len(line) < 10:
                if current_message:
                    messages.append({
                        'text': current_message.strip(),
                        'timestamp': line,
                        'type': 'message'
                    })
                current_message = ""
            else:
                current_message += " " + line
        
        # Добавляем последнее сообщение
        if current_message:
            messages.append({
                'text': current_message.strip(),
                'timestamp': 'unknown',
                'type': 'message'
            })
        
        return messages
    
    def scroll_chat(self, direction: str = 'up', count: int = 3) -> bool:
        """
        Прокручивает чат вверх или вниз
        
        Args:
            direction: 'up' или 'down'
            count: Количество прокруток
            
        Returns:
            True если прокрутка выполнена
        """
        try:
            if not self.activate_telegram():
                return False
            
            # Кликаем в область чата
            if self.telegram_window:
                center_x = self.telegram_window.left + self.telegram_window.width // 2
                center_y = self.telegram_window.top + self.telegram_window.height // 2
                pyautogui.click(center_x, center_y)
                time.sleep(0.2)
            
            # Прокручиваем
            for _ in range(count):
                if direction == 'up':
                    pyautogui.scroll(3)  # Прокрутка вверх
                else:
                    pyautogui.scroll(-3)  # Прокрутка вниз
                time.sleep(0.3)
            
            self.logger.info(f"Выполнена прокрутка {direction} ({count} раз)")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка прокрутки: {e}")
            return False
    
    def get_chat_info(self) -> Dict[str, str]:
        """Получает информацию о текущем чате"""
        try:
            screenshot_path = self.take_screenshot()
            if not screenshot_path:
                return {}
            
            # Анализируем скриншот для получения информации о чате
            extracted_text = self.extract_text_from_image(screenshot_path)
            
            # Простой анализ заголовка чата (обычно в верхней части)
            lines = extracted_text.split('\n')[:5]  # Берем первые 5 строк
            
            chat_info = {
                'screenshot': screenshot_path,
                'extracted_text_preview': extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text,
                'header_lines': lines
            }
            
            return chat_info
            
        except Exception as e:
            self.logger.error(f"Ошибка получения информации о чате: {e}")
            return {}
    
    def close_telegram(self) -> bool:
        """Закрывает Telegram"""
        try:
            if self.telegram_window:
                self.telegram_window.close()
                self.logger.info("Telegram закрыт")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Ошибка закрытия Telegram: {e}")
            return False
    
    def is_telegram_running(self) -> bool:
        """Проверяет, запущен ли Telegram через процессы и окна"""
        try:
            # Метод 1: Проверяем процессы
            telegram_processes = self._find_telegram_processes()
            if telegram_processes:
                self.logger.info(f"Найдены процессы Telegram: {telegram_processes}")
                
                # Метод 2: Проверяем окна
                if self.find_telegram_window():
                    self.logger.info("Telegram запущен и окно найдено")
                    return True
                else:
                    self.logger.warning("Процесс Telegram найден, но окно не найдено")
                    # Пытаемся открыть окно
                    return self._try_activate_telegram_from_process()
            
            self.logger.warning("Telegram не запущен")
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки Telegram: {e}")
            return False
    
    def _find_telegram_processes(self) -> List[Dict[str, str]]:
        """Находит все процессы Telegram"""
        telegram_processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe']):
                try:
                    proc_name = proc.info['name'].lower()
                    proc_exe = proc.info['exe']
                    
                    # Ищем процессы Telegram
                    if ('telegram' in proc_name or 
                        (proc_exe and 'telegram' in proc_exe.lower())):
                        
                        telegram_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'exe': proc_exe or 'unknown'
                        })
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            self.logger.error(f"Ошибка поиска процессов Telegram: {e}")
        
        return telegram_processes
    
    def _try_activate_telegram_from_process(self) -> bool:
        """Пытается активировать Telegram из процесса"""
        try:
            # Пытаемся найти окно еще раз через некоторое время
            for attempt in range(3):
                time.sleep(1)
                if self.find_telegram_window():
                    self.logger.info(f"Окно Telegram найдено на попытке {attempt + 1}")
                    return True
            
            # Если окно не найдено, пытаемся запустить новый экземпляр
            self.logger.info("Пытаемся запустить новый экземпляр Telegram")
            return self._launch_telegram()
            
        except Exception as e:
            self.logger.error(f"Ошибка активации Telegram из процесса: {e}")
            return False
    
    def _launch_telegram(self) -> bool:
        """Запускает или активирует Telegram Desktop"""
        try:
            # Сначала проверяем, есть ли уже запущенный процесс
            telegram_processes = self._find_telegram_processes()
            
            if telegram_processes:
                self.logger.info("Telegram уже запущен, пытаемся активировать окно")
                
                # Пытаемся активировать существующий процесс
                for proc_info in telegram_processes:
                    try:
                        # Отправляем сигнал процессу для показа окна
                        proc = psutil.Process(proc_info['pid'])
                        
                        # Пытаемся "разбудить" процесс
                        if proc_info['exe'] and os.path.exists(proc_info['exe']):
                            # Запускаем еще один экземпляр - Telegram покажет существующий
                            subprocess.Popen([proc_info['exe']], 
                                           creationflags=subprocess.CREATE_NO_WINDOW)
                            time.sleep(2)
                            
                            if self.find_telegram_window():
                                self.logger.info("Telegram активирован через повторный запуск")
                                return True
                    except Exception as e:
                        self.logger.warning(f"Не удалось активировать процесс {proc_info['pid']}: {e}")
                        continue
            
            # Если процесса нет, запускаем новый
            self.logger.info("Запускаем новый экземпляр Telegram")
            
            # Стандартные пути к Telegram
            possible_paths = [
                r"D:\spam\Telegram Desktop\Telegram.exe",  # Из диагностики
                r"C:\Users\{}\AppData\Roaming\Telegram Desktop\Telegram.exe".format(os.getenv('USERNAME')),
                r"C:\Program Files\Telegram Desktop\Telegram.exe",
                r"C:\Program Files (x86)\Telegram Desktop\Telegram.exe"
            ]
            
            # Ищем существующий путь
            for path in possible_paths:
                if os.path.exists(path):
                    self.logger.info(f"Запускаем Telegram: {path}")
                    subprocess.Popen([path])
                    
                    # Ждем запуска
                    for attempt in range(15):  # Увеличиваем время ожидания
                        time.sleep(1)
                        if self.find_telegram_window():
                            self.logger.info(f"Telegram успешно запущен (попытка {attempt + 1})")
                            return True
                    break
            
            # Пытаемся запустить через команду
            try:
                self.logger.info("Пытаемся запустить через команду 'telegram'")
                subprocess.Popen(['telegram'])
                time.sleep(3)
                if self.find_telegram_window():
                    return True
            except Exception as e:
                self.logger.warning(f"Команда 'telegram' не сработала: {e}")
            
            self.logger.error("Не удалось запустить или активировать Telegram")
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска Telegram: {e}")
            return False
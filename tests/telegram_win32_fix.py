"""
Исправление работы с Telegram через Win32 API
"""

import time
import subprocess
import psutil
import pyautogui

try:
    import win32gui
    import win32con
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("⚠️ win32gui не установлен. Установите: pip install pywin32")

def find_telegram_windows_win32():
    """Находит окна Telegram через Win32 API"""
    if not WIN32_AVAILABLE:
        return []
    
    telegram_windows = []
    
    def enum_windows_callback(hwnd, windows):
        if win32gui.IsWindow(hwnd):
            window_text = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            
            # Проверяем различные варианты
            if (window_text and 'telegram' in window_text.lower()) or \
               (class_name and 'telegram' in class_name.lower()):
                
                # Получаем информацию об окне
                try:
                    rect = win32gui.GetWindowRect(hwnd)
                    is_visible = win32gui.IsWindowVisible(hwnd)
                    
                    windows.append({
                        'hwnd': hwnd,
                        'title': window_text,
                        'class': class_name,
                        'rect': rect,
                        'visible': is_visible
                    })
                except:
                    pass
        return True
    
    try:
        win32gui.EnumWindows(enum_windows_callback, telegram_windows)
    except Exception as e:
        print(f"Ошибка поиска окон: {e}")
    
    return telegram_windows

def activate_telegram_win32(window_info):
    """Активирует окно Telegram через Win32 API"""
    if not WIN32_AVAILABLE:
        return False
    
    try:
        hwnd = window_info['hwnd']
        
        # Показываем окно если оно скрыто
        if not window_info['visible']:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            time.sleep(0.5)
        
        # Восстанавливаем окно если оно свернуто
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        time.sleep(0.5)
        
        # Выводим на передний план
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.5)
        
        # Активируем окно
        win32gui.SetActiveWindow(hwnd)
        
        return True
        
    except Exception as e:
        print(f"Ошибка активации окна: {e}")
        return False

def send_message_to_telegram(message):
    """Отправляет сообщение в Telegram"""
    try:
        # Небольшая пауза для активации
        time.sleep(1)
        
        # Кликаем в центр экрана (где должно быть окно Telegram)
        screen_width, screen_height = pyautogui.size()
        center_x, center_y = screen_width // 2, screen_height // 2
        
        pyautogui.click(center_x, center_y)
        time.sleep(0.5)
        
        # Пытаемся найти поле ввода через Tab
        for _ in range(5):
            pyautogui.press('tab')
            time.sleep(0.2)
        
        # Очищаем поле
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        
        # Вводим сообщение
        pyautogui.typewrite(message, interval=0.05)
        time.sleep(1)
        
        # Отправляем
        pyautogui.press('enter')
        
        return True
        
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")
        return False

def test_telegram_win32():
    """Тестирует работу с Telegram через Win32 API"""
    print("🔧 ТЕСТИРОВАНИЕ TELEGRAM ЧЕРЕЗ WIN32 API")
    print("=" * 60)
    
    if not WIN32_AVAILABLE:
        print("❌ Win32 API недоступен")
        return False
    
    # Ищем процессы Telegram
    telegram_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if 'telegram' in proc.info['name'].lower():
                telegram_processes.append(proc.info)
        except:
            continue
    
    if not telegram_processes:
        print("❌ Процесс Telegram не найден")
        return False
    
    print(f"✅ Найден процесс: {telegram_processes[0]['name']}")
    
    # Ищем окна через Win32 API
    telegram_windows = find_telegram_windows_win32()
    
    if not telegram_windows:
        print("❌ Окна Telegram не найдены через Win32 API")
        return False
    
    print(f"✅ Найдено окон: {len(telegram_windows)}")
    
    for i, window in enumerate(telegram_windows):
        print(f"  {i+1}. '{window['title']}'")
        print(f"     Класс: {window['class']}")
        print(f"     Видимо: {window['visible']}")
        print(f"     Размер: {window['rect']}")
    
    # Выбираем лучшее окно
    best_window = None
    for window in telegram_windows:
        if window['title'] and len(window['title']) > 1:
            best_window = window
            break
    
    if not best_window:
        best_window = telegram_windows[0]
    
    print(f"\\n🎯 Используем окно: '{best_window['title']}'")
    
    # Активируем окно
    if activate_telegram_win32(best_window):
        print("✅ Окно активировано через Win32 API")
        
        # Тестируем отправку сообщения
        print("\\n📤 Тестируем отправку сообщения...")
        test_message = "Тест Win32 API - Telegram работает! 🤖"
        
        if send_message_to_telegram(test_message):
            print("✅ Сообщение отправлено!")
            return True
        else:
            print("❌ Не удалось отправить сообщение")
    else:
        print("❌ Не удалось активировать окно")
    
    return False

def install_pywin32():
    """Устанавливает pywin32"""
    print("📦 Установка pywin32...")
    try:
        subprocess.check_call(['pip', 'install', 'pywin32'])
        print("✅ pywin32 установлен успешно!")
        print("🔄 Перезапустите скрипт для использования Win32 API")
        return True
    except Exception as e:
        print(f"❌ Ошибка установки pywin32: {e}")
        return False

def main():
    """Главная функция"""
    if not WIN32_AVAILABLE:
        print("❌ Win32 API недоступен")
        print("\\nХотите установить pywin32? (y/n): ", end="")
        try:
            response = input().lower().strip()
            if response in ['y', 'yes', 'да', 'д']:
                return install_pywin32()
        except KeyboardInterrupt:
            print("\\n👋 Отменено")
        return False
    
    return test_telegram_win32()

if __name__ == "__main__":
    try:
        if main():
            print("\\n🎉 УСПЕХ! Win32 API решение работает!")
        else:
            print("\\n❌ Win32 API решение не сработало")
    except KeyboardInterrupt:
        print("\\n👋 Прервано пользователем")
    except Exception as e:
        print(f"\\n❌ Критическая ошибка: {e}")
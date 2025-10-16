"""
Скрипт для активации Telegram из системного трея
"""

import time
import subprocess
import psutil
import pyautogui
from modules.telegram_manager import TelegramManager

def activate_telegram_from_tray():
    """Активирует Telegram из системного трея"""
    print("🔄 Активация Telegram из системного трея...")
    
    # Метод 1: Запуск нового экземпляра (Telegram покажет существующий)
    try:
        telegram_path = r"D:\spam\Telegram Desktop\Telegram.exe"
        print(f"Запускаем: {telegram_path}")
        
        subprocess.Popen([telegram_path], creationflags=subprocess.CREATE_NO_WINDOW)
        print("✅ Команда запуска отправлена")
        
        # Ждем появления окна
        telegram_manager = TelegramManager()
        
        for attempt in range(10):
            print(f"Попытка {attempt + 1}/10: Ищем окно...")
            time.sleep(1)
            
            if telegram_manager.find_telegram_window():
                print("✅ Окно Telegram найдено!")
                print(f"Заголовок: {telegram_manager.telegram_window.title}")
                print(f"Размер: {telegram_manager.telegram_window.width}x{telegram_manager.telegram_window.height}")
                return True
        
        print("❌ Окно так и не появилось")
        return False
        
    except Exception as e:
        print(f"❌ Ошибка активации: {e}")
        return False

def test_telegram_interaction():
    """Тестирует взаимодействие с активированным Telegram"""
    print("\\n🧪 Тестирование взаимодействия с Telegram...")
    
    telegram_manager = TelegramManager()
    
    if not telegram_manager.find_telegram_window():
        print("❌ Окно Telegram не найдено")
        return False
    
    # Активируем окно
    if telegram_manager.activate_telegram():
        print("✅ Окно активировано")
        
        # Пробуем отправить тестовое сообщение
        print("📝 Отправляем тестовое сообщение...")
        
        if telegram_manager.send_message("Тест активации Telegram 🤖"):
            print("✅ Сообщение отправлено!")
            return True
        else:
            print("❌ Не удалось отправить сообщение")
            return False
    else:
        print("❌ Не удалось активировать окно")
        return False

def main():
    """Главная функция"""
    print("🚀 АКТИВАЦИЯ TELEGRAM ИЗ ТРЕЯ")
    print("=" * 50)
    
    # Проверяем процессы
    telegram_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if 'telegram' in proc.info['name'].lower():
                telegram_processes.append(proc.info)
        except:
            continue
    
    if not telegram_processes:
        print("❌ Процесс Telegram не найден. Запустите Telegram Desktop.")
        return 1
    
    print(f"✅ Найден процесс Telegram: {telegram_processes[0]['name']} (PID: {telegram_processes[0]['pid']})")
    
    # Активируем из трея
    if activate_telegram_from_tray():
        print("\\n🎉 Telegram успешно активирован!")
        
        # Тестируем взаимодействие
        if test_telegram_interaction():
            print("\\n✅ Все работает! Теперь голосовые команды должны работать.")
        else:
            print("\\n⚠️ Telegram активирован, но взаимодействие не работает")
    else:
        print("\\n❌ Не удалось активировать Telegram")
        print("\\n💡 Попробуйте:")
        print("• Кликнуть по иконке Telegram в системном трее")
        print("• Нажать Win+R и ввести 'telegram'")
        print("• Перезапустить Telegram Desktop")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\\n👋 Прервано пользователем")
        exit(0)
    except Exception as e:
        print(f"\\n❌ Критическая ошибка: {e}")
        exit(1)
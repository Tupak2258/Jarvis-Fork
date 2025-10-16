"""
Отладочный скрипт для диагностики обнаружения Telegram
"""

import sys
import time
import psutil
import pygetwindow as gw
from modules.telegram_manager import TelegramManager
from modules.telegram_commands import TelegramCommandProcessor
from modules.adaptive_sheets_client import AdaptiveSheetsClient

def check_telegram_processes():
    """Проверяет все процессы связанные с Telegram"""
    print("🔍 Поиск процессов Telegram...")
    print("=" * 60)
    
    telegram_processes = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'status']):
            try:
                proc_name = proc.info['name'].lower()
                proc_exe = proc.info['exe']
                
                # Ищем процессы содержащие telegram
                if 'telegram' in proc_name or (proc_exe and 'telegram' in proc_exe.lower()):
                    telegram_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'exe': proc_exe or 'unknown',
                        'status': proc.info['status']
                    })
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    
    except Exception as e:
        print(f"❌ Ошибка поиска процессов: {e}")
        return []
    
    if telegram_processes:
        print(f"✅ Найдено {len(telegram_processes)} процессов Telegram:")
        for i, proc in enumerate(telegram_processes, 1):
            print(f"  {i}. PID: {proc['pid']}")
            print(f"     Имя: {proc['name']}")
            print(f"     Путь: {proc['exe']}")
            print(f"     Статус: {proc['status']}")
            print()
    else:
        print("❌ Процессы Telegram не найдены")
    
    return telegram_processes

def check_telegram_windows():
    """Проверяет окна Telegram"""
    print("🪟 Поиск окон Telegram...")
    print("=" * 60)
    
    telegram_windows = []
    
    try:
        all_windows = gw.getAllWindows()
        print(f"Всего окон найдено: {len(all_windows)}")
        
        for window in all_windows:
            if 'telegram' in window.title.lower():
                telegram_windows.append(window)
                
        if telegram_windows:
            print(f"✅ Найдено {len(telegram_windows)} окон Telegram:")
            for i, window in enumerate(telegram_windows, 1):
                print(f"  {i}. Заголовок: '{window.title}'")
                print(f"     Размер: {window.width}x{window.height}")
                print(f"     Позиция: ({window.left}, {window.top})")
                print(f"     Активно: {window.isActive}")
                print(f"     Видимо: {window.visible}")
                print()
        else:
            print("❌ Окна Telegram не найдены")
            print("\\n🔍 Все найденные окна:")
            for window in all_windows[:10]:  # Показываем первые 10
                print(f"  • '{window.title}'")
            if len(all_windows) > 10:
                print(f"  ... и еще {len(all_windows) - 10} окон")
    
    except Exception as e:
        print(f"❌ Ошибка поиска окон: {e}")
        return []
    
    return telegram_windows

def test_telegram_manager():
    """Тестирует TelegramManager"""
    print("\\n\\n🤖 Тестирование TelegramManager...")
    print("=" * 60)
    
    try:
        telegram_manager = TelegramManager()
        
        # Тест 1: Проверка запуска
        print("1️⃣ Проверка is_telegram_running()...")
        is_running = telegram_manager.is_telegram_running()
        print(f"   Результат: {is_running}")
        
        if is_running:
            # Тест 2: Поиск окна
            print("\\n2️⃣ Проверка find_telegram_window()...")
            window_found = telegram_manager.find_telegram_window()
            print(f"   Результат: {window_found}")
            
            if window_found and telegram_manager.telegram_window:
                window = telegram_manager.telegram_window
                print(f"   Окно: {window.title}")
                print(f"   Размеры: {window.width}x{window.height}")
                print(f"   Позиция: ({window.left}, {window.top})")
                
                # Тест 3: Активация
                print("\\n3️⃣ Проверка activate_telegram()...")
                activated = telegram_manager.activate_telegram()
                print(f"   Результат: {activated}")
                
                if activated:
                    print("\\n✅ TelegramManager работает корректно!")
                    return True
                else:
                    print("\\n⚠️ Не удалось активировать Telegram")
            else:
                print("\\n❌ Окно Telegram не найдено")
        else:
            print("\\n❌ Telegram не запущен согласно TelegramManager")
    
    except Exception as e:
        print(f"\\n❌ Ошибка тестирования TelegramManager: {e}")
    
    return False

def test_command_processing():
    """Тестирует обработку команд"""
    print("\\n\\n🗣️ Тестирование обработки команд...")
    print("=" * 60)
    
    try:
        sheets_client = AdaptiveSheetsClient()
        telegram_commands = TelegramCommandProcessor(sheets_client)
        
        test_commands = [
            "напиши в чат привет всем",
            "отправь сообщение тестирую систему",
            "отправь в чат как дела",
            "пошли в чат все работает",
            "сообщение в чат до свидания"
        ]
        
        for i, command in enumerate(test_commands, 1):
            print(f"\\n{i}️⃣ Тестируем: '{command}'")
            handled, response = telegram_commands.process_command(command)
            print(f"   Обработано: {handled}")
            print(f"   Ответ: {response}")
            
            if handled:
                print("   ✅ Команда распознана")
            else:
                print("   ❌ Команда не распознана")
    
    except Exception as e:
        print(f"❌ Ошибка тестирования команд: {e}")

def interactive_diagnosis():
    """Интерактивная диагностика"""
    print("\\n\\n🎮 Интерактивная диагностика")
    print("=" * 60)
    
    while True:
        print("\\nВыберите действие:")
        print("1. Проверить процессы Telegram")
        print("2. Проверить окна Telegram")
        print("3. Тестировать TelegramManager")
        print("4. Тестировать команды")
        print("5. Полная диагностика")
        print("0. Выход")
        
        try:
            choice = input("\\nВаш выбор: ").strip()
            
            if choice == "1":
                check_telegram_processes()
            elif choice == "2":
                check_telegram_windows()
            elif choice == "3":
                test_telegram_manager()
            elif choice == "4":
                test_command_processing()
            elif choice == "5":
                run_full_diagnosis()
            elif choice == "0":
                break
            else:
                print("❌ Неверный выбор")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    print("\\n👋 Диагностика завершена!")

def run_full_diagnosis():
    """Запускает полную диагностику"""
    print("🔬 ПОЛНАЯ ДИАГНОСТИКА TELEGRAM")
    print("=" * 80)
    
    # Шаг 1: Процессы
    processes = check_telegram_processes()
    
    # Шаг 2: Окна
    windows = check_telegram_windows()
    
    # Шаг 3: TelegramManager
    manager_works = test_telegram_manager()
    
    # Шаг 4: Команды
    test_command_processing()
    
    # Итоговый отчет
    print("\\n\\n📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 80)
    
    print(f"🔧 Процессы Telegram: {'✅ Найдены' if processes else '❌ Не найдены'} ({len(processes)})")
    print(f"🪟 Окна Telegram: {'✅ Найдены' if windows else '❌ Не найдены'} ({len(windows)})")
    print(f"🤖 TelegramManager: {'✅ Работает' if manager_works else '❌ Не работает'}")
    
    # Рекомендации
    print("\\n💡 РЕКОМЕНДАЦИИ:")
    
    if not processes:
        print("• Запустите Telegram Desktop")
        print("• Убедитесь что используете Desktop версию, а не веб")
    
    if processes and not windows:
        print("• Telegram запущен, но окно не найдено")
        print("• Попробуйте развернуть Telegram из системного трея")
        print("• Проверьте что Telegram не свернут")
    
    if windows and not manager_works:
        print("• Окно найдено, но TelegramManager не может с ним работать")
        print("• Возможно проблема с правами доступа")
        print("• Попробуйте перезапустить Telegram")
    
    if manager_works:
        print("• ✅ Все компоненты работают корректно!")
        print("• Можно использовать голосовые команды для Telegram")

def main():
    """Главная функция"""
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "processes":
            check_telegram_processes()
        elif mode == "windows":
            check_telegram_windows()
        elif mode == "manager":
            test_telegram_manager()
        elif mode == "commands":
            test_command_processing()
        elif mode == "interactive":
            interactive_diagnosis()
        elif mode == "full":
            run_full_diagnosis()
        else:
            print(f"❌ Неизвестный режим: {mode}")
            print("Доступные режимы: processes, windows, manager, commands, interactive, full")
            return 1
    else:
        # По умолчанию запускаем полную диагностику
        run_full_diagnosis()
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\\n\\n👋 Диагностика прервана пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\\n❌ Критическая ошибка: {e}")
        sys.exit(1)
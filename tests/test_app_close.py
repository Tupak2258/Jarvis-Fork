"""
Тестовый скрипт для проверки закрытия приложений
"""

import sys
import time
from modules.app_manager import AppManager
from modules.app_commands import AppCommandProcessor

def test_app_operations():
    """Тестирует операции с приложениями"""
    print("🧪 Тестирование операций с приложениями")
    print("=" * 50)
    
    # Создаем менеджер приложений
    app_manager = AppManager()
    app_commands = AppCommandProcessor(app_manager)
    
    # Тест 1: Открытие блокнота
    print("\n1️⃣ Тест открытия блокнота...")
    success, message = app_manager.open_app("блокнот")
    print(f"Результат: {message}")
    
    if success:
        print("⏳ Ждем 3 секунды...")
        time.sleep(3)
        
        # Тест 2: Закрытие блокнота
        print("\n2️⃣ Тест закрытия блокнота...")
        success, message = app_manager.close_app("блокнот")
        print(f"Результат: {message}")
    
    # Тест 3: Проверка голосовых команд
    print("\n3️⃣ Тест голосовых команд...")
    
    test_commands = [
        "открой блокнот",
        "закрой блокнот",
        "запусти калькулятор",
        "завершить калькулятор"
    ]
    
    for command in test_commands:
        print(f"\nТестируем команду: '{command}'")
        handled, response = app_commands.process_command(command)
        if handled:
            print(f"✅ Обработано: {response}")
            time.sleep(2)  # Пауза между командами
        else:
            print(f"❌ Не обработано: {response}")

def list_running_processes():
    """Показывает запущенные процессы"""
    print("\n📋 Запущенные процессы:")
    print("-" * 30)
    
    app_manager = AppManager()
    running_apps = app_manager.get_running_apps()
    
    # Фильтруем только интересные процессы
    interesting_processes = []
    keywords = ['notepad', 'calc', 'chrome', 'firefox', 'telegram', 'discord']
    
    for app in running_apps:
        app_name = app['name'].lower()
        if any(keyword in app_name for keyword in keywords):
            interesting_processes.append(app)
    
    if interesting_processes:
        for app in interesting_processes[:10]:  # Показываем первые 10
            print(f"• {app['name']} (PID: {app['pid']})")
    else:
        print("Интересные процессы не найдены")

def main():
    """Главная функция"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            list_running_processes()
            return
        elif sys.argv[1] == "--test":
            test_app_operations()
            return
    
    print("🔧 Утилита тестирования приложений")
    print("\nИспользование:")
    print("  python test_app_close.py --list   # Показать процессы")
    print("  python test_app_close.py --test   # Запустить тесты")
    
    # Интерактивный режим
    print("\n🎮 Интерактивный режим:")
    app_manager = AppManager()
    app_commands = AppCommandProcessor(app_manager)
    
    while True:
        try:
            command = input("\nВведите команду (или 'exit' для выхода): ").strip()
            
            if command.lower() in ['exit', 'quit', 'выход']:
                break
            
            if command.lower() == 'list':
                list_running_processes()
                continue
            
            # Обрабатываем команду
            handled, response = app_commands.process_command(command)
            if handled:
                print(f"✅ {response}")
            else:
                print(f"❌ Команда не распознана")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    print("\n👋 До свидания!")

if __name__ == "__main__":
    main()
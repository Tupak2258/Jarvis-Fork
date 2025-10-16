"""
Тестовый скрипт для проверки работы с Google Sheets
"""

import sys
import time
from modules.sheets_client import GoogleSheetsClient
from modules.sheets_commands import SheetsCommandProcessor
from modules.reports_manager import ReportsManager

def test_sheets_connection():
    """Тестирует подключение к Google Sheets"""
    print("🔗 Тестирование подключения к Google Sheets...")
    
    sheets_client = GoogleSheetsClient()
    
    if sheets_client.is_available():
        print("✅ Подключение к Google Sheets успешно!")
        return sheets_client
    else:
        print("❌ Не удалось подключиться к Google Sheets")
        print("💡 Проверьте:")
        print("  - Файл credentials/google_credentials.json существует")
        print("  - Учетные данные корректны")
        print("  - Google Sheets API включен")
        return None

def test_basic_operations(sheets_client):
    """Тестирует базовые операции с таблицей"""
    print("\n📋 Тестирование базовых операций...")
    
    # Тест 1: Добавление задачи
    print("\n1️⃣ Добавление задачи...")
    success = sheets_client.add_task("Тестовая задача от Джарвиса", priority="High", notes="Автоматический тест")
    if success:
        print("✅ Задача добавлена успешно")
    else:
        print("❌ Не удалось добавить задачу")
    
    # Тест 2: Получение задач
    print("\n2️⃣ Получение списка задач...")
    tasks = sheets_client.get_tasks()
    if tasks:
        print(f"✅ Найдено {len(tasks)} задач:")
        for i, task in enumerate(tasks[-3:], 1):  # Показываем последние 3
            print(f"   {i}. {task.get('Task', 'Без названия')} ({task.get('Status', 'Неизвестно')})")
    else:
        print("⚠️ Задачи не найдены")
    
    # Тест 3: Добавление заметки
    print("\n3️⃣ Добавление заметки...")
    success = sheets_client.add_note("Тестовая заметка - все работает!", category="Тестирование")
    if success:
        print("✅ Заметка добавлена успешно")
    else:
        print("❌ Не удалось добавить заметку")

def test_reports_manager(sheets_client):
    """Тестирует менеджер отчетов"""
    print("\n📊 Тестирование менеджера отчетов...")
    
    reports_manager = ReportsManager(sheets_client)
    
    # Тест 1: Начало рабочей сессии
    print("\n1️⃣ Начало рабочей сессии...")
    success, message = reports_manager.start_work_session(
        task="Тестирование Джарвиса", 
        category="Разработка", 
        priority="Высокий"
    )
    print(f"Результат: {message}")
    
    if success:
        print("⏳ Ждем 5 секунд для имитации работы...")
        time.sleep(5)
        
        # Тест 2: Завершение рабочей сессии
        print("\n2️⃣ Завершение рабочей сессии...")
        success, message = reports_manager.end_work_session(
            description="Протестировал все функции Google Sheets",
            notes="Все работает отлично!"
        )
        print(f"Результат: {message}")
    
    # Тест 3: Добавление записи о работе
    print("\n3️⃣ Добавление записи о работе...")
    success, message = reports_manager.add_work_entry(
        task="Написание документации",
        description="Создал руководство пользователя",
        duration_minutes=45,
        category="Документация"
    )
    print(f"Результат: {message}")
    
    # Тест 4: Дневной отчет
    print("\n4️⃣ Генерация дневного отчета...")
    success, report = reports_manager.get_daily_report()
    if success:
        print("✅ Дневной отчет:")
        print(report)
    else:
        print(f"❌ Ошибка генерации отчета: {report}")

def test_voice_commands(sheets_client):
    """Тестирует голосовые команды"""
    print("\n🗣️ Тестирование голосовых команд...")
    
    sheets_commands = SheetsCommandProcessor(sheets_client)
    
    test_commands = [
        "добавь задачу изучить новые технологии",
        "создай заметку встреча с командой завтра",
        "начинаю работу над проектом веб-сайт",
        "покажи мои задачи",
        "отчет за день"
    ]
    
    for i, command in enumerate(test_commands, 1):
        print(f"\n{i}️⃣ Тестируем команду: '{command}'")
        handled, response = sheets_commands.process_command(command)
        
        if handled:
            print(f"✅ Обработано: {response}")
            if i == 3:  # После начала работы ждем немного
                print("⏳ Ждем 3 секунды...")
                time.sleep(3)
                # Завершаем работу
                print("   Завершаем рабочую сессию...")
                handled2, response2 = sheets_commands.process_command("заканчиваю работу создал главную страницу")
                print(f"   Результат: {response2}")
        else:
            print(f"❌ Не обработано: {response}")
        
        time.sleep(1)  # Пауза между командами

def interactive_mode(sheets_client):
    """Интерактивный режим для тестирования"""
    print("\n🎮 Интерактивный режим тестирования Google Sheets")
    print("Доступные команды:")
    print("  - Любые команды для Google Sheets (добавь задачу, начинаю работу, отчет за день)")
    print("  - 'help' - показать справку")
    print("  - 'status' - показать статус подключения")
    print("  - 'exit' - выход")
    
    sheets_commands = SheetsCommandProcessor(sheets_client)
    
    while True:
        try:
            command = input("\n🎤 Введите команду: ").strip()
            
            if command.lower() in ['exit', 'quit', 'выход']:
                break
            elif command.lower() == 'help':
                print(sheets_commands.get_help_text())
                continue
            elif command.lower() == 'status':
                if sheets_client.is_available():
                    print("✅ Google Sheets подключен и готов к работе")
                else:
                    print("❌ Google Sheets недоступен")
                continue
            
            # Обрабатываем команду
            handled, response = sheets_commands.process_command(command)
            if handled:
                print(f"✅ {response}")
            else:
                print(f"❌ Команда не распознана как команда Google Sheets")
                print("💡 Попробуйте: 'добавь задачу ...', 'начинаю работу ...', 'отчет за день'")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    print("\n👋 Тестирование завершено!")

def main():
    """Главная функция"""
    print("🧪 Тестирование Google Sheets интеграции")
    print("=" * 50)
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = "full"
    
    # Тестируем подключение
    sheets_client = test_sheets_connection()
    if not sheets_client:
        return 1
    
    try:
        if mode == "connection":
            print("\n✅ Тест подключения завершен успешно!")
        elif mode == "basic":
            test_basic_operations(sheets_client)
        elif mode == "reports":
            test_reports_manager(sheets_client)
        elif mode == "voice":
            test_voice_commands(sheets_client)
        elif mode == "interactive":
            interactive_mode(sheets_client)
        elif mode == "full":
            test_basic_operations(sheets_client)
            test_reports_manager(sheets_client)
            test_voice_commands(sheets_client)
            
            print("\n🎉 Все тесты завершены!")
            print("\nХотите перейти в интерактивный режим? (y/n): ", end="")
            if input().lower().strip() in ['y', 'yes', 'да', 'д']:
                interactive_mode(sheets_client)
        else:
            print(f"❌ Неизвестный режим: {mode}")
            print("Доступные режимы: connection, basic, reports, voice, interactive, full")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n👋 Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
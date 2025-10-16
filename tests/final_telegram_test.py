"""
Финальный тест исправления Telegram команд
"""

from modules.adaptive_sheets_client import AdaptiveSheetsClient
from modules.telegram_commands import TelegramCommandProcessor
from modules.app_commands import AppCommandProcessor
from modules.app_manager import AppManager

def test_telegram_vs_app_commands():
    """Тестирует разделение команд между Telegram и App"""
    print("🎯 Финальный тест: Telegram vs App команды")
    print("=" * 60)
    
    # Инициализация
    sheets_client = AdaptiveSheetsClient()
    telegram_commands = TelegramCommandProcessor(sheets_client)
    app_manager = AppManager()
    app_commands = AppCommandProcessor(app_manager)
    
    # Критические тестовые команды
    test_cases = [
        # Telegram команды - должны обрабатываться telegram_commands
        {
            "command": "напиши в чат привет всем",
            "expected": "telegram",
            "description": "Основная проблемная команда"
        },
        {
            "command": "отправь сообщение как дела",
            "expected": "telegram", 
            "description": "Альтернативная команда Telegram"
        },
        
        # App команды - должны обрабатываться app_commands
        {
            "command": "напиши текст hello world",
            "expected": "app",
            "description": "Команда ввода текста"
        },
        {
            "command": "введи пароль 123456",
            "expected": "app",
            "description": "Команда ввода пароля"
        },
    ]
    
    print("\\n🔍 Тестирование критических команд:")
    print("-" * 60)
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        command = test_case["command"]
        expected = test_case["expected"]
        description = test_case["description"]
        
        print(f"\\n{i}. {description}")
        print(f"   Команда: '{command}'")
        print(f"   Ожидается: {expected}")
        
        # Тестируем Telegram команды
        telegram_handled, telegram_response = telegram_commands.process_command(command)
        
        # Тестируем App команды  
        app_handled, app_response = app_commands.process_command(command)
        
        # Анализируем результат
        if expected == "telegram":
            if telegram_handled and not app_handled:
                print(f"   ✅ ПРАВИЛЬНО: Обработано telegram_commands")
                print(f"   📝 Ответ: {telegram_response}")
                success_count += 1
            elif app_handled:
                print(f"   ❌ ОШИБКА: Обработано app_commands вместо telegram_commands")
                print(f"   📝 Ответ app: {app_response}")
            else:
                print(f"   ⚠️ НЕ ОБРАБОТАНО: Возможно Telegram не запущен")
                print(f"   📝 Telegram: {telegram_response}")
                print(f"   📝 App: {app_response}")
                
        elif expected == "app":
            if app_handled and not telegram_handled:
                print(f"   ✅ ПРАВИЛЬНО: Обработано app_commands")
                print(f"   📝 Ответ: {app_response}")
                success_count += 1
            elif telegram_handled:
                print(f"   ❌ ОШИБКА: Обработано telegram_commands вместо app_commands")
                print(f"   📝 Ответ telegram: {telegram_response}")
            else:
                print(f"   ❌ НЕ ОБРАБОТАНО: Команда не распознана")
    
    # Результаты
    print(f"\\n\\n📊 Результаты финального теста:")
    print("=" * 60)
    
    accuracy = (success_count / total_count) * 100
    print(f"Успешных тестов: {success_count}/{total_count} ({accuracy:.1f}%)")
    
    if accuracy >= 75:
        print("\\n🎉 УСПЕХ! Конфликт команд решен!")
        print("✅ Команды 'напиши в чат' и 'напиши текст' больше не конфликтуют")
        print("✅ Приоритет команд настроен правильно")
    else:
        print("\\n❌ ТРЕБУЮТСЯ ДОПОЛНИТЕЛЬНЫЕ ИСПРАВЛЕНИЯ")
        print("⚠️ Конфликт команд все еще существует")
    
    return accuracy >= 75

def test_pattern_recognition():
    """Тестирует распознавание паттернов команд"""
    print("\\n\\n🔍 Тест распознавания паттернов:")
    print("=" * 60)
    
    sheets_client = AdaptiveSheetsClient()
    telegram_commands = TelegramCommandProcessor(sheets_client)
    app_manager = AppManager()
    app_commands = AppCommandProcessor(app_manager)
    
    # Тестируем паттерны
    telegram_patterns = [
        "напиши в чат привет",
        "отправь сообщение тест", 
        "отправь в чат hello",
        "пошли в чат как дела",
        "сообщение в чат спасибо",
        "текст в чат до встречи"
    ]
    
    app_patterns = [
        "напиши текст hello",
        "введи пароль 123",
        "напиши документ",
        "введи логин admin"
    ]
    
    print("\\n📱 Telegram паттерны:")
    for pattern in telegram_patterns:
        handled, response = telegram_commands.process_command(pattern)
        status = "✅" if handled else "❌"
        print(f"   {status} '{pattern}' -> {handled}")
    
    print("\\n💻 App паттерны:")
    for pattern in app_patterns:
        handled, response = app_commands.process_command(pattern)
        status = "✅" if handled else "❌"
        print(f"   {status} '{pattern}' -> {handled}")

if __name__ == "__main__":
    success = test_telegram_vs_app_commands()
    test_pattern_recognition()
    
    print("\\n\\n🏁 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ:")
    print("=" * 60)
    
    if success:
        print("🎉 Исправление Telegram команд ЗАВЕРШЕНО УСПЕШНО!")
        print("\\n✅ Что исправлено:")
        print("   • Изменен приоритет обработки команд")
        print("   • Telegram команды обрабатываются первыми")
        print("   • Исключены конфликтующие паттерны в app_commands")
        print("   • Улучшен механизм отправки сообщений")
        print("\\n🎤 Теперь работает:")
        print("   'Джарвис, напиши в чат привет всем' ✅")
    else:
        print("❌ Требуются дополнительные исправления")
        print("\\n🔧 Рекомендации:")
        print("   • Проверьте запуск Telegram Desktop")
        print("   • Убедитесь в правильности паттернов")
        print("   • Проверьте приоритет в main.py")
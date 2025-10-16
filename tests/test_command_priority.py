"""
Тестирование приоритета обработки команд после исправлений
"""

from modules.adaptive_sheets_client import AdaptiveSheetsClient
from modules.telegram_commands import TelegramCommandProcessor
from modules.app_commands import AppCommandProcessor
from modules.sheets_commands import SheetsCommandProcessor
from modules.web_commands import WebCommandProcessor

def test_command_priority():
    """Тестирует приоритет обработки команд"""
    print("🧪 Тестирование приоритета команд после исправлений")
    print("=" * 60)
    
    # Инициализация всех обработчиков
    sheets_client = AdaptiveSheetsClient()
    telegram_commands = TelegramCommandProcessor(sheets_client)
    
    # Для app_commands нужен AppManager
    from modules.app_manager import AppManager
    app_manager = AppManager()
    app_commands = AppCommandProcessor(app_manager)
    
    sheets_commands = SheetsCommandProcessor(sheets_client)
    web_commands = WebCommandProcessor()  # Без параметров
    
    def process_command_with_priority(command):
        """Обрабатывает команду с правильным приоритетом"""
        # 1. Telegram команды (высший приоритет)
        handled, response = telegram_commands.process_command(command)
        if handled:
            return handled, response, "telegram_commands"
        
        # 2. Sheets команды
        handled, response = sheets_commands.process_command(command)
        if handled:
            return handled, response, "sheets_commands"
        
        # 3. Web команды
        handled, response = web_commands.process_command(command)
        if handled:
            return handled, response, "web_commands"
        
        # 4. App команды (низший приоритет)
        handled, response = app_commands.process_command(command)
        if handled:
            return handled, response, "app_commands"
        
        return False, "Команда не распознана", "unhandled"
    
    # Тестовые команды
    test_commands = [
        # Telegram команды (должны обрабатываться telegram_commands)
        ("напиши в чат привет всем", "telegram_commands"),
        ("отправь сообщение как дела", "telegram_commands"),
        ("отправь в чат тестирую", "telegram_commands"),
        ("пошли в чат все работает", "telegram_commands"),
        
        # App команды (должны обрабатываться app_commands)
        ("напиши текст hello world", "app_commands"),
        ("введи пароль 123456", "app_commands"),
        ("открой блокнот", "app_commands"),
        ("закрой браузер", "app_commands"),
        
        # Sheets команды
        ("добавь в таблицу тест", "sheets_commands"),
        ("запиши в гугл таблицу данные", "sheets_commands"),
        
        # Web команды
        ("найди в гугле python", "web_commands"),
        ("открой сайт github.com", "web_commands"),
    ]
    
    results = {
        "telegram_commands": {"correct": 0, "total": 0},
        "app_commands": {"correct": 0, "total": 0},
        "sheets_commands": {"correct": 0, "total": 0},
        "web_commands": {"correct": 0, "total": 0},
        "unhandled": {"correct": 0, "total": 0}
    }
    
    for i, (command, expected_handler) in enumerate(test_commands, 1):
        print(f"\n{i:2d}. Команда: '{command}'")
        print(f"    Ожидается: {expected_handler}")
        
        try:
            handled, response, actual_handler = process_command_with_priority(command)
            
            if handled:
                
                print(f"    ✅ Обработано: {actual_handler}")
                print(f"    📝 Ответ: {response}")
                
                # Проверяем правильность
                if actual_handler == expected_handler:
                    results[expected_handler]["correct"] += 1
                    print(f"    🎯 ПРАВИЛЬНО!")
                else:
                    print(f"    ❌ НЕПРАВИЛЬНО! Ожидался {expected_handler}, получен {actual_handler}")
                
                results[expected_handler]["total"] += 1
                
            else:
                print(f"    ❌ НЕ ОБРАБОТАНО: {response}")
                results["unhandled"]["total"] += 1
                
        except Exception as e:
            print(f"    💥 ОШИБКА: {e}")
            results["unhandled"]["total"] += 1
    
    # Статистика
    print(f"\n\n📊 Статистика тестирования:")
    print("=" * 60)
    
    total_correct = 0
    total_commands = 0
    
    for handler, stats in results.items():
        if stats["total"] > 0:
            accuracy = (stats["correct"] / stats["total"]) * 100
            print(f"{handler:15s}: {stats['correct']:2d}/{stats['total']:2d} ({accuracy:5.1f}%)")
            total_correct += stats["correct"]
            total_commands += stats["total"]
    
    if total_commands > 0:
        overall_accuracy = (total_correct / total_commands) * 100
        print(f"{'ОБЩАЯ ТОЧНОСТЬ':15s}: {total_correct:2d}/{total_commands:2d} ({overall_accuracy:5.1f}%)")
    
    # Рекомендации
    print(f"\n\n💡 Рекомендации:")
    if overall_accuracy >= 90:
        print("🎉 Отличная работа! Приоритет команд настроен правильно.")
    elif overall_accuracy >= 70:
        print("⚠️ Хорошо, но есть место для улучшений.")
    else:
        print("❌ Требуются дополнительные исправления приоритета команд.")
    
    return overall_accuracy >= 80

if __name__ == "__main__":
    test_command_priority()
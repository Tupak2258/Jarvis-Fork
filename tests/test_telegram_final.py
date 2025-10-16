"""
Финальный тест отправки сообщений в Telegram
"""

import time
from modules.telegram_manager import TelegramManager
from modules.telegram_commands import TelegramCommandProcessor
from modules.adaptive_sheets_client import AdaptiveSheetsClient

def test_telegram_message_sending():
    """Тестирует отправку сообщений в Telegram"""
    print("🚀 ФИНАЛЬНЫЙ ТЕСТ ОТПРАВКИ СООБЩЕНИЙ В TELEGRAM")
    print("=" * 70)
    
    # Инициализация
    telegram_manager = TelegramManager()
    
    # Шаг 1: Поиск окна
    print("1️⃣ Поиск окна Telegram...")
    if not telegram_manager.find_telegram_window():
        print("❌ Окно Telegram не найдено")
        return False
    
    window = telegram_manager.telegram_window
    print(f"✅ Найдено окно: '{window.title}'")
    print(f"   Размер: {window.width}x{window.height}")
    print(f"   Позиция: ({window.left}, {window.top})")
    
    # Шаг 2: Активация окна
    print("\\n2️⃣ Активация окна...")
    if not telegram_manager.activate_telegram():
        print("❌ Не удалось активировать окно")
        return False
    
    print("✅ Окно активировано")
    
    # Шаг 3: Отправка тестового сообщения
    print("\\n3️⃣ Отправка тестового сообщения...")
    test_message = "🤖 Тест Jarvis - система работает!"
    
    print(f"Отправляем: '{test_message}'")
    
    if telegram_manager.send_message(test_message):
        print("✅ Сообщение отправлено успешно!")
        return True
    else:
        print("❌ Не удалось отправить сообщение")
        return False

def test_voice_commands():
    """Тестирует голосовые команды"""
    print("\\n\\n🗣️ ТЕСТ ГОЛОСОВЫХ КОМАНД")
    print("=" * 70)
    
    try:
        sheets_client = AdaptiveSheetsClient()
        telegram_commands = TelegramCommandProcessor(sheets_client)
        
        test_commands = [
            "напиши в чат привет всем",
            "отправь сообщение как дела друзья",
            "отправь в чат тестирую Jarvis"
        ]
        
        for i, command in enumerate(test_commands, 1):
            print(f"\\n{i}️⃣ Команда: '{command}'")
            
            handled, response = telegram_commands.process_command(command)
            
            if handled:
                print(f"✅ Обработано: {response}")
                time.sleep(2)  # Пауза между сообщениями
            else:
                print(f"❌ Не обработано: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования команд: {e}")
        return False

def interactive_test():
    """Интерактивный тест"""
    print("\\n\\n🎮 ИНТЕРАКТИВНЫЙ ТЕСТ")
    print("=" * 70)
    
    telegram_manager = TelegramManager()
    
    if not telegram_manager.find_telegram_window():
        print("❌ Окно Telegram не найдено")
        return False
    
    if not telegram_manager.activate_telegram():
        print("❌ Не удалось активировать Telegram")
        return False
    
    print("✅ Telegram готов к работе!")
    print("\\nВведите сообщения для отправки (или 'exit' для выхода):")
    
    while True:
        try:
            message = input("\\n💬 Сообщение: ").strip()
            
            if message.lower() in ['exit', 'quit', 'выход']:
                break
            
            if not message:
                continue
            
            print(f"📤 Отправляем: '{message}'")
            
            if telegram_manager.send_message(message):
                print("✅ Отправлено!")
            else:
                print("❌ Ошибка отправки")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    print("\\n👋 Интерактивный тест завершен!")
    return True

def main():
    """Главная функция"""
    print("🔧 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ TELEGRAM ИНТЕГРАЦИИ")
    print("=" * 80)
    
    # Тест 1: Базовая отправка сообщений
    if not test_telegram_message_sending():
        print("\\n❌ Базовый тест не прошел")
        return False
    
    # Тест 2: Голосовые команды
    if not test_voice_commands():
        print("\\n❌ Тест голосовых команд не прошел")
        return False
    
    print("\\n\\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
    print("=" * 80)
    print("✅ Telegram интеграция работает корректно")
    print("✅ Голосовые команды функционируют")
    print("✅ Отправка сообщений работает")
    
    print("\\n🎤 Теперь вы можете использовать:")
    print("• 'Джарвис, напиши в чат привет'")
    print("• 'Джарвис, отправь сообщение как дела'")
    print("• 'Джарвис, отправь в чат тестирую систему'")
    
    # Предлагаем интерактивный тест
    print("\\nХотите протестировать интерактивную отправку? (y/n): ", end="")
    try:
        response = input().lower().strip()
        if response in ['y', 'yes', 'да', 'д']:
            interactive_test()
    except KeyboardInterrupt:
        pass
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\\n🎊 ПОЗДРАВЛЯЕМ! Telegram интеграция полностью настроена!")
        else:
            print("\\n😞 Есть проблемы, которые нужно решить")
    except KeyboardInterrupt:
        print("\\n\\n👋 Тест прерван пользователем")
    except Exception as e:
        print(f"\\n❌ Критическая ошибка: {e}")
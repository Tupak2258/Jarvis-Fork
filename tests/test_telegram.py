"""
Тестовый скрипт для проверки работы с Telegram
"""

import sys
import time
from modules.telegram_manager import TelegramManager
from modules.vision_analyzer import VisionAnalyzer
from modules.telegram_commands import TelegramCommandProcessor
from modules.adaptive_sheets_client import AdaptiveSheetsClient

def test_telegram_connection():
    """Тестирует подключение к Telegram"""
    print("📱 Тестирование подключения к Telegram...")
    
    telegram_manager = TelegramManager()
    
    if telegram_manager.is_telegram_running():
        print("✅ Telegram запущен")
        
        if telegram_manager.activate_telegram():
            print("✅ Окно Telegram активировано")
            return telegram_manager
        else:
            print("⚠️ Не удалось активировать окно Telegram")
            return telegram_manager
    else:
        print("❌ Telegram не запущен")
        print("💡 Запустите Telegram Desktop и повторите тест")
        return None

def test_screenshot():
    """Тестирует создание скриншотов"""
    print("\n📸 Тестирование скриншотов...")
    
    telegram_manager = TelegramManager()
    
    if not telegram_manager.is_telegram_running():
        print("❌ Telegram не запущен")
        return None
    
    screenshot_path = telegram_manager.take_screenshot()
    if screenshot_path:
        print(f"✅ Скриншот создан: {screenshot_path}")
        return screenshot_path
    else:
        print("❌ Не удалось создать скриншот")
        return None

def test_vision_analysis(screenshot_path):
    """Тестирует анализ изображений с помощью QwenVL"""
    print("\n🔍 Тестирование анализа изображений...")
    
    vision_analyzer = VisionAnalyzer()
    
    # Проверяем доступность модели
    if not vision_analyzer._check_model_availability():
        print("❌ Модель QwenVL недоступна")
        print("💡 Убедитесь, что Ollama запущен и модель qwen2.5vl:7b загружена")
        return False
    
    print("✅ Модель QwenVL доступна")
    
    # Тестируем общий анализ
    print("🔍 Выполняем общий анализ скриншота...")
    analysis = vision_analyzer.analyze_telegram_screenshot(screenshot_path, "general")
    
    if analysis.get('success'):
        print("✅ Анализ выполнен успешно")
        print(f"📋 Результат анализа:\n{analysis['response'][:300]}...")
        return True
    else:
        print(f"❌ Ошибка анализа: {analysis.get('error', 'Неизвестная ошибка')}")
        return False

def test_data_extraction(screenshot_path):
    """Тестирует извлечение структурированных данных"""
    print("\n📊 Тестирование извлечения данных...")
    
    vision_analyzer = VisionAnalyzer()
    
    # Извлекаем разные типы данных
    data_types = ['contacts', 'dates', 'numbers', 'tasks']
    structured_data = vision_analyzer.extract_structured_data(screenshot_path, data_types)
    
    if structured_data:
        print("✅ Данные извлечены:")
        for data_type, items in structured_data.items():
            if items:
                print(f"  📋 {data_type}: {len(items)} элементов")
                for item in items[:2]:  # Показываем первые 2
                    print(f"    • {item}")
        return structured_data
    else:
        print("⚠️ Данные не извлечены или не найдены")
        return {}

def test_voice_commands():
    """Тестирует голосовые команды"""
    print("\n🗣️ Тестирование голосовых команд...")
    
    try:
        sheets_client = AdaptiveSheetsClient()
        telegram_commands = TelegramCommandProcessor(sheets_client)
        
        test_commands = [
            "открой телеграм",
            "сделай скриншот телеграма",
            "прочитай чат",
            "найди контакты в чате"
        ]
        
        for i, command in enumerate(test_commands, 1):
            print(f"\n{i}️⃣ Тестируем команду: '{command}'")
            handled, response = telegram_commands.process_command(command)
            
            if handled:
                print(f"✅ Обработано: {response[:100]}...")
                time.sleep(2)  # Пауза между командами
            else:
                print(f"❌ Не обработано: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования команд: {e}")
        return False

def interactive_mode():
    """Интерактивный режим для тестирования"""
    print("\n🎮 Интерактивный режим тестирования Telegram")
    print("Доступные команды:")
    print("  - Любые команды для Telegram (открой телеграм, прочитай чат, извлеки данные)")
    print("  - 'screenshot' - сделать скриншот")
    print("  - 'analyze' - анализировать последний скриншот")
    print("  - 'help' - показать справку")
    print("  - 'exit' - выход")
    
    try:
        sheets_client = AdaptiveSheetsClient()
        telegram_commands = TelegramCommandProcessor(sheets_client)
        telegram_manager = TelegramManager()
        vision_analyzer = VisionAnalyzer()
        
        last_screenshot = None
        
        while True:
            try:
                command = input("\n🎤 Введите команду: ").strip()
                
                if command.lower() in ['exit', 'quit', 'выход']:
                    break
                elif command.lower() == 'help':
                    print(telegram_commands.get_help_text())
                    continue
                elif command.lower() == 'screenshot':
                    if telegram_manager.is_telegram_running():
                        last_screenshot = telegram_manager.take_screenshot()
                        if last_screenshot:
                            print(f"✅ Скриншот создан: {last_screenshot}")
                        else:
                            print("❌ Не удалось создать скриншот")
                    else:
                        print("❌ Telegram не запущен")
                    continue
                elif command.lower() == 'analyze':
                    if last_screenshot:
                        analysis = vision_analyzer.analyze_telegram_screenshot(last_screenshot, "general")
                        if analysis.get('success'):
                            print(f"✅ Анализ:\n{analysis['response']}")
                        else:
                            print(f"❌ Ошибка анализа: {analysis.get('error')}")
                    else:
                        print("❌ Сначала сделайте скриншот")
                    continue
                
                # Обрабатываем команду
                handled, response = telegram_commands.process_command(command)
                if handled:
                    print(f"✅ {response}")
                else:
                    print(f"❌ Команда не распознана как команда Telegram")
                    print("💡 Попробуйте: 'открой телеграм', 'прочитай чат', 'извлеки данные'")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")
        
        print("\n👋 Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")

def main():
    """Главная функция"""
    print("🧪 Тестирование Telegram интеграции")
    print("=" * 50)
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = "full"
    
    try:
        if mode == "connection":
            telegram_manager = test_telegram_connection()
            if telegram_manager:
                print("\n✅ Тест подключения завершен успешно!")
            else:
                print("\n❌ Тест подключения не прошел")
                return 1
                
        elif mode == "screenshot":
            screenshot_path = test_screenshot()
            if screenshot_path:
                print(f"\n✅ Скриншот создан: {screenshot_path}")
            else:
                return 1
                
        elif mode == "vision":
            screenshot_path = test_screenshot()
            if screenshot_path:
                success = test_vision_analysis(screenshot_path)
                if not success:
                    return 1
            else:
                return 1
                
        elif mode == "extraction":
            screenshot_path = test_screenshot()
            if screenshot_path:
                test_data_extraction(screenshot_path)
            else:
                return 1
                
        elif mode == "commands":
            test_voice_commands()
            
        elif mode == "interactive":
            interactive_mode()
            
        elif mode == "full":
            # Полный тест
            telegram_manager = test_telegram_connection()
            if not telegram_manager:
                return 1
            
            screenshot_path = test_screenshot()
            if not screenshot_path:
                return 1
            
            vision_success = test_vision_analysis(screenshot_path)
            if vision_success:
                test_data_extraction(screenshot_path)
            
            test_voice_commands()
            
            print("\n🎉 Все тесты завершены!")
            print("\nХотите перейти в интерактивный режим? (y/n): ", end="")
            if input().lower().strip() in ['y', 'yes', 'да', 'д']:
                interactive_mode()
        else:
            print(f"❌ Неизвестный режим: {mode}")
            print("Доступные режимы: connection, screenshot, vision, extraction, commands, interactive, full")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n👋 Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
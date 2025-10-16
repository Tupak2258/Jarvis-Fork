"""
Тестовый скрипт для проверки интеллектуального поиска приложений
"""

import sys
from modules.smart_app_finder import SmartAppFinder
from modules.app_manager import AppManager
from modules.app_commands import AppCommandProcessor

def test_smart_finder():
    """Тестирует интеллектуальный поиск приложений"""
    print("🧠 Тестирование интеллектуального поиска приложений")
    print("=" * 60)
    
    smart_finder = SmartAppFinder()
    
    # Тестовые запросы
    test_requests = [
        "открой телеграм",
        "запусти telegram",
        "включи дискорд",
        "открой хром",
        "запусти браузер",
        "открой блокнот",
        "включи калькулятор",
        "запусти ворд",
        "открой код",  # VS Code
        "включи спотифай",
        "открой стим",
        "запусти фотошоп"
    ]
    
    print("\n🔍 Тестирование поиска:")
    for request in test_requests:
        print(f"\n📝 Запрос: '{request}'")
        success, message, executable = smart_finder.find_app_intelligently(request)
        
        if success:
            print(f"✅ {message}")
            if executable:
                print(f"   Исполняемый файл: {executable}")
        else:
            print(f"❌ {message}")
    
    return smart_finder

def test_app_manager():
    """Тестирует AppManager с интеллектуальным поиском"""
    print("\n\n🔧 Тестирование AppManager с интеллектуальным поиском")
    print("=" * 60)
    
    app_manager = AppManager()
    
    test_apps = [
        "телеграм",
        "telegram",
        "дискорд",
        "хром",
        "блокнот",
        "калькулятор",
        "ворд",
        "код"
    ]
    
    print("\n🔍 Тестирование поиска приложений:")
    for app_name in test_apps:
        print(f"\n📝 Ищем: '{app_name}'")
        found_path = app_manager.find_app(app_name)
        
        if found_path:
            print(f"✅ Найдено: {found_path}")
        else:
            print(f"❌ Не найдено")
    
    return app_manager

def test_voice_commands():
    """Тестирует голосовые команды"""
    print("\n\n🗣️ Тестирование голосовых команд")
    print("=" * 60)
    
    app_manager = AppManager()
    app_commands = AppCommandProcessor(app_manager)
    
    test_commands = [
        "открой телеграм",
        "запусти дискорд",
        "включи хром",
        "открой блокнот",
        "запусти калькулятор",
        "открой несуществующую программу"
    ]
    
    print("\n🎤 Тестирование команд:")
    for command in test_commands:
        print(f"\n📝 Команда: '{command}'")
        handled, response = app_commands.process_command(command)
        
        if handled:
            print(f"✅ Обработано: {response}")
        else:
            print(f"❌ Не обработано: {response}")

def test_llm_integration():
    """Тестирует интеграцию с LLM"""
    print("\n\n🤖 Тестирование интеграции с LLM")
    print("=" * 60)
    
    smart_finder = SmartAppFinder()
    
    # Проверяем доступность LLM
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama доступен")
            
            # Тестируем LLM запросы
            test_names = [
                "телеграм",
                "хром", 
                "ворд",
                "фотошоп",
                "неизвестная программа"
            ]
            
            print("\n🧠 Тестирование LLM запросов:")
            for name in test_names:
                print(f"\n📝 Спрашиваем LLM про: '{name}'")
                result = smart_finder._ask_llm_for_app_name(name)
                if result:
                    print(f"✅ LLM ответил: {result}")
                else:
                    print(f"❌ LLM не смог определить")
        else:
            print("❌ Ollama недоступен")
    except Exception as e:
        print(f"❌ Ошибка подключения к Ollama: {e}")

def interactive_test():
    """Интерактивное тестирование"""
    print("\n\n🎮 Интерактивное тестирование")
    print("=" * 60)
    print("Введите название приложения для поиска (или 'exit' для выхода):")
    
    smart_finder = SmartAppFinder()
    app_manager = AppManager()
    
    while True:
        try:
            user_input = input("\n🔍 Введите название приложения: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'выход']:
                break
            
            if not user_input:
                continue
            
            print(f"\n📝 Ищем: '{user_input}'")
            
            # Тестируем интеллектуальный поиск
            success, message, executable = smart_finder.find_app_intelligently(f"открой {user_input}")
            print(f"🧠 Интеллектуальный поиск: {message}")
            
            # Тестируем обычный поиск
            found_path = app_manager.find_app(user_input)
            if found_path:
                print(f"🔧 Обычный поиск: Найдено - {found_path}")
            else:
                print(f"🔧 Обычный поиск: Не найдено")
            
            # Предлагаем открыть если найдено
            if success and executable:
                open_choice = input(f"\n❓ Открыть {executable}? (y/n): ").lower().strip()
                if open_choice in ['y', 'yes', 'да', 'д']:
                    success, message = app_manager.open_app(user_input)
                    print(f"🚀 Результат открытия: {message}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    print("\n👋 Тестирование завершено!")

def main():
    """Главная функция"""
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = "full"
    
    try:
        if mode == "finder":
            test_smart_finder()
        elif mode == "manager":
            test_app_manager()
        elif mode == "commands":
            test_voice_commands()
        elif mode == "llm":
            test_llm_integration()
        elif mode == "interactive":
            interactive_test()
        elif mode == "full":
            test_smart_finder()
            test_app_manager()
            test_voice_commands()
            test_llm_integration()
            
            print("\n🎉 Все тесты завершены!")
            print("\nХотите перейти в интерактивный режим? (y/n): ", end="")
            if input().lower().strip() in ['y', 'yes', 'да', 'д']:
                interactive_test()
        else:
            print(f"❌ Неизвестный режим: {mode}")
            print("Доступные режимы: finder, manager, commands, llm, interactive, full")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n👋 Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
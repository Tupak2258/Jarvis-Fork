"""
Улучшенный скрипт запуска Jarvis Assistant с проверкой зависимостей
"""

import sys
import os
import logging
from pathlib import Path

def setup_environment():
    """Настройка окружения"""
    # Добавляем текущую директорию в PYTHONPATH
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))

def check_critical_dependencies():
    """Проверка критически важных зависимостей"""
    critical_modules = [
        'colorama',
        'rich',
        'logging'
    ]
    
    missing = []
    for module in critical_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"❌ Критические модули отсутствуют: {', '.join(missing)}")
        print("📦 Установите зависимости: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Главная функция запуска"""
    print("🤖 Запуск Jarvis Assistant...")
    
    # Настройка окружения
    setup_environment()
    
    # Проверка критических зависимостей
    if not check_critical_dependencies():
        return 1
    
    try:
        # Импортируем и запускаем основное приложение
        from main import main as jarvis_main
        return jarvis_main()
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("🔧 Проверьте установку зависимостей: python check_dependencies.py")
        return 1
        
    except KeyboardInterrupt:
        print("\n👋 Jarvis остановлен пользователем")
        return 0
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("📋 Проверьте логи для подробной информации")
        return 1

if __name__ == "__main__":
    sys.exit(main())
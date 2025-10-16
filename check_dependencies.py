"""
Скрипт проверки зависимостей для Jarvis Assistant
"""

import sys
import importlib
from pathlib import Path

def check_dependency(module_name, package_name=None, optional=False):
    """Проверяет наличие зависимости"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name} - OK")
        return True
    except ImportError:
        status = "⚠️" if optional else "❌"
        pkg_name = package_name or module_name
        print(f"{status} {module_name} - НЕ НАЙДЕН (установите: pip install {pkg_name})")
        return optional

def main():
    """Основная функция проверки"""
    print("🔍 Проверка зависимостей Jarvis Assistant...\n")
    
    # Обязательные зависимости
    required_deps = [
        ("requests", "requests"),
        ("speech_recognition", "SpeechRecognition"),
        ("pyttsx3", "pyttsx3"),
        ("gspread", "gspread"),
        ("colorama", "colorama"),
        ("rich", "rich"),
        ("psutil", "psutil"),
    ]
    
    # Опциональные зависимости
    optional_deps = [
        ("pyautogui", "pyautogui"),
        ("win32gui", "pywin32"),
        ("flask", "flask"),
        ("pyaudio", "pyaudio"),
        ("sounddevice", "sounddevice"),
        ("numpy", "numpy"),
    ]
    
    print("📋 Обязательные зависимости:")
    all_required_ok = True
    for module, package in required_deps:
        if not check_dependency(module, package, optional=False):
            all_required_ok = False
    
    print("\n📋 Опциональные зависимости:")
    for module, package in optional_deps:
        check_dependency(module, package, optional=True)
    
    print("\n" + "="*50)
    
    if all_required_ok:
        print("✅ Все обязательные зависимости установлены!")
        print("🚀 Jarvis Assistant готов к запуску!")
    else:
        print("❌ Некоторые обязательные зависимости отсутствуют.")
        print("📦 Установите их командой: pip install -r requirements.txt")
        return 1
    
    # Проверка файлов конфигурации
    print("\n🔧 Проверка конфигурации:")
    
    config_files = [
        ("config/__init__.py", "обязательный"),
        ("config/settings.py", "обязательный"),
        ("modules/__init__.py", "обязательный"),
        (".env", "опциональный"),
        ("credentials/google_credentials.json", "опциональный"),
    ]
    
    config_ok = True
    for config_file, file_type in config_files:
        if Path(config_file).exists():
            print(f"✅ {config_file} - найден")
        else:
            if file_type == "обязательный":
                print(f"❌ {config_file} - не найден (обязательный)")
                config_ok = False
            else:
                print(f"⚠️ {config_file} - не найден (опциональный)")
    
    # Проверка импорта конфигурации
    try:
        from config import ASSISTANT_NAME, USER_NAME, WAKE_WORD
        print("✅ Конфигурация успешно импортирована")
    except ImportError as e:
        print(f"❌ Ошибка импорта конфигурации: {e}")
        config_ok = False
    
    if not config_ok:
        print("❌ Проблемы с конфигурацией. Проверьте файлы config/")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
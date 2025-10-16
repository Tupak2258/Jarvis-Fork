"""
Скрипт первоначальной настройки Jarvis Assistant
"""

import os
import sys
from pathlib import Path
import shutil

def create_directories():
    """Создает необходимые директории"""
    directories = [
        "logs",
        "data", 
        "credentials",
        "config",
        "modules",
        "docs"
    ]
    
    print("📁 Создание директорий...")
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"  ✅ {directory}/")

def check_config_files():
    """Проверяет и создает файлы конфигурации"""
    print("\n🔧 Проверка конфигурации...")
    
    config_files = {
        "config/__init__.py": True,
        "config/settings.py": True,
        ".env": False,
        "credentials/google_credentials.json": False
    }
    
    for file_path, required in config_files.items():
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            if required:
                print(f"  ❌ {file_path} - отсутствует (обязательный)")
                return False
            else:
                print(f"  ⚠️ {file_path} - отсутствует (опциональный)")
    
    return True

def copy_example_files():
    """Копирует примеры файлов"""
    print("\n📋 Настройка примеров...")
    
    examples = [
        (".env.example", ".env"),
        ("credentials/google_credentials_example.json", "credentials/google_credentials.json")
    ]
    
    for source, target in examples:
        if Path(source).exists() and not Path(target).exists():
            try:
                shutil.copy2(source, target)
                print(f"  ✅ Создан {target} из {source}")
            except Exception as e:
                print(f"  ⚠️ Не удалось создать {target}: {e}")

def check_python_version():
    """Проверяет версию Python"""
    print("🐍 Проверка версии Python...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"  ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ❌ Python {version.major}.{version.minor}.{version.micro}")
        print("  ⚠️ Требуется Python 3.8 или выше")
        return False

def install_dependencies():
    """Предлагает установить зависимости"""
    print("\n📦 Установка зависимостей...")
    
    if Path("requirements.txt").exists():
        print("  Найден файл requirements.txt")
        
        response = input("  Установить зависимости? (y/n): ").lower().strip()
        if response in ['y', 'yes', 'да', 'д']:
            try:
                import subprocess
                result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("  ✅ Зависимости установлены успешно")
                else:
                    print(f"  ❌ Ошибка установки: {result.stderr}")
            except Exception as e:
                print(f"  ❌ Ошибка: {e}")
        else:
            print("  ⚠️ Установка пропущена")
            print("  💡 Установите вручную: pip install -r requirements.txt")
    else:
        print("  ❌ Файл requirements.txt не найден")

def main():
    """Основная функция настройки"""
    print("🤖 Настройка Jarvis Assistant")
    print("=" * 40)
    
    # Проверка Python
    if not check_python_version():
        return 1
    
    # Создание директорий
    create_directories()
    
    # Копирование примеров
    copy_example_files()
    
    # Проверка конфигурации
    if not check_config_files():
        print("\n❌ Проблемы с конфигурацией!")
        print("💡 Убедитесь, что все необходимые файлы созданы")
        return 1
    
    # Установка зависимостей
    install_dependencies()
    
    print("\n" + "=" * 40)
    print("🎉 Настройка завершена!")
    print("\n📋 Следующие шаги:")
    print("1. Настройте файл .env под свои нужды")
    print("2. Установите и запустите Ollama: https://ollama.ai")
    print("3. Загрузите модель: ollama pull llama2")
    print("4. Запустите проверку: python check_dependencies.py")
    print("5. Запустите Jarvis: python start_jarvis.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
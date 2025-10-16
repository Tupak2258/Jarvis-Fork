"""
Скрипт для исправления проблемы с поиском Telegram
"""

import subprocess
import psutil
from pathlib import Path

def find_telegram_paths():
    """Находит все возможные пути к Telegram"""
    print("🔍 Поиск Telegram на системе...")
    
    telegram_paths = []
    
    # 1. Поиск через where
    try:
        result = subprocess.run(['where', 'telegram'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            paths = result.stdout.strip().split('\n')
            telegram_paths.extend(paths)
            print(f"✅ Найдено через 'where': {paths}")
    except Exception as e:
        print(f"⚠️ Ошибка 'where': {e}")
    
    # 2. Поиск среди запущенных процессов
    try:
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                if 'telegram' in proc.info['name'].lower():
                    if proc.info['exe']:
                        telegram_paths.append(proc.info['exe'])
                        print(f"✅ Найден запущенный процесс: {proc.info['exe']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        print(f"⚠️ Ошибка поиска процессов: {e}")
    
    # 3. Поиск в стандартных местах
    standard_paths = [
        Path.home() / "AppData" / "Roaming" / "Telegram Desktop" / "Telegram.exe",
        Path("C:") / "Users" / "Public" / "Desktop" / "Telegram.lnk",
        Path("C:") / "Program Files" / "Telegram Desktop" / "Telegram.exe",
        Path("C:") / "Program Files (x86)" / "Telegram Desktop" / "Telegram.exe",
    ]
    
    for path in standard_paths:
        if path.exists():
            telegram_paths.append(str(path))
            print(f"✅ Найден в стандартном месте: {path}")
    
    # Убираем дубликаты
    unique_paths = list(set(telegram_paths))
    
    print(f"\n📋 Всего найдено уникальных путей: {len(unique_paths)}")
    for i, path in enumerate(unique_paths, 1):
        print(f"  {i}. {path}")
    
    return unique_paths

def test_telegram_launch(paths):
    """Тестирует запуск Telegram по найденным путям"""
    print(f"\n🚀 Тестирование запуска Telegram...")
    
    for i, path in enumerate(paths, 1):
        print(f"\n{i}. Тестируем путь: {path}")
        try:
            # Проверяем существование файла
            if Path(path).exists():
                print(f"   ✅ Файл существует")
                
                # Пробуем запустить
                process = subprocess.Popen([path], shell=True)
                print(f"   ✅ Запуск успешен (PID: {process.pid})")
                
                # Ждем немного и проверяем, что процесс запустился
                import time
                time.sleep(2)
                
                if process.poll() is None:
                    print(f"   ✅ Процесс работает")
                    
                    # Завершаем тестовый процесс
                    try:
                        process.terminate()
                        print(f"   ✅ Тестовый процесс завершен")
                    except:
                        pass
                    
                    return path  # Возвращаем рабочий путь
                else:
                    print(f"   ❌ Процесс завершился сразу")
            else:
                print(f"   ❌ Файл не существует")
                
        except Exception as e:
            print(f"   ❌ Ошибка запуска: {e}")
    
    return None

def main():
    """Главная функция"""
    print("🔧 Диагностика и исправление проблемы с Telegram")
    print("=" * 60)
    
    # Находим пути к Telegram
    telegram_paths = find_telegram_paths()
    
    if not telegram_paths:
        print("\n❌ Telegram не найден на системе")
        print("💡 Убедитесь, что Telegram Desktop установлен")
        return 1
    
    # Тестируем запуск
    working_path = test_telegram_launch(telegram_paths)
    
    if working_path:
        print(f"\n🎉 Найден рабочий путь к Telegram: {working_path}")
        
        # Предлагаем обновить конфигурацию
        print(f"\n💡 Рекомендации:")
        print(f"1. Используйте полный путь: {working_path}")
        print(f"2. Или убедитесь, что Telegram в PATH")
        
        return 0
    else:
        print(f"\n❌ Ни один путь не работает")
        print(f"💡 Попробуйте переустановить Telegram Desktop")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
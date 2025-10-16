"""
Скрипт для исправления проблемы с окном Telegram
"""

import time
import psutil
import pygetwindow as gw
from modules.telegram_manager import TelegramManager

def show_telegram_status():
    """Показывает текущий статус Telegram"""
    print("📊 СТАТУС TELEGRAM")
    print("=" * 50)
    
    # Проверяем процессы
    telegram_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if 'telegram' in proc.info['name'].lower():
                telegram_processes.append(proc.info)
        except:
            continue
    
    if telegram_processes:
        print("✅ Процесс Telegram запущен:")
        for proc in telegram_processes:
            print(f"   • {proc['name']} (PID: {proc['pid']})")
            print(f"     Путь: {proc['exe']}")
    else:
        print("❌ Процесс Telegram не найден")
        return False
    
    # Проверяем окна
    all_windows = gw.getAllWindows()
    telegram_windows = []
    
    for window in all_windows:
        if 'telegram' in window.title.lower():
            telegram_windows.append(window)
    
    if telegram_windows:
        print("\\n✅ Окна Telegram найдены:")
        for window in telegram_windows:
            print(f"   • '{window.title}'")
            print(f"     Размер: {window.width}x{window.height}")
            print(f"     Видимо: {window.visible}")
    else:
        print("\\n❌ Окна Telegram не найдены")
        print("\\n🔍 Все доступные окна:")
        for i, window in enumerate(all_windows[:15]):
            print(f"   {i+1:2d}. '{window.title}'")
        if len(all_windows) > 15:
            print(f"   ... и еще {len(all_windows) - 15} окон")
    
    return len(telegram_windows) > 0

def manual_activation_guide():
    """Показывает руководство по ручной активации"""
    print("\\n\\n📋 РУКОВОДСТВО ПО АКТИВАЦИИ TELEGRAM")
    print("=" * 60)
    
    print("🎯 Telegram запущен, но окно скрыто. Попробуйте:")
    print()
    print("1️⃣ СИСТЕМНЫЙ ТРЕЙ:")
    print("   • Найдите иконку Telegram в правом нижнем углу экрана")
    print("   • Кликните по ней ЛЕВОЙ кнопкой мыши")
    print("   • Или кликните ПРАВОЙ кнопкой → 'Показать Telegram'")
    print()
    print("2️⃣ ГОРЯЧИЕ КЛАВИШИ:")
    print("   • Нажмите Win + R")
    print("   • Введите 'telegram' и нажмите Enter")
    print()
    print("3️⃣ ДИСПЕТЧЕР ЗАДАЧ:")
    print("   • Нажмите Ctrl + Shift + Esc")
    print("   • Найдите 'Telegram.exe' в списке")
    print("   • Кликните правой кнопкой → 'Перейти к окну'")
    print()
    print("4️⃣ ALT + TAB:")
    print("   • Нажмите Alt + Tab")
    print("   • Найдите Telegram среди открытых приложений")
    print()
    
    print("⏰ После активации у вас есть 30 секунд для проверки...")
    
    # Обратный отсчет
    for i in range(30, 0, -1):
        print(f"\\r⏳ Ожидание: {i:2d} сек (активируйте Telegram сейчас!)", end="", flush=True)
        time.sleep(1)
    
    print("\\n")

def test_after_activation():
    """Тестирует Telegram после активации"""
    print("\\n🧪 ПРОВЕРКА ПОСЛЕ АКТИВАЦИИ")
    print("=" * 50)
    
    telegram_manager = TelegramManager()
    
    if telegram_manager.find_telegram_window():
        print("✅ Окно Telegram найдено!")
        print(f"   Заголовок: '{telegram_manager.telegram_window.title}'")
        print(f"   Размер: {telegram_manager.telegram_window.width}x{telegram_manager.telegram_window.height}")
        
        # Тестируем активацию
        if telegram_manager.activate_telegram():
            print("✅ Окно успешно активировано!")
            
            # Предлагаем тест отправки сообщения
            print("\\n💬 Хотите протестировать отправку сообщения? (y/n): ", end="")
            try:
                response = input().lower().strip()
                if response in ['y', 'yes', 'да', 'д']:
                    test_message = "Тест Jarvis - Telegram работает! 🤖"
                    print(f"\\n📤 Отправляем: '{test_message}'")
                    
                    if telegram_manager.send_message(test_message):
                        print("✅ Сообщение отправлено успешно!")
                        print("\\n🎉 ВСЕ РАБОТАЕТ! Теперь голосовые команды должны функционировать.")
                        return True
                    else:
                        print("❌ Не удалось отправить сообщение")
                        print("💡 Убедитесь что открыт какой-то чат в Telegram")
                else:
                    print("\\n✅ Активация прошла успешно!")
                    return True
            except KeyboardInterrupt:
                print("\\n👋 Тест прерван")
                return True
        else:
            print("⚠️ Окно найдено, но не удалось его активировать")
    else:
        print("❌ Окно Telegram все еще не найдено")
        print("\\n💡 Попробуйте:")
        print("• Перезапустить Telegram Desktop")
        print("• Проверить настройки Telegram (Настройки → Дополнительно → Запуск)")
        print("• Убедиться что используете Desktop версию, а не веб")
        return False
    
    return True

def main():
    """Главная функция"""
    print("🔧 ИСПРАВЛЕНИЕ ПРОБЛЕМЫ С TELEGRAM")
    print("=" * 60)
    
    # Показываем статус
    has_window = show_telegram_status()
    
    if has_window:
        print("\\n✅ Telegram уже активен! Проверяем работоспособность...")
        return test_after_activation()
    
    # Показываем руководство
    manual_activation_guide()
    
    # Проверяем результат
    return test_after_activation()

if __name__ == "__main__":
    try:
        if main():
            print("\\n🎉 УСПЕХ! Telegram готов к работе с голосовыми командами.")
            print("\\nТеперь вы можете использовать:")
            print("• 'Джарвис, напиши в чат привет'")
            print("• 'Джарвис, отправь сообщение как дела'")
            print("• 'Джарвис, прочитай чат'")
            exit(0)
        else:
            print("\\n❌ Проблема не решена. Обратитесь за помощью.")
            exit(1)
    except KeyboardInterrupt:
        print("\\n\\n👋 Прервано пользователем")
        exit(0)
    except Exception as e:
        print(f"\\n❌ Критическая ошибка: {e}")
        exit(1)
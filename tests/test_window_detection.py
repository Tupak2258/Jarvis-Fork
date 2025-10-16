"""
Тестирование обнаружения окна Telegram по скриншоту
"""

import pygetwindow as gw
import time
from modules.telegram_manager import TelegramManager

def analyze_all_windows():
    """Анализирует все окна для поиска Telegram"""
    print("🔍 АНАЛИЗ ВСЕХ ОКОН")
    print("=" * 60)
    
    all_windows = gw.getAllWindows()
    print(f"Всего окон найдено: {len(all_windows)}")
    
    telegram_candidates = []
    
    for i, window in enumerate(all_windows):
        title = window.title
        
        # Ищем окна которые могут быть Telegram
        is_telegram_candidate = False
        
        # Проверяем размер (Telegram обычно большое окно)
        if window.width > 800 and window.height > 600:
            # Проверяем заголовок на наличие русских имен/чатов
            if any(char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя' for char in title.lower()):
                is_telegram_candidate = True
            
            # Или если это пустой заголовок у большого окна
            if not title.strip():
                is_telegram_candidate = True
        
        if is_telegram_candidate:
            telegram_candidates.append(window)
            print(f"🎯 КАНДИДАТ {len(telegram_candidates)}: '{title}'")
            print(f"   Размер: {window.width}x{window.height}")
            print(f"   Позиция: ({window.left}, {window.top})")
            print(f"   Видимо: {window.visible}")
            print()
        else:
            print(f"{i+1:2d}. '{title}' ({window.width}x{window.height})")
    
    return telegram_candidates

def test_telegram_detection():
    """Тестирует обнаружение Telegram"""
    print("\\n\\n🤖 ТЕСТИРОВАНИЕ ОБНАРУЖЕНИЯ TELEGRAM")
    print("=" * 60)
    
    telegram_manager = TelegramManager()
    
    # Тест 1: Стандартный поиск
    print("1️⃣ Стандартный поиск...")
    found = telegram_manager.find_telegram_window()
    print(f"   Результат: {found}")
    
    if found and telegram_manager.telegram_window:
        window = telegram_manager.telegram_window
        print(f"   Найденное окно: '{window.title}'")
        print(f"   Размер: {window.width}x{window.height}")
        
        # Тест активации
        print("\\n2️⃣ Тестирование активации...")
        activated = telegram_manager.activate_telegram()
        print(f"   Результат: {activated}")
        
        if activated:
            print("\\n3️⃣ Тестирование отправки сообщения...")
            test_message = "Тест обнаружения окна 🔍"
            sent = telegram_manager.send_message(test_message)
            print(f"   Результат: {sent}")
            
            if sent:
                print("\\n✅ ВСЕ РАБОТАЕТ ИДЕАЛЬНО!")
                return True
    
    print("\\n❌ Стандартное обнаружение не сработало")
    return False

def main():
    """Главная функция"""
    print("🔍 ДИАГНОСТИКА ОБНАРУЖЕНИЯ TELEGRAM ПО СКРИНШОТУ")
    print("=" * 80)
    
    # Анализируем все окна
    candidates = analyze_all_windows()
    
    if not candidates:
        print("\\n❌ Кандидаты на Telegram не найдены")
        return False
    
    print(f"\\n✅ Найдено {len(candidates)} кандидатов")
    
    # Тестируем обнаружение
    success = test_telegram_detection()
    
    if not success:
        print("\\n💡 РЕКОМЕНДАЦИИ:")
        print("• Telegram открыт, но система его не распознает")
        print("• Нужно улучшить алгоритм поиска окон")
        print("• Возможно, заголовок окна меняется в зависимости от чата")
    
    return success

if __name__ == "__main__":
    main()
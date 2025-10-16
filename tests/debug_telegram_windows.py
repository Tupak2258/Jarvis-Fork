"""
Отладка поиска правильного окна Telegram
"""

import pygetwindow as gw
import time

def analyze_telegram_windows():
    """Анализирует все окна связанные с Telegram"""
    print("🔍 АНАЛИЗ ВСЕХ ОКОН TELEGRAM")
    print("=" * 60)
    
    all_windows = gw.getAllWindows()
    telegram_windows = []
    
    for window in all_windows:
        title = window.title.lower()
        
        # Ищем все окна которые могут быть связаны с Telegram
        is_telegram_related = False
        
        # Прямые индикаторы
        if 'telegram' in title:
            is_telegram_related = True
        
        # Окна с @ символом (чаты)
        elif '@' in window.title:
            is_telegram_related = True
        
        # Окна с русскими именами больших размеров
        elif (window.width > 400 and window.height > 300 and 
              any(char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя' for char in title)):
            is_telegram_related = True
        
        if is_telegram_related:
            telegram_windows.append(window)
    
    if not telegram_windows:
        print("❌ Окна Telegram не найдены")
        return []
    
    print(f"✅ Найдено {len(telegram_windows)} окон связанных с Telegram:")
    
    for i, window in enumerate(telegram_windows, 1):
        print(f"\\n{i}. ОКНО: '{window.title}'")
        print(f"   Размер: {window.width}x{window.height}")
        print(f"   Позиция: ({window.left}, {window.top})")
        print(f"   Видимо: {window.visible}")
        
        # Анализируем характеристики
        score = 0
        reasons = []
        
        # Размер окна (большие окна лучше)
        if window.width > 800 and window.height > 600:
            score += 3
            reasons.append("Большой размер")
        elif window.width > 400 and window.height > 300:
            score += 1
            reasons.append("Средний размер")
        else:
            score -= 2
            reasons.append("Маленький размер")
        
        # Заголовок окна
        if '@' in window.title:
            score += 2
            reasons.append("Содержит @ (чат)")
        elif 'telegram' in window.title.lower():
            if window.title.lower() == 'telegramdesktop':
                score -= 1  # Техническое окно
                reasons.append("Техническое окно")
            else:
                score += 1
                reasons.append("Содержит 'telegram'")
        
        # Видимость
        if window.visible:
            score += 1
            reasons.append("Видимое")
        else:
            score -= 1
            reasons.append("Скрытое")
        
        print(f"   Оценка: {score} ({', '.join(reasons)})")
    
    # Сортируем по оценке
    telegram_windows.sort(key=lambda w: (
        # Приоритет 1: Окна с @ в заголовке
        2 if '@' in w.title else 0,
        # Приоритет 2: Большие видимые окна
        1 if w.visible and w.width > 400 and w.height > 300 else 0,
        # Приоритет 3: Размер окна
        w.width * w.height
    ), reverse=True)
    
    print(f"\\n🎯 ЛУЧШИЙ КАНДИДАТ: '{telegram_windows[0].title}'")
    
    return telegram_windows

def test_window_activation(window):
    """Тестирует активацию конкретного окна"""
    print(f"\\n🧪 ТЕСТ АКТИВАЦИИ ОКНА: '{window.title}'")
    print("=" * 60)
    
    try:
        # Активируем окно
        print("1️⃣ Активируем окно...")
        window.activate()
        time.sleep(1)
        
        # Проверяем активацию
        print("2️⃣ Проверяем активацию...")
        if hasattr(window, 'isActive'):
            print(f"   Активно: {window.isActive}")
        
        # Пробуем кликнуть в центр
        print("3️⃣ Кликаем в центр окна...")
        center_x = window.left + window.width // 2
        center_y = window.top + window.height // 2
        
        import pyautogui
        original_failsafe = pyautogui.FAILSAFE
        pyautogui.FAILSAFE = False
        
        pyautogui.click(center_x, center_y)
        time.sleep(1)
        
        # Пробуем ввести тестовый текст
        print("4️⃣ Пробуем ввести тест...")
        pyautogui.typewrite("test", interval=0.1)
        time.sleep(1)
        
        # Удаляем тестовый текст
        for _ in range(4):
            pyautogui.press('backspace')
            time.sleep(0.1)
        
        pyautogui.FAILSAFE = original_failsafe
        
        print("✅ Тест активации завершен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def interactive_window_selection():
    """Интерактивный выбор окна"""
    print("\\n\\n🎮 ИНТЕРАКТИВНЫЙ ВЫБОР ОКНА")
    print("=" * 60)
    
    windows = analyze_telegram_windows()
    
    if not windows:
        return None
    
    print("\\nВыберите окно для тестирования:")
    for i, window in enumerate(windows, 1):
        print(f"{i}. '{window.title}' ({window.width}x{window.height})")
    
    try:
        choice = int(input("\\nВаш выбор (номер): ")) - 1
        
        if 0 <= choice < len(windows):
            selected_window = windows[choice]
            print(f"\\n✅ Выбрано окно: '{selected_window.title}'")
            
            # Тестируем выбранное окно
            test_window_activation(selected_window)
            
            return selected_window
        else:
            print("❌ Неверный выбор")
            return None
            
    except (ValueError, KeyboardInterrupt):
        print("❌ Отменено")
        return None

def main():
    """Главная функция"""
    print("🔧 ОТЛАДКА ПОИСКА ПРАВИЛЬНОГО ОКНА TELEGRAM")
    print("=" * 80)
    
    # Анализируем все окна
    windows = analyze_telegram_windows()
    
    if not windows:
        print("\\n❌ Окна Telegram не найдены")
        return
    
    # Тестируем лучший кандидат
    best_window = windows[0]
    print(f"\\n🎯 Тестируем лучший кандидат: '{best_window.title}'")
    
    if test_window_activation(best_window):
        print("\\n✅ Лучший кандидат работает!")
    else:
        print("\\n❌ Лучший кандидат не работает")
        
        # Предлагаем интерактивный выбор
        print("\\nХотите выбрать окно вручную? (y/n): ", end="")
        try:
            response = input().lower().strip()
            if response in ['y', 'yes', 'да', 'д']:
                interactive_window_selection()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
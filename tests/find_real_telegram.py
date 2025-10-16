"""
Поиск настоящего окна Telegram (не панель задач)
"""

import pygetwindow as gw
import time
import pyautogui

def find_real_telegram_window():
    """Находит настоящее окно Telegram с интерфейсом"""
    print("🔍 ПОИСК НАСТОЯЩЕГО ОКНА TELEGRAM")
    print("=" * 60)
    
    all_windows = gw.getAllWindows()
    candidates = []
    
    for window in all_windows:
        title = window.title
        
        # Критерии для настоящего окна Telegram:
        # 1. Размер больше 400x300 (не панель задач)
        # 2. Содержит @ или русские символы (чат)
        # 3. Позиция не (-32000, -32000) (не свернутое)
        
        if (window.width > 400 and window.height > 300 and 
            window.left > -1000 and window.top > -1000):  # Не свернутое
            
            # Проверяем содержимое заголовка
            has_chat_indicators = (
                '@' in title or  # Символ чата
                any(char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя' for char in title.lower()) or  # Русские символы
                'telegram' in title.lower()  # Прямое упоминание
            )
            
            if has_chat_indicators:
                candidates.append(window)
    
    if not candidates:
        print("❌ Кандидаты не найдены")
        print("\\n🔍 Все большие окна:")
        for window in all_windows:
            if window.width > 400 and window.height > 300:
                print(f"  • '{window.title}' ({window.width}x{window.height}) pos:({window.left},{window.top})")
        return None
    
    print(f"✅ Найдено {len(candidates)} кандидатов:")
    
    for i, window in enumerate(candidates, 1):
        print(f"\\n{i}. '{window.title}'")
        print(f"   Размер: {window.width}x{window.height}")
        print(f"   Позиция: ({window.left}, {window.top})")
        print(f"   Видимо: {window.visible}")
        
        # Оценка качества
        score = 0
        
        # Размер (чем больше, тем лучше)
        if window.width > 800 and window.height > 600:
            score += 3
        elif window.width > 600 and window.height > 400:
            score += 2
        else:
            score += 1
        
        # Заголовок
        if '@' in window.title:
            score += 2  # Чат
        elif any(char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя' for char in window.title.lower()):
            score += 1  # Русский текст
        
        # Видимость
        if window.visible:
            score += 1
        
        print(f"   Оценка: {score}")
    
    # Выбираем лучший
    best_window = max(candidates, key=lambda w: (
        w.width * w.height,  # Размер
        2 if '@' in w.title else 0,  # Чат
        1 if w.visible else 0  # Видимость
    ))
    
    print(f"\\n🎯 ЛУЧШИЙ КАНДИДАТ: '{best_window.title}'")
    print(f"   Размер: {best_window.width}x{best_window.height}")
    
    return best_window

def test_telegram_interaction(window):
    """Тестирует взаимодействие с окном Telegram"""
    print(f"\\n🧪 ТЕСТ ВЗАИМОДЕЙСТВИЯ С: '{window.title}'")
    print("=" * 60)
    
    try:
        # Отключаем fail-safe
        original_failsafe = pyautogui.FAILSAFE
        pyautogui.FAILSAFE = False
        
        # Активируем окно
        print("1️⃣ Активируем окно...")
        window.activate()
        time.sleep(1)
        
        # Кликаем в центр для фокуса
        center_x = window.left + window.width // 2
        center_y = window.top + window.height // 2
        
        print(f"2️⃣ Кликаем в центр ({center_x}, {center_y})...")
        pyautogui.click(center_x, center_y)
        time.sleep(1)
        
        # Пробуем найти поле ввода (обычно внизу)
        input_x = window.left + window.width // 2
        input_y = window.top + window.height - 50  # Поле ввода внизу
        
        print(f"3️⃣ Кликаем в поле ввода ({input_x}, {input_y})...")
        pyautogui.click(input_x, input_y)
        time.sleep(1)
        
        # Тестируем ввод
        test_message = "Тест поиска правильного окна 🎯"
        
        print(f"4️⃣ Вводим тестовое сообщение: '{test_message}'")
        
        # Очищаем поле
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        
        # Вводим сообщение
        pyautogui.typewrite(test_message, interval=0.03)
        time.sleep(1)
        
        print("5️⃣ Готовы отправить? (Enter для отправки, любая клавиша для отмены)")
        
        # Ждем подтверждения пользователя
        import msvcrt
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\\r':  # Enter
                pyautogui.press('enter')
                print("✅ Сообщение отправлено!")
            else:
                # Очищаем поле
                pyautogui.hotkey('ctrl', 'a')
                pyautogui.press('delete')
                print("❌ Отправка отменена, поле очищено")
        else:
            # Автоматически отправляем через 3 секунды
            print("⏰ Автоотправка через 3 секунды...")
            time.sleep(3)
            pyautogui.press('enter')
            print("✅ Сообщение отправлено автоматически!")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False
    finally:
        # Восстанавливаем fail-safe
        pyautogui.FAILSAFE = original_failsafe

def manual_window_selection():
    """Ручной выбор окна из всех больших окон"""
    print("\\n\\n🎮 РУЧНОЙ ВЫБОР ОКНА")
    print("=" * 60)
    
    all_windows = gw.getAllWindows()
    big_windows = [w for w in all_windows if w.width > 400 and w.height > 300 and w.left > -1000]
    
    if not big_windows:
        print("❌ Больших окон не найдено")
        return None
    
    print("Все большие окна:")
    for i, window in enumerate(big_windows, 1):
        print(f"{i:2d}. '{window.title}' ({window.width}x{window.height})")
    
    try:
        choice = int(input("\\nВыберите номер окна: ")) - 1
        
        if 0 <= choice < len(big_windows):
            selected = big_windows[choice]
            print(f"\\n✅ Выбрано: '{selected.title}'")
            return selected
        else:
            print("❌ Неверный номер")
            return None
            
    except (ValueError, KeyboardInterrupt):
        print("❌ Отменено")
        return None

def main():
    """Главная функция"""
    print("🔧 ПОИСК НАСТОЯЩЕГО ОКНА TELEGRAM")
    print("=" * 80)
    
    # Автоматический поиск
    window = find_real_telegram_window()
    
    if window:
        # Тестируем найденное окно
        if test_telegram_interaction(window):
            print("\\n🎉 УСПЕХ! Найдено правильное окно Telegram!")
            print(f"Окно: '{window.title}'")
            print(f"Размер: {window.width}x{window.height}")
            print(f"Позиция: ({window.left}, {window.top})")
        else:
            print("\\n❌ Найденное окно не работает")
    else:
        print("\\n❌ Автоматический поиск не дал результатов")
    
    # Предлагаем ручной выбор
    print("\\nХотите выбрать окно вручную? (y/n): ", end="")
    try:
        response = input().lower().strip()
        if response in ['y', 'yes', 'да', 'д']:
            manual_window = manual_window_selection()
            if manual_window:
                test_telegram_interaction(manual_window)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
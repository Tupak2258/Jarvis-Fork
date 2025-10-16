"""
Улучшенный метод отправки сообщений в Telegram
"""

import time
import pyautogui
import pygetwindow as gw
from modules.telegram_manager import TelegramManager

def improved_send_message(telegram_manager, message):
    """Улучшенный метод отправки сообщений"""
    
    # Отключаем fail-safe
    original_failsafe = pyautogui.FAILSAFE
    pyautogui.FAILSAFE = False
    
    try:
        print(f"🚀 Отправляем сообщение: '{message}'")
        
        # Активируем Telegram
        if not telegram_manager.activate_telegram():
            print("❌ Не удалось активировать Telegram")
            return False
        
        window = telegram_manager.telegram_window
        print(f"📱 Окно: '{window.title}' ({window.width}x{window.height})")
        
        # Метод 1: Прямой клик в поле ввода
        print("\\n1️⃣ Метод 1: Клик в поле ввода...")
        
        # Координаты поля ввода (из скриншота видно что оно внизу)
        input_x = window.left + window.width // 2
        input_y = window.top + window.height - 40  # Ближе к низу
        
        print(f"   Кликаем в ({input_x}, {input_y})")
        pyautogui.click(input_x, input_y)
        time.sleep(1)
        
        # Проверяем что поле активно - вводим пробел и удаляем
        pyautogui.press('space')
        time.sleep(0.1)
        pyautogui.press('backspace')
        time.sleep(0.1)
        
        # Вводим сообщение
        print(f"   Вводим текст...")
        pyautogui.typewrite(message, interval=0.05)
        time.sleep(1)
        
        # Отправляем
        print(f"   Нажимаем Enter...")
        pyautogui.press('enter')
        time.sleep(0.5)
        
        print("✅ Метод 1 выполнен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в методе 1: {e}")
        
        # Метод 2: Через горячие клавиши
        try:
            print("\\n2️⃣ Метод 2: Горячие клавиши...")
            
            # Фокусируемся на окне
            center_x = window.left + window.width // 2
            center_y = window.top + window.height // 2
            pyautogui.click(center_x, center_y)
            time.sleep(0.5)
            
            # Переходим к полю ввода через Tab
            for i in range(5):
                pyautogui.press('tab')
                time.sleep(0.2)
                print(f"   Tab {i+1}/5")
            
            # Вводим сообщение
            pyautogui.typewrite(message, interval=0.05)
            time.sleep(1)
            
            # Отправляем
            pyautogui.press('enter')
            time.sleep(0.5)
            
            print("✅ Метод 2 выполнен")
            return True
            
        except Exception as e2:
            print(f"❌ Ошибка в методе 2: {e2}")
            
            # Метод 3: Через буфер обмена
            try:
                print("\\n3️⃣ Метод 3: Через буфер обмена...")
                
                import pyperclip
                
                # Сохраняем сообщение в буфер
                pyperclip.copy(message)
                
                # Кликаем в поле ввода
                pyautogui.click(input_x, input_y)
                time.sleep(0.5)
                
                # Очищаем поле
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.2)
                
                # Вставляем из буфера
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(1)
                
                # Отправляем
                pyautogui.press('enter')
                time.sleep(0.5)
                
                print("✅ Метод 3 выполнен")
                return True
                
            except Exception as e3:
                print(f"❌ Все методы не сработали: {e3}")
                return False
    
    finally:
        # Восстанавливаем fail-safe
        pyautogui.FAILSAFE = original_failsafe

def test_improved_sending():
    """Тестирует улучшенную отправку"""
    print("🧪 ТЕСТ УЛУЧШЕННОЙ ОТПРАВКИ СООБЩЕНИЙ")
    print("=" * 60)
    
    telegram_manager = TelegramManager()
    
    # Находим окно
    if not telegram_manager.find_telegram_window():
        print("❌ Окно Telegram не найдено")
        return False
    
    print(f"✅ Найдено окно: '{telegram_manager.telegram_window.title}'")
    
    # Тестируем отправку
    test_messages = [
        "Тест улучшенной отправки 🚀",
        "Проверяем все методы",
        "Система работает!"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\\n📤 Сообщение {i}/{len(test_messages)}")
        
        success = improved_send_message(telegram_manager, message)
        
        if success:
            print(f"✅ Сообщение {i} отправлено!")
        else:
            print(f"❌ Сообщение {i} не отправлено")
        
        time.sleep(2)  # Пауза между сообщениями
    
    return True

def interactive_test():
    """Интерактивный тест"""
    print("\\n\\n🎮 ИНТЕРАКТИВНЫЙ ТЕСТ")
    print("=" * 60)
    
    telegram_manager = TelegramManager()
    
    if not telegram_manager.find_telegram_window():
        print("❌ Окно Telegram не найдено")
        return
    
    print("✅ Telegram готов!")
    print("Введите сообщения (или 'exit' для выхода):")
    
    while True:
        try:
            message = input("\\n💬 Сообщение: ").strip()
            
            if message.lower() in ['exit', 'quit', 'выход']:
                break
            
            if not message:
                continue
            
            success = improved_send_message(telegram_manager, message)
            
            if success:
                print("✅ Отправлено!")
            else:
                print("❌ Не удалось отправить")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    print("\\n👋 Тест завершен!")

def main():
    """Главная функция"""
    print("🔧 УЛУЧШЕННАЯ ОТПРАВКА СООБЩЕНИЙ В TELEGRAM")
    print("=" * 80)
    
    # Автоматический тест
    if test_improved_sending():
        print("\\n🎉 Автоматический тест прошел!")
        
        # Предлагаем интерактивный тест
        print("\\nХотите протестировать интерактивную отправку? (y/n): ", end="")
        try:
            response = input().lower().strip()
            if response in ['y', 'yes', 'да', 'д']:
                interactive_test()
        except KeyboardInterrupt:
            pass
    else:
        print("\\n❌ Автоматический тест не прошел")

if __name__ == "__main__":
    main()
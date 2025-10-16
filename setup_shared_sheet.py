"""
Скрипт для настройки работы с существующей Google Sheets таблицей
"""

import sys
from modules.sheets_client import GoogleSheetsClient

def setup_shared_sheet():
    """Настраивает работу с существующей таблицей"""
    print("🔧 Настройка работы с существующей Google Sheets таблицей")
    print("=" * 60)
    
    print("\n📋 Инструкция:")
    print("1. Откройте Google Sheets в браузере")
    print("2. Создайте новую таблицу или откройте существующую")
    print("3. Нажмите кнопку 'Поделиться' (Share)")
    print("4. Добавьте этот email с правами 'Редактор':")
    print("   📧 jarvis@jarvis-472400.iam.gserviceaccount.com")
    print("5. Снимите галочку 'Уведомить пользователей'")
    print("6. Нажмите 'Поделиться'")
    
    print("\n⏳ После выполнения этих шагов нажмите Enter...")
    input()
    
    # Запрашиваем название таблицы
    print("\n📝 Введите название вашей таблицы:")
    sheet_name = input("Название: ").strip()
    
    if not sheet_name:
        print("❌ Название таблицы не может быть пустым")
        return False
    
    # Тестируем подключение
    print(f"\n🔍 Тестируем подключение к таблице '{sheet_name}'...")
    
    try:
        sheets_client = GoogleSheetsClient()
        
        if not sheets_client.is_available():
            print("❌ Google Sheets клиент недоступен")
            return False
        
        # Пробуем открыть таблицу
        try:
            spreadsheet = sheets_client.client.open(sheet_name)
            print(f"✅ Таблица '{sheet_name}' найдена!")
            print(f"📊 URL: {spreadsheet.url}")
            print(f"📋 Листов: {len(spreadsheet.worksheets())}")
            
            # Показываем существующие листы
            worksheets = spreadsheet.worksheets()
            print("\n📄 Существующие листы:")
            for i, ws in enumerate(worksheets, 1):
                print(f"  {i}. {ws.title}")
            
            # Обновляем конфигурацию
            update_config(sheet_name)
            
            # Настраиваем базовые листы если нужно
            setup_jarvis_sheets(sheets_client, spreadsheet)
            
            return True
            
        except Exception as e:
            print(f"❌ Не удалось открыть таблицу '{sheet_name}': {e}")
            print("\n💡 Возможные причины:")
            print("  - Таблица не была расшарена с service account")
            print("  - Неправильное название таблицы")
            print("  - Нет прав доступа")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def update_config(sheet_name):
    """Обновляет конфигурацию с новым названием таблицы"""
    try:
        # Читаем текущую конфигурацию
        with open('config/settings.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменяем название таблицы
        old_line = 'SPREADSHEET_NAME = "Jarvis Assistant Data"'
        new_line = f'SPREADSHEET_NAME = "{sheet_name}"'
        
        if old_line in content:
            content = content.replace(old_line, new_line)
            
            # Записываем обновленную конфигурацию
            with open('config/settings.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Конфигурация обновлена: SPREADSHEET_NAME = '{sheet_name}'")
        else:
            print("⚠️ Не удалось обновить конфигурацию автоматически")
            print(f"💡 Вручную измените SPREADSHEET_NAME на '{sheet_name}' в config/settings.py")
            
    except Exception as e:
        print(f"⚠️ Ошибка обновления конфигурации: {e}")

def setup_jarvis_sheets(sheets_client, spreadsheet):
    """Настраивает листы для Jarvis если их нет"""
    print("\n🔧 Настройка листов для Jarvis...")
    
    required_sheets = {
        'Conversations': ['Timestamp', 'User Input', 'AI Response', 'Command'],
        'Tasks': ['Date', 'Task', 'Status', 'Priority', 'Notes'],
        'Commands': ['Timestamp', 'Command', 'Result', 'Error'],
        'Work_Reports': ['Дата', 'Время начала', 'Время окончания', 'Задача/Проект', 
                        'Описание работы', 'Статус', 'Время работы (мин)', 
                        'Категория', 'Приоритет', 'Заметки']
    }
    
    existing_sheets = [ws.title for ws in spreadsheet.worksheets()]
    
    for sheet_name, headers in required_sheets.items():
        if sheet_name not in existing_sheets:
            try:
                print(f"  📄 Создаю лист '{sheet_name}'...")
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=len(headers))
                worksheet.update('1:1', [headers])
                
                # Форматирование заголовков
                worksheet.format('1:1', {
                    'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
                    'textFormat': {'bold': True}
                })
                
                print(f"  ✅ Лист '{sheet_name}' создан")
            except Exception as e:
                print(f"  ⚠️ Не удалось создать лист '{sheet_name}': {e}")
        else:
            print(f"  ✅ Лист '{sheet_name}' уже существует")

def test_functionality():
    """Тестирует основную функциональность"""
    print("\n🧪 Тестирование функциональности...")
    
    try:
        sheets_client = GoogleSheetsClient()
        
        # Тест добавления задачи
        print("  📋 Тестируем добавление задачи...")
        success = sheets_client.add_task("Тестовая задача - настройка завершена!", priority="High")
        if success:
            print("  ✅ Задача добавлена успешно")
        else:
            print("  ❌ Не удалось добавить задачу")
        
        # Тест добавления заметки
        print("  📝 Тестируем добавление заметки...")
        success = sheets_client.add_note("Google Sheets настроен и работает!")
        if success:
            print("  ✅ Заметка добавлена успешно")
        else:
            print("  ❌ Не удалось добавить заметку")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Ошибка тестирования: {e}")
        return False

def main():
    """Главная функция"""
    try:
        if setup_shared_sheet():
            if test_functionality():
                print("\n🎉 Настройка завершена успешно!")
                print("\n📋 Что дальше:")
                print("1. Запустите полный тест: python test_google_sheets.py")
                print("2. Запустите Jarvis: python start_jarvis.py")
                print("3. Попробуйте команды: 'добавь задачу', 'начинаю работу', 'отчет за день'")
                return 0
            else:
                print("\n⚠️ Настройка завершена, но тестирование не прошло")
                return 1
        else:
            print("\n❌ Настройка не завершена")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n👋 Настройка прервана пользователем")
        return 1
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
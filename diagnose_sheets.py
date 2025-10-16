"""
Диагностический скрипт для Google Sheets
"""

import os
from modules.sheets_client import GoogleSheetsClient
from config import GOOGLE_SPREADSHEET_ID, GOOGLE_CREDENTIALS_PATH

def diagnose_connection():
    """Диагностирует подключение к Google Sheets"""
    print("🔍 Диагностика Google Sheets подключения")
    print("=" * 50)
    
    # Проверяем переменные окружения
    print("\n📋 Переменные окружения:")
    print(f"GOOGLE_SPREADSHEET_ID: {GOOGLE_SPREADSHEET_ID}")
    print(f"GOOGLE_SHEETS_ENABLED: {os.environ.get('GOOGLE_SHEETS_ENABLED', 'не установлено')}")
    
    # Проверяем файл credentials
    print(f"\n🔑 Файл credentials:")
    print(f"Путь: {GOOGLE_CREDENTIALS_PATH}")
    print(f"Существует: {GOOGLE_CREDENTIALS_PATH.exists()}")
    
    if GOOGLE_CREDENTIALS_PATH.exists():
        try:
            import json
            with open(GOOGLE_CREDENTIALS_PATH, 'r') as f:
                creds = json.load(f)
            print(f"Service Account Email: {creds.get('client_email', 'не найден')}")
            print(f"Project ID: {creds.get('project_id', 'не найден')}")
        except Exception as e:
            print(f"Ошибка чтения credentials: {e}")
    
    # Тестируем подключение
    print(f"\n🔗 Тестирование подключения:")
    try:
        sheets_client = GoogleSheetsClient()
        
        if not sheets_client.is_available():
            print("❌ Клиент недоступен")
            return
        
        print("✅ Клиент инициализирован")
        
        # Пробуем открыть таблицу по ID
        if GOOGLE_SPREADSHEET_ID:
            try:
                spreadsheet = sheets_client.client.open_by_key(GOOGLE_SPREADSHEET_ID)
                print(f"✅ Таблица открыта по ID: {GOOGLE_SPREADSHEET_ID}")
                print(f"📊 Название таблицы: {spreadsheet.title}")
                print(f"🔗 URL: {spreadsheet.url}")
                
                # Показываем листы
                worksheets = spreadsheet.worksheets()
                print(f"📄 Листов в таблице: {len(worksheets)}")
                for i, ws in enumerate(worksheets, 1):
                    print(f"  {i}. {ws.title} ({ws.row_count}x{ws.col_count})")
                
                # Пробуем прочитать данные из первого листа
                if worksheets:
                    first_sheet = worksheets[0]
                    print(f"\n📖 Пробуем прочитать данные из листа '{first_sheet.title}':")
                    try:
                        # Читаем первые 3 строки
                        values = first_sheet.get_all_values()[:3]
                        for i, row in enumerate(values, 1):
                            print(f"  Строка {i}: {row[:5]}...")  # Показываем первые 5 колонок
                        print("✅ Чтение данных успешно")
                    except Exception as e:
                        print(f"❌ Ошибка чтения данных: {e}")
                
                # Пробуем записать тестовые данные
                print(f"\n✏️ Пробуем записать тестовые данные:")
                try:
                    # Ищем лист Tasks или создаем его
                    task_sheet = None
                    for ws in worksheets:
                        if ws.title == 'Tasks':
                            task_sheet = ws
                            break
                    
                    if not task_sheet:
                        print("📄 Создаем лист 'Tasks'...")
                        task_sheet = spreadsheet.add_worksheet(title='Tasks', rows=100, cols=5)
                        task_sheet.update('A1:E1', [['Date', 'Task', 'Status', 'Priority', 'Notes']])
                        print("✅ Лист 'Tasks' создан")
                    
                    # Добавляем тестовую запись
                    import datetime
                    test_row = [
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Тестовая задача - диагностика",
                        "New",
                        "Medium",
                        "Автоматический тест подключения"
                    ]
                    
                    task_sheet.append_row(test_row)
                    print("✅ Тестовая запись добавлена успешно!")
                    
                    # Читаем последнюю запись для проверки
                    all_records = task_sheet.get_all_records()
                    if all_records:
                        last_record = all_records[-1]
                        print(f"📖 Последняя запись: {last_record.get('Task', 'не найдено')}")
                    
                except Exception as e:
                    print(f"❌ Ошибка записи данных: {e}")
                    print(f"Тип ошибки: {type(e).__name__}")
                    if hasattr(e, 'response'):
                        print(f"HTTP статус: {e.response.status_code}")
                        print(f"Ответ сервера: {e.response.text[:200]}...")
                
            except Exception as e:
                print(f"❌ Ошибка открытия таблицы по ID: {e}")
                print(f"Тип ошибки: {type(e).__name__}")
        else:
            print("⚠️ GOOGLE_SPREADSHEET_ID не установлен")
    
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    diagnose_connection()
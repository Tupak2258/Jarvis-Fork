# 🔧 Настройка Google Sheets для Jarvis

## Проблема: Service Account использует квоту проекта, а не личную

Текущий service account `jarvis@jarvis-472400.iam.gserviceaccount.com` использует квоту Google Cloud проекта, которая ограничена. Нужно настроить доступ к вашему личному Google Drive с 2TB.

## 🎯 Решение 1: Поделиться таблицей с существующим Service Account

### Шаги:
1. Откройте [Google Sheets](https://sheets.google.com)
2. Создайте новую таблицу или откройте существующую
3. Нажмите кнопку **"Поделиться"** (Share)
4. В поле "Добавить пользователей и группы" введите:
   ```
   jarvis@jarvis-472400.iam.gserviceaccount.com
   ```
5. Выберите роль **"Редактор"** (Editor)
6. Снимите галочку **"Уведомить пользователей"** (Notify people)
7. Нажмите **"Поделиться"**
8. Скопируйте URL таблицы или её название

### Обновите конфигурацию:
```python
# В config/settings.py измените:
SPREADSHEET_NAME = "Название вашей таблицы"
# или используйте ID таблицы из URL
```

## 🎯 Решение 2: Создать новый Service Account в личном проекте

### Шаги:
1. Перейдите в [Google Cloud Console](https://console.cloud.google.com)
2. Создайте новый проект или выберите существующий
3. Включите Google Sheets API и Google Drive API
4. Создайте новый Service Account
5. Скачайте JSON ключ
6. Замените файл `credentials/google_credentials.json`

## 🎯 Решение 3: Использовать OAuth2 (рекомендуется для личного использования)

Для личного использования лучше использовать OAuth2, который будет работать с вашим личным аккаунтом.

### Создание OAuth2 credentials:
1. Перейдите в [Google Cloud Console](https://console.cloud.google.com)
2. Выберите проект или создайте новый
3. Включите Google Sheets API
4. Перейдите в "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Выберите "Desktop application"
6. Скачайте JSON файл

## 🧪 Тестирование подключения

После настройки запустите тест:
```bash
python test_google_sheets.py connection
```

## 📋 Структура таблицы Jarvis

Jarvis автоматически создаст следующие листы:
- **Conversations** - История разговоров
- **Tasks** - Управление задачами  
- **Commands** - Лог системных команд
- **Work_Reports** - Отчеты о работе

## ⚠️ Важные замечания

1. **Service Account** - Хорош для серверных приложений, но использует квоту проекта
2. **OAuth2** - Лучше для личного использования, использует вашу личную квоту
3. **Права доступа** - Service Account нужно явно добавлять в каждую таблицу
4. **Безопасность** - Не делитесь файлом credentials.json

## 🔍 Отладка

Если возникают проблемы:
1. Проверьте права доступа к таблице
2. Убедитесь, что включены нужные API
3. Проверьте квоту в Google Cloud Console
4. Посмотрите логи в папке `logs/`
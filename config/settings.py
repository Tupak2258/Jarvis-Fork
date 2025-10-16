"""
Настройки Jarvis Assistant
"""

import os
from pathlib import Path

# Загружаем переменные окружения из .env файла
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Загружены переменные из {env_file}")
    else:
        print(f"⚠️ Файл .env не найден: {env_file}")
except ImportError:
    print("⚠️ python-dotenv не установлен, переменные .env не загружены")
except Exception as e:
    print(f"⚠️ Ошибка загрузки .env: {e}")

# Базовые пути
BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
CREDENTIALS_DIR = BASE_DIR / "credentials"

# Создаем директории если не существуют
LOGS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
CREDENTIALS_DIR.mkdir(exist_ok=True)

# Настройки логирования
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Настройки ассистента
ASSISTANT_NAME = "Jarvis"
USER_NAME = os.environ.get("USERNAME", "Пользователь")
WAKE_WORD = "джарвис"

# Настройки Ollama
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5vl:7b"  # Можно изменить на другую модель
OLLAMA_TIMEOUT = 30  # Таймаут для запросов к Ollama в секундах

# Настройки TTS (Text-to-Speech)
TTS_RATE = 200  # Скорость речи (150-300)
TTS_VOICE_ID = 0  # Индекс голоса (0 - первый доступный)
TTS_VOLUME = 0.8  # Громкость (0.0-1.0)

# Настройки STT (Speech-to-Text)
STT_TIMEOUT = 10  # Таймаут ожидания команды в секундах
STT_PHRASE_TIMEOUT = 1.0  # Таймаут между фразами
STT_ENERGY_THRESHOLD = 300  # Порог энергии для активации микрофона

# Разрешенные системные команды (для безопасности)
ALLOWED_SYSTEM_COMMANDS = [
    'notepad',
    'calc',
    'explorer',
    'cmd',
    'powershell',
    'mspaint',
    'chrome',
    'firefox',
    'msedge',
    'telegram',
    'discord',
    'spotify',
    'vlc',
    'code',
    'winword',
    'excel',
    'teams'
]

# Настройки Google Sheets (опционально)
GOOGLE_SHEETS_ENABLED = True
GOOGLE_CREDENTIALS_PATH = CREDENTIALS_DIR / "google_credentials.json"
SPREADSHEET_NAME = "Jarvis Assistant Data"  # Название таблицы Google Sheets
GOOGLE_SPREADSHEET_ID = os.environ.get("GOOGLE_SPREADSHEET_ID", "")  # ID таблицы из .env

# Настройки производительности
PERFORMANCE_MONITORING_ENABLED = True
MAX_RESPONSE_TIME_WARNING = 5.0  # Предупреждение если ответ дольше 5 сек
MAX_MEMORY_USAGE_WARNING = 500  # Предупреждение если память больше 500 MB

# Настройки веб-панели
WEB_DASHBOARD_HOST = "127.0.0.1"
WEB_DASHBOARD_PORT = 5000
WEB_DASHBOARD_DEBUG = False

# Настройки автоматизации приложений
APP_AUTOMATION_ENABLED = True
GUI_AUTOMATION_DELAY = 0.5  # Задержка между действиями GUI
TYPING_INTERVAL = 0.02  # Интервал между символами при печати

# Языковые настройки
LANGUAGE = "ru"  # Основной язык
SPEECH_LANGUAGE = "ru-RU"  # Язык для распознавания речи

# Настройки безопасности
SAFE_MODE = True  # Безопасный режим (ограничивает некоторые команды)
MAX_TEXT_LENGTH = 1000  # Максимальная длина вводимого текста
ALLOWED_FILE_EXTENSIONS = ['.txt', '.md', '.py', '.js', '.html', '.css']

# Экспериментальные функции
EXPERIMENTAL_FEATURES = {
    'voice_training': False,
    'context_memory': True,
    'smart_suggestions': False,
    'multi_language': False
}

# Настройки отладки
DEBUG_MODE = False
VERBOSE_LOGGING = False
SAVE_AUDIO_FILES = False  # Сохранять аудио файлы для отладки
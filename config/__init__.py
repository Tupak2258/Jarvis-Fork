"""
Конфигурационный модуль Jarvis Assistant
"""

from .settings import *

__all__ = [
    'LOGS_DIR',
    'LOG_LEVEL', 
    'LOG_FORMAT',
    'ASSISTANT_NAME',
    'USER_NAME',
    'WAKE_WORD',
    'OLLAMA_BASE_URL',
    'OLLAMA_MODEL',
    'OLLAMA_TIMEOUT',
    'TTS_RATE',
    'TTS_VOICE_ID',
    'ALLOWED_SYSTEM_COMMANDS',
    'GOOGLE_CREDENTIALS_PATH',
    'SPREADSHEET_NAME',
    'GOOGLE_SPREADSHEET_ID'
]
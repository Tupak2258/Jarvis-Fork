"""
Модули Jarvis Assistant
"""

from .llm_clients import OllamaClient
from .stt import SpeechRecognizer
from .tts import TextToSpeech
from .sheets_client import GoogleSheetsClient
from .system_tools import SystemTools

# Опциональные модули
try:
    from .app_manager import AppManager
    from .app_commands import AppCommandProcessor
    from .performance_monitor import PerformanceMonitor
    from .config_manager import ConfigManager
    from .web_commands import WebCommandProcessor
    from .sheets_commands import SheetsCommandProcessor
    from .reports_manager import ReportsManager
    
    __all__ = [
        'OllamaClient',
        'SpeechRecognizer', 
        'TextToSpeech',
        'GoogleSheetsClient',
        'SystemTools',
        'AppManager',
        'AppCommandProcessor',
        'PerformanceMonitor',
        'ConfigManager',
        'WebCommandProcessor',
        'SheetsCommandProcessor',
        'ReportsManager'
    ]
except ImportError:
    __all__ = [
        'OllamaClient',
        'SpeechRecognizer', 
        'TextToSpeech',
        'GoogleSheetsClient',
        'SystemTools'
    ]
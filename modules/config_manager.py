"""
Модуль управления конфигурацией
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Класс для управления конфигурацией приложения"""
    
    def __init__(self, config_file: str = "data/user_config.json"):
        self.config_file = Path(config_file)
        self.logger = logging.getLogger(__name__)
        self.config = self._load_default_config()
        self.load_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию по умолчанию"""
        return {
            "tts": {
                "rate": 200,
                "volume": 0.8,
                "voice_id": 0
            },
            "stt": {
                "timeout": 10,
                "phrase_timeout": 1.0,
                "energy_threshold": 300
            },
            "assistant": {
                "wake_word": "джарвис",
                "response_delay": 0.5,
                "auto_save_conversations": True
            },
            "ui": {
                "show_timestamps": True,
                "color_theme": "default",
                "log_level": "INFO"
            }
        }
    
    def load_config(self):
        """Загружает конфигурацию из файла"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                
                # Объединяем с конфигурацией по умолчанию
                self._merge_config(self.config, user_config)
                self.logger.info("Пользовательская конфигурация загружена")
            else:
                self.logger.info("Используется конфигурация по умолчанию")
        except Exception as e:
            self.logger.error(f"Ошибка загрузки конфигурации: {e}")
    
    def save_config(self):
        """Сохраняет текущую конфигурацию в файл"""
        try:
            self.config_file.parent.mkdir(exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            self.logger.info("Конфигурация сохранена")
        except Exception as e:
            self.logger.error(f"Ошибка сохранения конфигурации: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Получает значение конфигурации по ключу
        
        Args:
            key: Ключ в формате "section.parameter"
            default: Значение по умолчанию
        """
        try:
            keys = key.split('.')
            value = self.config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        Устанавливает значение конфигурации
        
        Args:
            key: Ключ в формате "section.parameter"
            value: Новое значение
        """
        try:
            keys = key.split('.')
            config_ref = self.config
            
            # Навигация до предпоследнего уровня
            for k in keys[:-1]:
                if k not in config_ref:
                    config_ref[k] = {}
                config_ref = config_ref[k]
            
            # Установка значения
            config_ref[keys[-1]] = value
            self.logger.info(f"Конфигурация обновлена: {key} = {value}")
        except Exception as e:
            self.logger.error(f"Ошибка установки конфигурации {key}: {e}")
    
    def _merge_config(self, default: Dict, user: Dict):
        """Рекурсивно объединяет пользовательскую конфигурацию с базовой"""
        for key, value in user.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_config(default[key], value)
            else:
                default[key] = value
    
    def reset_to_defaults(self):
        """Сбрасывает конфигурацию к значениям по умолчанию"""
        self.config = self._load_default_config()
        self.save_config()
        self.logger.info("Конфигурация сброшена к значениям по умолчанию")
    
    def export_config(self, filename: str):
        """Экспортирует конфигурацию в файл"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Конфигурация экспортирована в {filename}")
        except Exception as e:
            self.logger.error(f"Ошибка экспорта конфигурации: {e}")
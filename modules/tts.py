"""
Модуль синтеза речи (Text-to-Speech)
"""

import pyttsx3
import logging
import threading
from typing import Optional
from config import TTS_RATE, TTS_VOICE_ID


class TextToSpeech:
    """Класс для синтеза речи"""
    
    def __init__(self):
        self.engine = None
        self.logger = logging.getLogger(__name__)
        self.is_speaking = False
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Инициализация TTS движка"""
        try:
            self.engine = pyttsx3.init()
            
            # Настройка голоса
            voices = self.engine.getProperty('voices')
            if voices and len(voices) > TTS_VOICE_ID:
                self.engine.setProperty('voice', voices[TTS_VOICE_ID].id)
                self.logger.info(f"Установлен голос: {voices[TTS_VOICE_ID].name}")
            
            # Настройка скорости речи
            self.engine.setProperty('rate', TTS_RATE)
            
            # Настройка громкости (0.0 до 1.0)
            self.engine.setProperty('volume', 0.8)
            
            self.logger.info("TTS движок инициализирован")
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации TTS: {e}")
            self.engine = None
    
    def speak(self, text: str, blocking: bool = True):
        """
        Произносит текст
        
        Args:
            text: Текст для произношения
            blocking: Блокировать ли выполнение до завершения речи
        """
        if not self.engine:
            self.logger.error("TTS движок не инициализирован")
            return
        
        if not text or not text.strip():
            return
        
        # Остановка предыдущего произношения если есть
        if self.is_speaking:
            self.stop_speaking()
        
        try:
            self.is_speaking = True
            self.logger.info(f"Произношу: {text[:50]}...")
            
            if blocking:
                self.engine.say(text)
                self.engine.runAndWait()
                self.is_speaking = False
            else:
                # Асинхронное произношение с лучшим управлением потоками
                def speak_async():
                    try:
                        self.engine.say(text)
                        self.engine.runAndWait()
                    except Exception as e:
                        self.logger.error(f"Ошибка в асинхронном произношении: {e}")
                    finally:
                        self.is_speaking = False
                
                thread = threading.Thread(target=speak_async, name="TTS-Thread")
                thread.daemon = True
                thread.start()
                
        except Exception as e:
            self.logger.error(f"Ошибка произношения: {e}")
            self.is_speaking = False
    
    def speak_async(self, text: str):
        """Асинхронное произношение текста"""
        self.speak(text, blocking=False)
    
    def stop_speaking(self):
        """Останавливает текущее произношение"""
        if self.engine and self.is_speaking:
            try:
                self.engine.stop()
                self.is_speaking = False
                self.logger.info("Произношение остановлено")
            except Exception as e:
                self.logger.error(f"Ошибка остановки произношения: {e}")
    
    def is_busy(self) -> bool:
        """Проверяет, произносится ли сейчас речь"""
        return self.is_speaking
    
    def set_rate(self, rate: int):
        """
        Устанавливает скорость речи
        
        Args:
            rate: Скорость (обычно 150-300)
        """
        if self.engine:
            try:
                self.engine.setProperty('rate', rate)
                self.logger.info(f"Скорость речи установлена: {rate}")
            except Exception as e:
                self.logger.error(f"Ошибка установки скорости: {e}")
    
    def set_volume(self, volume: float):
        """
        Устанавливает громкость речи
        
        Args:
            volume: Громкость от 0.0 до 1.0
        """
        if self.engine:
            try:
                volume = max(0.0, min(1.0, volume))  # Ограничиваем диапазон
                self.engine.setProperty('volume', volume)
                self.logger.info(f"Громкость установлена: {volume}")
            except Exception as e:
                self.logger.error(f"Ошибка установки громкости: {e}")
    
    def get_voices(self) -> list:
        """Получает список доступных голосов"""
        if not self.engine:
            return []
        
        try:
            voices = self.engine.getProperty('voices')
            voice_list = []
            
            for i, voice in enumerate(voices):
                voice_info = {
                    'id': voice.id,
                    'name': voice.name,
                    'languages': getattr(voice, 'languages', []),
                    'gender': getattr(voice, 'gender', 'unknown'),
                    'age': getattr(voice, 'age', 'unknown')
                }
                voice_list.append((i, voice_info))
            
            return voice_list
            
        except Exception as e:
            self.logger.error(f"Ошибка получения голосов: {e}")
            return []
    
    def set_voice(self, voice_index: int):
        """
        Устанавливает голос по индексу
        
        Args:
            voice_index: Индекс голоса из списка
        """
        if not self.engine:
            return
        
        try:
            voices = self.engine.getProperty('voices')
            if 0 <= voice_index < len(voices):
                self.engine.setProperty('voice', voices[voice_index].id)
                self.logger.info(f"Голос изменен на: {voices[voice_index].name}")
            else:
                self.logger.error(f"Неверный индекс голоса: {voice_index}")
                
        except Exception as e:
            self.logger.error(f"Ошибка установки голоса: {e}")
    
    def test_speech(self, text: str = "Тестирование синтеза речи"):
        """Тестирует работу синтеза речи"""
        try:
            self.logger.info("Запуск теста TTS...")
            self.speak(text)
            self.logger.info("Тест TTS завершен успешно")
            return True
        except Exception as e:
            self.logger.error(f"Тест TTS провален: {e}")
            return False
    
    def save_to_file(self, text: str, filename: str):
        """
        Сохраняет речь в аудиофайл
        
        Args:
            text: Текст для синтеза
            filename: Имя файла для сохранения
        """
        if not self.engine:
            self.logger.error("TTS движок не инициализирован")
            return
        
        try:
            self.engine.save_to_file(text, filename)
            self.engine.runAndWait()
            self.logger.info(f"Речь сохранена в файл: {filename}")
        except Exception as e:
            self.logger.error(f"Ошибка сохранения в файл: {e}")
    
    def cleanup(self):
        """Очистка ресурсов"""
        if self.engine:
            try:
                self.engine.stop()
                self.logger.info("TTS движок остановлен")
            except:
                pass
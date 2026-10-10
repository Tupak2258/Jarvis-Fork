"""
Модуль синтеза речи (Text-to-Speech).
Работает по принципу "свежий движок на каждую фразу" — только так
pyttsx3 стабильно работает с SAPI5 на Windows.
"""

import pyttsx3
import logging
import re
from config import TTS_RATE, TTS_VOICE_ID


def _clean_for_tts(text: str) -> str:
    """Чистит текст от markdown, эмодзи и мусора перед озвучкой."""
    if not text:
        return ""
    text = re.sub(r"```.*?```", " (код пропущен) ", text, flags=re.S)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"[*_#>]+", "", text)
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    text = re.sub(r"[\U00010000-\U0010ffff]", "", text)  # эмодзи
    text = re.sub(r"<[^>]+>", "", text)                   # xml-теги
    text = re.sub(r"\s+", " ", text).strip()
    return text[:1500]


class TextToSpeech:
    """Простой TTS: свежий движок на каждую фразу."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_speaking = False
        self._last_volume = 0.8
        self._last_rate = TTS_RATE
        self._muted = False
        self.logger.info("TTS готов (режим: свежий движок на фразу)")

    def _make_engine(self):
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        if voices and len(voices) > TTS_VOICE_ID:
            engine.setProperty("voice", voices[TTS_VOICE_ID].id)
        engine.setProperty("rate", self._last_rate)
        engine.setProperty("volume", 0.0 if self._muted else self._last_volume)
        return engine

    def speak(self, text: str, blocking: bool = True):
        """Произносит текст. Параметр blocking игнорируется — всегда синхронно."""
        text = _clean_for_tts(text)
        if not text:
            return

        self.is_speaking = True
        self.logger.info(f"Произношу: {text[:50]}...")
        try:
            engine = self._make_engine()
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            del engine
        except Exception as e:
            self.logger.error(f"Ошибка произношения: {type(e).__name__}: {e}")
        finally:
            self.is_speaking = False

    def speak_async(self, text: str):
        """Совместимость со старым API."""
        self.speak(text)

    def stop_speaking(self):
        self.is_speaking = False

    def is_busy(self) -> bool:
        return self.is_speaking

    def set_rate(self, rate: int):
        self._last_rate = rate
        self.logger.info(f"Скорость речи: {rate}")

    def set_volume(self, volume: float):
        self._last_volume = max(0.0, min(1.0, volume))
        self.logger.info(f"Громкость: {self._last_volume}")

    def get_voices(self) -> list:
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            result = [(i, {
                "id": v.id, "name": v.name,
                "languages": getattr(v, "languages", []),
                "gender": getattr(v, "gender", "unknown"),
            }) for i, v in enumerate(voices)]
            engine.stop()
            return result
        except Exception as e:
            self.logger.error(f"Ошибка получения голосов: {e}")
            return []

    def test_speech(self, text: str = "Тестирование синтеза речи") -> bool:
        try:
            self.speak(text)
            return True
        except Exception as e:
            self.logger.error(f"Тест TTS провален: {e}")
            return False

    def save_to_file(self, text: str, filename: str):
        try:
            engine = pyttsx3.init()
            engine.save_to_file(text, filename)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            self.logger.error(f"Ошибка сохранения: {e}")

    def cleanup(self):
        pass  # нечего чистить — движок живёт только на время фразы

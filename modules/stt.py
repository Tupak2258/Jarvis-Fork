# stt.py (Финальная версия с принудительным преобразованием аудио)

import logging
import speech_recognition as sr
import numpy as np
import torch
import torchaudio
from faster_whisper import WhisperModel
from config import WAKE_WORD

class SpeechRecognizer:
    """Класс для распознавания речи с использованием Whisper."""
    
    def __init__(self):
        self.model_size = "large-v3"
        self.logger = logging.getLogger(__name__)

        # Определяем, есть ли GPU
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compute_type = "float16" if self.device == "cuda" else "int8"

        try:
            self.model = WhisperModel(
                self.model_size, 
                device=self.device, 
                compute_type=self.compute_type
            )
            self.logger.info(f"Модель Whisper '{self.model_size}' загружена на {self.device.upper()}.")
        except Exception as e:
            self.logger.error(f"Не удалось загрузить модель Whisper: {e}")
            raise

        # --- КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: ЗАДАЕМ ЧАСТОТУ ДИСКРЕТИЗАЦИИ ---
        # Мы явно указываем желаемую частоту, чтобы избежать несоответствий.
        self.sample_rate = 16000
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone(sample_rate=self.sample_rate)
        # --------------------------------------------------------
        
        self.logger.info("Калибровка микрофона (2 сек)...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        self.logger.info("Калибровка завершена.")

    def _process_audio(self, audio_data: sr.AudioData) -> str:
        """Преобразует аудиоданные в нужный формат и распознает текст."""
        # Получаем сырые данные
        raw_data = audio_data.get_raw_data()
        
        # Конвертируем в тензор PyTorch
        audio_tensor = torch.from_numpy(
            np.frombuffer(raw_data, dtype=np.int16).copy()
        ).float() / 32768.0
        
        # --- ПРИНУДИТЕЛЬНОЕ ПРЕОБРАЗОВАНИЕ В 16000 ГЦ ---
        # Проверяем, соответствует ли частота микрофона целевой
        source_sample_rate = audio_data.sample_rate
        if source_sample_rate != self.sample_rate:
            self.logger.warning(f"Обнаружено несоответствие частоты: {source_sample_rate}Hz. Преобразую в {self.sample_rate}Hz.")
            resampler = torchaudio.transforms.Resample(orig_freq=source_sample_rate, new_freq=self.sample_rate)
            audio_tensor = resampler(audio_tensor)
        # --------------------------------------------------

        # Распознаем русскую речь
        segments, info = self.model.transcribe(
            audio_tensor.numpy(), # faster-whisper ожидает NumPy массив
            beam_size=5, 
            vad_filter=True, 
            language="ru"
        )
        
        text = "".join(segment.text for segment in segments).strip()
        return text

    def listen_for_wake_word(self) -> bool:
        """Прослушивает слово активации."""
        try:
            with self.microphone as source:
                # Используем более короткий таймаут для активации
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=4)
            
            text = self._process_audio(audio)
            
            if text:
                self.logger.info(f"Распознано (для активации): \"{text}\"")
                # Упрощаем проверку для надежности
                clean_text = ''.join(filter(str.isalnum, text.lower()))
                clean_wake_word = ''.join(filter(str.isalnum, WAKE_WORD.lower()))
                if clean_wake_word in clean_text:
                    self.logger.info("Кодовое слово обнаружено.")
                    return True
        except sr.WaitTimeoutError:
            return False # Это нормально, просто ничего не было сказано
        except Exception as e:
            self.logger.error(f"Ошибка в цикле прослушивания: {e}")
            
        return False

    # ... (остальные методы listen_for_command и test_microphone остаются без изменений, как в предпоследнем ответе)
    def listen_for_command(self, timeout: int = 10) -> str | None:
        """Прослушивает команду после активации."""
        try:
            with self.microphone as source:
                self.logger.info("Слушаю команду...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            text = self._process_audio(audio)
            
            if text:
                self.logger.info(f"Команда распознана: {text}")
                return text
            else:
                self.logger.warning("Не удалось распознать команду (пустой текст).")
                return None
                
        except sr.WaitTimeoutError:
            self.logger.info("Таймаут ожидания команды.")
            return None
        except Exception as e:
            self.logger.error(f"Ошибка при распознавании команды: {e}")
            return None
    
    def test_microphone(self) -> bool:
        """Тестирует работу микрофона."""
        try:
            with self.microphone as source:
                self.recognizer.listen(source, timeout=1, phrase_time_limit=1)
            return True
        except Exception:
            return False
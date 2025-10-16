# check_mic.py
from modules.stt import SpeechRecognizer

def list_mics():
    """Функция для вывода списка доступных микрофонов."""
    recognizer = SpeechRecognizer()
    mic_list = recognizer.get_microphone_list()
    
    if not mic_list:
        print("Не найдено ни одного микрофона.")
        return

    print("Найдены следующие микрофоны:")
    for index, name in enumerate(mic_list):
        print(f"  Индекс: {index}, Имя: {name}")

if __name__ == "__main__":
    list_mics()
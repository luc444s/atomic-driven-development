import speech_recognition as sr
from pydub import AudioSegment

# Ruta del archivo de audio
audio_path = "bOGDAN TIPO DE DOC NIF CIF.m4a"

# Convertir a WAV
sound = AudioSegment.from_file(audio_path, format="m4a")
wav_path = "temp.wav"
sound.export(wav_path, format="wav")

# Reconocimiento de voz
r = sr.Recognizer()
with sr.AudioFile(wav_path) as source:
    audio_data = r.record(source)

try:
    texto = r.recognize_google(audio_data, language="es-ES")
    print("\n--- TRANSCRIPCIÓN ---\n")
    print(texto)
except Exception as e:
    print(f"Error: {e}")

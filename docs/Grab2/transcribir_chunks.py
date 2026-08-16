import math

import speech_recognition as sr
from pydub import AudioSegment

AUDIO_INPUT = "bOGDAN TIPO DE DOC NIF CIF.m4a"
WAV_OUTPUT = "temp_full.wav"
CHUNK_SECONDS = 50  # trozos de ~50s para evitar límites

print("Convirtiendo M4A a WAV...")
audio = AudioSegment.from_file(AUDIO_INPUT, format="m4a")
audio.export(WAV_OUTPUT, format="wav")

r = sr.Recognizer()

def transcribir_trozo(wav_path, start_ms, end_ms, idx):
    segment = AudioSegment.from_wav(wav_path)[start_ms:end_ms]
    tmp_name = f"chunk_{idx}.wav"
    segment.export(tmp_name, format="wav")
    with sr.AudioFile(tmp_name) as source:
        audio_data = r.record(source)
    try:
        # Cambia a "es-PE" si prefieres español Perú
        text = r.recognize_google(audio_data, language="es-ES")
    except Exception as e:
        text = f"[Error en chunk {idx}: {e}]"
    return text

dur_ms = len(AudioSegment.from_wav(WAV_OUTPUT))
total_chunks = math.ceil(dur_ms / (CHUNK_SECONDS * 1000))

print(f"Duración total: {dur_ms/1000:.1f}s | Chunks: {total_chunks}")

salida = []
for i in range(total_chunks):
    start_ms = i * CHUNK_SECONDS * 1000
    end_ms = min((i + 1) * CHUNK_SECONDS * 1000, dur_ms)
    mm = (start_ms // 1000) // 60
    ss = (start_ms // 1000) % 60
    marca = f"[{mm:02d}:{ss:02d}]"
    print(f"Transcribiendo {marca} ({i+1}/{total_chunks})...")
    texto = transcribir_trozo(WAV_OUTPUT, start_ms, end_ms, i+1)
    salida.append(f"{marca} {texto}")

print("\n--- TRANSCRIPCIÓN (con timestamps) ---\n")
print("\n".join(salida))

# Guarda también en archivo de texto
with open("transcripcion.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(salida))

print('\nListo. Guardado en "transcripcion.txt".')

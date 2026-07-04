import os
import math
import speech_recognition as sr
from pydub import AudioSegment

# Buscar el primer archivo .m4a en la carpeta actual
audios_m4a = [f for f in os.listdir() if f.lower().endswith(".m4a")]
if not audios_m4a:
    print("No se encontró ningún archivo .m4a en esta carpeta.")
    exit()

AUDIO_INPUT = audios_m4a[0]
print(f"🎤 Usando archivo: {AUDIO_INPUT}")

# Configuración
WAV_OUTPUT = "temp_full.wav"
CHUNK_SECONDS = 50  # trozos de 50 segundos para evitar cortes

# Convertir a WAV
print("⏳ Convirtiendo M4A a WAV...")
audio = AudioSegment.from_file(AUDIO_INPUT, format="m4a")
audio.export(WAV_OUTPUT, format="wav")

# Inicializar reconocedor
r = sr.Recognizer()

def transcribir_trozo(wav_path, start_ms, end_ms, idx):
    segment = AudioSegment.from_wav(wav_path)[start_ms:end_ms]
    tmp_name = f"chunk_{idx}.wav"
    segment.export(tmp_name, format="wav")
    with sr.AudioFile(tmp_name) as source:
        audio_data = r.record(source)
    try:
        text = r.recognize_google(audio_data, language="es-ES")  # Cambiar a "es-PE" si prefieres acento Perú
    except Exception as e:
        text = f"[Error en chunk {idx}: {e}]"
    os.remove(tmp_name)  # borrar archivo temporal
    return text

# Procesar por chunks
dur_ms = len(AudioSegment.from_wav(WAV_OUTPUT))
total_chunks = math.ceil(dur_ms / (CHUNK_SECONDS * 1000))
print(f"📏 Duración: {dur_ms/1000:.1f} segundos | Chunks: {total_chunks}")

salida = []
for i in range(total_chunks):
    start_ms = i * CHUNK_SECONDS * 1000
    end_ms = min((i + 1) * CHUNK_SECONDS * 1000, dur_ms)
    mm = (start_ms // 1000) // 60
    ss = (start_ms // 1000) % 60
    marca = f"[{mm:02d}:{ss:02d}]"
    print(f"🔍 Transcribiendo {marca} ({i+1}/{total_chunks})...")
    texto = transcribir_trozo(WAV_OUTPUT, start_ms, end_ms, i+1)
    salida.append(f"{marca} {texto}")

# Guardar transcripción
nombre_txt = os.path.splitext(AUDIO_INPUT)[0] + "_transcripcion.txt"
with open(nombre_txt, "w", encoding="utf-8") as f:
    f.write("\n".join(salida))

print("\n✅ Transcripción completada.")
print(f"📝 Guardada en: {nombre_txt}")
print("\n--- TRANSCRIPCIÓN ---\n")
print("\n".join(salida))

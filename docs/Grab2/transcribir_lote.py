import sys
sys.path.insert(0, r"D:\Lib\site-packages")
import sys
sys.path.append(r"D:\Lib\site-packages")


import os, math
import traceback
import speech_recognition as sr
from pydub import AudioSegment

IDIOMA = "es-PE"      # Cambia a "es-ES" si prefieres
CHUNK_SECONDS = 50     # Trozos de 50s para evitar cortes del servicio

def transcribir_archivo(m4a_file):
    base = os.path.splitext(m4a_file)[0]
    wav_tmp = base + "_temp_full.wav"
    out_txt = base + "_transcripcion.txt"

    print(f"\n🎤 Procesando: {m4a_file}")
    try:
        # Convertir a WAV
        print("⏳ Convirtiendo a WAV...")
        audio = AudioSegment.from_file(m4a_file, format="m4a")
        audio.export(wav_tmp, format="wav")

        # Preparar para trocear
        dur_ms = len(AudioSegment.from_wav(wav_tmp))
        total_chunks = math.ceil(dur_ms / (CHUNK_SECONDS * 1000))
        print(f"📏 Duración: {dur_ms/1000:.1f}s | Chunks: {total_chunks}")

        r = sr.Recognizer()
        salida = []
        for i in range(total_chunks):
            start_ms = i * CHUNK_SECONDS * 1000
            end_ms = min((i + 1) * CHUNK_SECONDS * 1000, dur_ms)
            mm = (start_ms // 1000) // 60
            ss = (start_ms // 1000) % 60
            marca = f"[{mm:02d}:{ss:02d}]"

            # Crear chunk temporal
            chunk_wav = f"{base}_chunk_{i+1}.wav"
            segment = AudioSegment.from_wav(wav_tmp)[start_ms:end_ms]
            segment.export(chunk_wav, format="wav")

            print(f"🔍 Transcribiendo {marca} ({i+1}/{total_chunks})...")
            try:
                with sr.AudioFile(chunk_wav) as source:
                    audio_data = r.record(source)
                texto = r.recognize_google(audio_data, language=IDIOMA)
            except Exception as e:
                texto = f"[Error en chunk {i+1}: {e}]"
            finally:
                try:
                    os.remove(chunk_wav)
                except:
                    pass

            salida.append(f"{marca} {texto}")

        # Guardar salida
        with open(out_txt, "w", encoding="utf-8") as f:
            f.write("\n".join(salida))

        print(f"✅ Listo: {out_txt}")
    except Exception as e:
        print(f"❌ Error con {m4a_file}: {e}")
        traceback.print_exc()
    finally:
        try:
            if os.path.exists(wav_tmp):
                os.remove(wav_tmp)
        except:
            pass

def main():
    files = [f for f in os.listdir() if f.lower().endswith(".m4a")]
    if not files:
        print("No se encontraron archivos .m4a en esta carpeta.")
        return
    print(f"Se encontraron {len(files)} archivo(s) .m4a.")
    for f in files:
        transcribir_archivo(f)

if __name__ == "__main__":
    main()

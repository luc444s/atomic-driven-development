import sys

print("PYTHON:", sys.executable)
print("VERSION:", sys.version)
print("PATHS:")
for p in sys.path:
    print(" -", p)

try:
    import speech_recognition as sr
    print("SR_OK:", sr.__file__)
except Exception as e:
    print("SR_ERR:", repr(e))

try:
    import pydub
    print("PYDUB_OK:", pydub.__file__)
except Exception as e:
    print("PYDUB_ERR:", repr(e))

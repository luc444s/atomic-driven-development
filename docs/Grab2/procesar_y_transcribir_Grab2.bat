@echo off
setlocal ENABLEDELAYEDEXPANSION
title Procesar y Transcribir Grab2 - Fix + Lote
color 1F

REM === CONFIG ===
set "DIR=D:\DISCO D\NO TOCAR\Clientes\2025\Proberton 2.0\grabaciones\Grab2"
set "PYTHON=D:\python.exe"
set "PY_SCRIPT_ABS=D:\Proyectos\Proberton2025\transcribir_lote.py"
set "FFMPEG=D:\ffmpeg\bin\ffmpeg.exe"
if not exist "%FFMPEG%" set "FFMPEG=ffmpeg"

echo [STEP] Cambiando a carpeta...
cd /d "%DIR%" || (echo [ERROR] No pude entrar a "%DIR%" & pause & exit /b 1)
echo [OK] Carpeta actual: %CD%

echo.
echo [LIST] .m4a detectados:
dir /b /a:-d *.m4a *.M4A 2>nul || echo (ninguno encontrado)

echo.
echo [CHECK] FFmpeg...
"%FFMPEG%" -version >nul 2>&1 || (echo [ERROR] FFmpeg no disponible. Ajusta ruta o PATH. & pause & exit /b 1)
echo [OK] FFmpeg OK.

echo.
echo [A] Reparando m4a -> *_fix.m4a
set "NEWFOUND=0"
for %%F in (*.m4a *.M4A) do (
  echo "%%~nF" | find /I "_fix" >nul && (echo  - Saltando "%%F" (ya es FIX)) && (goto :cont)
  if exist "%%~nF_fix.m4a" (echo  - Saltando "%%F" (ya existe FIX) & goto :cont)

  echo  >>> Reparando: "%%F"
  "%FFMPEG%" -hide_banner -loglevel error -y -i "%%F" -c copy "%%~nF_fix.m4a"
  if errorlevel 1 (
    del /q "%%~nF_fix.m4a" >nul 2>&1
    echo     - Re-encode AAC...
    "%FFMPEG%" -hide_banner -loglevel error -y -err_detect ignore_err -i "%%F" -vn -acodec aac -b:a 192k "%%~nF_fix.m4a"
    if errorlevel 1 (
      del /q "%%~nF_fix.m4a" >nul 2>&1
      echo     - VIA WAV temporal...
      "%FFMPEG%" -hide_banner -loglevel error -y -err_detect ignore_err -i "%%F" -acodec pcm_s16le -ar 44100 "%%~nF_temp.wav"
      if not errorlevel 1 (
        "%FFMPEG%" -hide_banner -loglevel error -y -i "%%~nF_temp.wav" -acodec aac -b:a 192k "%%~nF_fix.m4a"
        del /q "%%~nF_temp.wav" >nul 2>&1
      )
    )
  )
  if exist "%%~nF_fix.m4a" (echo     [OK] "%%~nF_fix.m4a" & set "NEWFOUND=1") else (echo     [ERROR] No se pudo reparar "%%F")
  :cont
)

echo.
echo [B] Ordenando originales -> .\originales
if not exist "originales" mkdir "originales" >nul 2>&1
for %%F in (*.m4a *.M4A) do (
  echo "%%~nF" | find /I "_fix" >nul
  if errorlevel 1 if exist "%%~nF_fix.m4a" (
    move /Y "%%F" "originales\" >nul
    echo  - Movido "%%F" -> originales\
  )
)

echo.
echo [C] Transcribir en lote
set "PY_SCRIPT=%PY_SCRIPT_ABS%"
if not exist "%PY_SCRIPT%" if exist "transcribir_lote.py" set "PY_SCRIPT=%CD%\transcribir_lote.py"
if not exist "%PY_SCRIPT%" (echo [ERROR] No encuentro transcribir_lote.py & pause & exit /b 1)

echo [RUN] "%PYTHON%" "%PY_SCRIPT%"
"%PYTHON%" "%PY_SCRIPT%"
echo [SALIDA PYTHON] Codigo: %ERRORLEVEL%

echo.
echo === FIN ===
echo - Revisa *_transcripcion.txt (y *_resumen.txt si tu script lo genera)
pause
endlocal

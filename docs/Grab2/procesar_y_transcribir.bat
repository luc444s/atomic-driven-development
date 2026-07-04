@echo off
setlocal ENABLEDELAYEDEXPANSION
title Procesar y Transcribir (.m4a) - Fix + Lote

REM ========== CONFIGURACION ==========
REM Carpeta por defecto (Modo auto)
set "DIR_DEF=D:\DISCO D\NO TOCAR\Clientes\2025\Proberton 2.0\grabaciones\Grab2"

REM Python y Script
set "PYTHON=D:\python.exe"
set "PY_SCRIPT_ABS=D:\Proyectos\Proberton2025\transcribir_lote.py"

REM FFmpeg: ruta absoluta recomendada; si no existe, usa el del PATH
set "FFMPEG=D:\ffmpeg\bin\ffmpeg.exe"
if not exist "%FFMPEG%" set "FFMPEG=ffmpeg"

REM Tamaño letra y colores
color 1F

echo.
echo ===========================================
echo   Procesar y Transcribir Audios (.m4a)
echo   - Repara archivos (crea *_fix.m4a)
echo   - Mueve originales a .\originales
echo   - Transcribe en lote con Python
echo ===========================================
echo.

REM -------- ELEGIR MODO --------
echo [1] Usar carpeta por defecto:
echo     "%DIR_DEF%"
echo [2] Elegir carpeta manualmente (puedes arrastrarla aqui)
echo.
set "CHOICE="
set /p CHOICE=Elige 1 o 2 y presiona Enter: 

if "%CHOICE%"=="2" (
  echo.
  set "DIR="
  set /p DIR=Arrastra aqui la carpeta con .m4a (o pega la ruta) y presiona Enter: 
  if "%DIR%"=="" (
     echo [ERROR] No se proporciono carpeta. Saliendo...
     pause
     exit /b 1
  )
) else (
  set "DIR=%DIR_DEF%"
)

echo.
echo [INFO] Carpeta de trabajo: "%DIR%"
if not exist "%DIR%" (
  echo [ERROR] La carpeta no existe.
  pause
  exit /b 1
)

REM -------- IR A LA CARPETA --------
cd /d "%DIR%" || (echo [ERROR] No pude ir a %DIR% & pause & exit /b 1)

REM -------- VERIFICAR PYTHON --------
echo.
echo [CHECK] Verificando Python: "%PYTHON%"
if not exist "%PYTHON%" (
  echo [ERROR] No encontre "%PYTHON%".
  echo Edita el .BAT y corrige la variable PYTHON.
  pause
  exit /b 1
)

REM -------- VERIFICAR FFMPEG --------
echo [CHECK] Verificando FFmpeg: "%FFMPEG%"
"%FFMPEG%" -version >nul 2>&1
if errorlevel 1 (
  echo [ADVERTENCIA] No pude ejecutar FFmpeg desde "%FFMPEG%".
  echo Intentare usar "ffmpeg" del PATH del sistema...
  set "FFMPEG=ffmpeg"
  "%FFMPEG%" -version >nul 2>&1
  if errorlevel 1 (
    echo [ERROR] FFmpeg no esta disponible. Instala/ajusta ruta (D:\ffmpeg\bin\ffmpeg.exe) o agrega al PATH.
    pause
    exit /b 1
  )
)
echo [OK] FFmpeg disponible.

REM -------- REPARAR M4A (crear *_fix.m4a) --------
echo.
echo ===========================================
echo   A) Reparando M4A (crear *_fix.m4a)
echo ===========================================
set "NEWFOUND=0"

for %%F in (*.m4a) do (
  REM saltar si el nombre ya contiene _fix
  echo "%%~nF" | find /I "_fix" >nul && (
    echo - Saltando "%%F" (ya es *_fix.m4a)
  ) || (
    REM saltar si ya existe su *_fix
    if exist "%%~nF_fix.m4a" (
      echo - Saltando "%%F" (ya existe %%~nF_fix.m4a)
    ) else (
      echo.
      echo >>> Reparando: "%%F"
      REM 1) Remux sin recodificar
      "%FFMPEG%" -hide_banner -loglevel error -y -i "%%F" -c copy "%%~nF_fix.m4a"
      if errorlevel 1 (
        echo   - Remux fallo. Probando re-encode AAC...
        del /q "%%~nF_fix.m4a" >nul 2>&1

        REM 2) Re-encode a AAC (tolerante)
        "%FFMPEG%" -hide_banner -loglevel error -y -err_detect ignore_err -i "%%F" -vn -acodec aac -b:a 192k "%%~nF_fix.m4a"
        if errorlevel 1 (
          echo   - Re-encode directo fallo. Probando via WAV temporal...
          del /q "%%~nF_fix.m4a" >nul 2>&1

          REM 3) Plan C: WAV temporal -> AAC
          "%FFMPEG%" -hide_banner -loglevel error -y -err_detect ignore_err -i "%%F" -acodec pcm_s16le -ar 44100 "%%~nF_temp.wav"
          if not errorlevel 1 (
            "%FFMPEG%" -hide_banner -loglevel error -y -i "%%~nF_temp.wav" -acodec aac -b:a 192k "%%~nF_fix.m4a"
            del /q "%%~nF_temp.wav" >nul 2>&1
          )
        )
      )

      if exist "%%~nF_fix.m4a" (
        echo   [OK] Generado: "%%~nF_fix.m4a"
        set "NEWFOUND=1"
      ) else (
        echo   [ERROR] No se pudo reparar "%%F". Archivo probablemente irrecuperable.
      )
    )
  )
)

REM -------- ORDENAR ORIGINALES --------
echo.
echo ===========================================
echo   B) Ordenando originales -> .\originales
echo ===========================================
if not exist "originales" mkdir "originales" >nul 2>&1

for %%F in (*.m4a) do (
  echo "%%~nF" | find /I "_fix" >nul && (REM es FIX, no mover) || (
    if exist "%%~nF_fix.m4a" (
      move /Y "%%F" "originales\" >nul
      echo - Movido "%%F" -> originales\
    )
  )
)

REM -------- VERIFICAR SCRIPT PYTHON --------
echo.
echo ===========================================
echo   C) Transcribir en lote con Python
echo ===========================================
set "PY_SCRIPT=%PY_SCRIPT_ABS%"
if not exist "%PY_SCRIPT%" (
  echo [WARN] No encontre "%PY_SCRIPT_ABS%".
  if exist "transcribir_lote.py" (
    set "PY_SCRIPT=%CD%\transcribir_lote.py"
    echo [OK] Usare el script local: "%PY_SCRIPT%"
  ) else (
    echo [ERROR] No hay script transcribir_lote.py ni en "%PY_SCRIPT_ABS%" ni en "%CD%".
    echo Edita el .BAT y corrige PY_SCRIPT_ABS o copia el script aqui.
    pause
    exit /b 1
  )
)

REM -------- TRANSCRIBIR --------
if "%NEWFOUND%"=="1" (
  echo [INFO] Se generaron nuevos *_fix.m4a. Iniciando transcripcion...
) else (
  echo [INFO] No se detectaron nuevos *_fix.m4a. Transcribire todo lo que encuentre.
)

echo.
"%PYTHON%" "%PY_SCRIPT%"
set "EC=%ERRORLEVEL%"
echo.
if NOT "%EC%"=="0" (
  echo [ADVERTENCIA] Python salio con codigo %EC%. Revisa mensajes arriba.
) else (
  echo [OK] Transcripcion finalizada.
)

echo.
echo Archivos generados: *_transcripcion.txt (y, si tu script lo hace, *_resumen.txt)
echo.
echo === FIN ===
pause
endlocal

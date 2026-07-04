@echo off
setlocal ENABLEDELAYEDEXPANSION
title Procesar y Transcribir (.m4a) - Fix + Lote (v2 verbose)
color 1F

REM === CONFIGURACION ===
set "DIR_DEF=D:\DISCO D\NO TOCAR\Clientes\2025\Proberton 2.0\grabaciones\Grab2"
set "PYTHON=D:\python.exe"
set "PY_SCRIPT_ABS=D:\Proyectos\Proberton2025\transcribir_lote.py"
set "FFMPEG=D:\ffmpeg\bin\ffmpeg.exe"
if not exist "%FFMPEG%" set "FFMPEG=ffmpeg"

echo.
echo ====== MODO ======
echo [1] Usar carpeta por defecto:
echo     "%DIR_DEF%"
echo [2] Elegir carpeta manualmente (puedes arrastrarla aqui)
set /p CHOICE=Elige 1 o 2 y Enter: 

if "%CHOICE%"=="2" (
  set "DIR="
  set /p DIR=Arrastra/pega ruta de carpeta con .m4a y Enter: 
  if "%DIR%"=="" (echo [ERROR] No se proporciono carpeta.& pause & exit /b 1)
) else (
  set "DIR=%DIR_DEF%"
)

echo.
echo [INFO] Carpeta de trabajo esperada:
echo "%DIR%"
if not exist "%DIR%" (echo [ERROR] La carpeta no existe.& pause & exit /b 1)

echo.
echo [STEP] Cambiando a carpeta...
cd /d "%DIR%" || (echo [ERROR] No pude entrar a "%DIR%".& pause & exit /b 1)
echo [OK] Carpeta actual: %CD%

echo.
echo [CHECK] Python: "%PYTHON%"
if not exist "%PYTHON%" (echo [ERROR] No encontre "%PYTHON%". Edita el BAT.& pause & exit /b 1)
"%PYTHON%" --version

echo.
echo [CHECK] FFmpeg: "%FFMPEG%"
"%FFMPEG%" -version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] FFmpeg no disponible. Ajusta la ruta o PATH.
  pause
  exit /b 1
) else (
  for /f "tokens=1,2*" %%a in ('%FFMPEG% -version 2^>nul ^| findstr /i /c:"ffmpeg version"') do echo [OK] %%a %%b %%c
)

echo.
echo [LIST] Buscando .m4a en %CD%
dir /b /a:-d *.m4a *.M4A 2>nul || echo (ninguno listado)
set "NEWFOUND=0"
set "COUNT=0"

for %%F in (*.m4a *.M4A) do (
  set /a COUNT+=1
  echo.
  echo --- Archivo %%F ---
  echo "%%~nF" | find /I "_fix" >nul
  if not errorlevel 1 (
    echo   [SKIP] Ya es *_fix.m4a, no reparo.
    goto :continueLoop
  )

  if exist "%%~nF_fix.m4a" (
    echo   [SKIP] Ya existe "%%~nF_fix.m4a"
    goto :continueLoop
  )

  echo   [TRY1] Remux sin recodificar...
  "%FFMPEG%" -hide_banner -loglevel error -y -i "%%F" -c copy "%%~nF_fix.m4a"
  if errorlevel 1 (
    echo   [TRY2] Re-encode AAC tolerante...
    del /q "%%~nF_fix.m4a" >nul 2>&1
    "%FFMPEG%" -hide_banner -loglevel error -y -err_detect ignore_err -i "%%F" -vn -acodec aac -b:a 192k "%%~nF_fix.m4a"
    if errorlevel 1 (
      echo   [TRY3] WAV temporal -> AAC...
      del /q "%%~nF_fix.m4a" >nul 2>&1
      "%FFMPEG%" -hide_banner -loglevel error -y -err_detect ignore_err -i "%%F" -acodec pcm_s16le -ar 44100 "%%~nF_temp.wav"
      if errorlevel 1 (
        echo   [FAIL] No pude decodificar "%%F". Prob. corrupto.
      ) else (
        "%FFMPEG%" -hide_banner -loglevel error -y -i "%%~nF_temp.wav" -acodec aac -b:a 192k "%%~nF_fix.m4a"
        del /q "%%~nF_temp.wav" >nul 2>&1
      )
    )
  )

  if exist "%%~nF_fix.m4a" (
    echo   [OK] Generado "%%~nF_fix.m4a"
    set "NEWFOUND=1"
  ) else (
    echo   [ERROR] No se pudo reparar "%%F"
  )

  :continueLoop
)

echo.
echo [INFO] Total iterado: %COUNT% archivo(s).
if "%COUNT%"=="0" (
  echo [NOTA] No hay .m4a en esta carpeta. Nada que reparar ni transcribir.
  goto :endSection
)

echo.
echo [STEP] Ordenando originales -> .\originales
if not exist "originales" mkdir "originales" >nul 2>&1
for %%F in (*.m4a *.M4A) do (
  echo "%%~nF" | find /I "_fix" >nul
  if errorlevel 1 (
    if exist "%%~nF_fix.m4a" (
      move /Y "%%F" "originales\" >nul && echo - Movido "%%F" -> originales\
    )
  )
)

:endSection

echo.
echo [TRANSCRIBIR] Buscando script...
set "PY_SCRIPT=%PY_SCRIPT_ABS%"
if not exist "%PY_SCRIPT%" (
  if exist "transcribir_lote.py" (
    set "PY_SCRIPT=%CD%\transcribir_lote.py"
    echo [OK] Usare script local: "%PY_SCRIPT%"
  ) else (
    echo [ERROR] No hay transcribir_lote.py ni en "%PY_SCRIPT_ABS%" ni en "%CD%".
    pause
    exit /b 1
  )
)

echo.
echo [RUN] "%PYTHON%" "%PY_SCRIPT%"
"%PYTHON%" "%PY_SCRIPT%"
echo [SALIDA PYTHON] Codigo: %ERRORLEVEL%

echo.
echo === FIN ===
echo Si no viste nada, revisa:
echo - Que haya .m4a en la carpeta (no subcarpetas).
echo - Que se muestren en la seccion [LIST].
echo - Que exista transcribir_lote.py (abs. o local).
pause
endlocal


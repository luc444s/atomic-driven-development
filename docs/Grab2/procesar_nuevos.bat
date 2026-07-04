@echo off
setlocal ENABLEDELAYEDEXPANSION

REM === CONFIGURA TUS RUTAS ===
set "DIR=D:\DISCO D\NO TOCAR\Clientes\2025\Proberton 2.0\grabaciones\Grab2"
set "PYTHON=D:\python.exe"
set "PY_SCRIPT=D:\Proyectos\Proberton2025\transcribir_lote.py"
set "FFMPEG=D:\ffmpeg\bin\ffmpeg.exe"

cd /d "%DIR%" || (echo [ERROR] No pude ir a %DIR% & pause & exit /b 1)

echo === Buscando NUEVOS .m4a (sin *_fix.m4a) ===
set "NEWFOUND=0"

for %%F in (*.m4a) do (
    if not exist "%%~nF_fix.m4a" (
        echo.
        echo >>> Procesando: "%%F"

        REM 1) Intento rapido: remux (copia sin recodificar)
        "%FFMPEG%" -hide_banner -loglevel error -y -i "%%F" -c copy "%%~nF_fix.m4a"
        if errorlevel 1 (
            echo   - Remux fallo. Probando re-encode AAC (tolerante)...
            del /q "%%~nF_fix.m4a" >nul 2>&1

            REM 2) Re-encode directo a AAC
            "%FFMPEG%" -hide_banner -loglevel error -y -err_detect ignore_err -i "%%F" -vn -acodec aac -b:a 192k "%%~nF_fix.m4a"
            if errorlevel

@echo off
if defined CLAUDE_PLUGIN_DATA (
    set "VENV=%CLAUDE_PLUGIN_DATA%\venv"
) else (
    set "VENV=%USERPROFILE%\.claude\plugins\data\mllog\venv"
)
set "MLLOG=%VENV%\Scripts\mllog.exe"
if not exist "%MLLOG%" (
    echo mllog not installed yet — restart session to trigger bootstrap. 1>&2
    exit /b 1
)
"%MLLOG%" %*

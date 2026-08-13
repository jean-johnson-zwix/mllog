@echo off
if defined CLAUDE_PLUGIN_DATA (
    set "VENV=%CLAUDE_PLUGIN_DATA%\venv"
) else (
    set "VENV=%USERPROFILE%\.claude\plugins\data\mllog\venv"
)
set "PYEXE=%VENV%\Scripts\python.exe"
if not exist "%PYEXE%" (
    echo mllog venv not set up — restart session to trigger bootstrap. 1>&2
    exit /b 1
)
"%PYEXE%" %*

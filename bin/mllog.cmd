@echo off
if defined CLAUDE_PLUGIN_DATA (
    set "VENV=%CLAUDE_PLUGIN_DATA%\venv"
) else (
    rem ponytail: scan for data dir — name includes marketplace name, which varies
    for /d %%D in ("%USERPROFILE%\.claude\plugins\data\mllog-*") do set "VENV=%%D\venv"
)
set "MLLOG=%VENV%\Scripts\mllog.exe"
if not exist "%MLLOG%" (
    echo mllog not installed yet — restart session to trigger bootstrap. 1>&2
    exit /b 1
)
"%MLLOG%" %*

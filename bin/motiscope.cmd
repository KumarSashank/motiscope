@echo off
rem motiscope launcher for Windows. Put this directory on your PATH.
setlocal
set "MOTISCOPE_BIN=%~dp0"
python "%MOTISCOPE_BIN%..\scripts\cli.py" %*
endlocal

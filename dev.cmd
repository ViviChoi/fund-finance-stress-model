@echo off
REM Windows convenience wrapper for dev.py.
REM Usage:  dev.cmd setup   |   dev.cmd all   |   dev.cmd test   ...
python "%~dp0dev.py" %*

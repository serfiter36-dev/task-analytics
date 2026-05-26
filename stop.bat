@echo off
echo Остановка Task Analytics...
taskkill /FI "WINDOWTITLE eq Backend*" /F > nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend*" /F > nul 2>&1
echo Готово! Серверы остановлены.

@echo off
echo Запуск Task Analytics...

:: Запуск бэкенда в свёрнутом окне
start /min "Backend" cmd /k "cd /d C:\GitHub\projects\task-analytics\backend && venv\Scripts\activate.bat && set PYTHONUNBUFFERED=1 && python -m uvicorn main:app --reload"

:: Ждём 3 секунды пока бэкенд запустится
timeout /t 3 /nobreak > nul

:: Запуск фронтенда в свёрнутом окне
start /min "Frontend" cmd /k "cd /d C:\GitHub\projects\task-analytics\frontend && py -m http.server 3000"

:: Ждём ещё 2 секунды
timeout /t 2 /nobreak > nul

:: Открываем браузер
start http://localhost:3000

echo Готово! Приложение открыто в браузере.
echo Для остановки закройте свёрнутые окна Backend и Frontend в панели задач.

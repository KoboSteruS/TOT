@echo off
echo ============================================
echo      OOO "TOT" - Админ-панель
echo ============================================
echo.

REM Проверка виртуального окружения
if not exist "venv\" (
    echo Создаю виртуальное окружение...
    python -m venv venv
)

REM Активация виртуального окружения
call venv\Scripts\activate

REM Установка зависимостей
echo Устанавливаю зависимости...
pip install -r requirements.txt --quiet

REM Запуск приложения
echo.
echo ============================================
echo Запускаю сервер...
echo ============================================
echo.
python app.py

pause

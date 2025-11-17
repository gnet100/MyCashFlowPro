@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

cls
echo ============================================================
echo 🚀 מערכת ניהול כספים - הפעלה מהירה
echo ============================================================
echo.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo 📂 תיקייה נוכחית: %CD%
echo.

REM Open browser after 3 seconds
start /B cmd /c "timeout /t 3 >nul && start http://localhost:5000"

REM Try Python in PATH
echo 🔍 מחפש Python...
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ Python נמצא בנתיב
    echo 🚀 מפעיל את המערכת...
    echo.
    python start.py
    goto :end
)

REM Try Miniconda
echo ⚠️ Python לא בנתיב, מנסה Miniconda...
if exist "C:\Users\Golan\miniconda3\python.exe" (
    echo ✅ נמצא Miniconda
    echo 🚀 מפעיל את המערכת...
    echo.
    "C:\Users\Golan\miniconda3\python.exe" start.py
    goto :end
)

REM Try common Python locations
echo ⚠️ Miniconda לא נמצא, מחפש במיקומים נפוצים...
if exist "C:\Python311\python.exe" (
    echo ✅ נמצא Python 3.11
    "C:\Python311\python.exe" start.py
    goto :end
)
if exist "C:\Python310\python.exe" (
    echo ✅ נמצא Python 3.10
    "C:\Python310\python.exe" start.py
    goto :end
)
if exist "C:\Python39\python.exe" (
    echo ✅ נמצא Python 3.9
    "C:\Python39\python.exe" start.py
    goto :end
)

REM Python not found
echo.
echo ❌ Python לא נמצא במערכת!
echo.
echo 💡 פתרונות:
echo   1. הוסף Python ל-PATH
echo   2. הרץ ידנית:
echo      C:\Users\Golan\miniconda3\python.exe start.py
echo   3. התקן Python מ-https://www.python.org
echo.
pause
goto :end

:end
echo.
echo ============================================================
if %ERRORLEVEL% NEQ 0 (
    echo ❌ המערכת נסגרה עם שגיאה
    pause
)

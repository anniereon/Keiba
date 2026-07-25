:: batファイルをANSIで保存

@echo off
setlocal
cd /d %~dp0

call .venv\Scripts\activate

cd /d "%~dp0"app\取得
python "レースデータ取得_仮予測・実績収集用.py" "result"
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] レースデータ取得_仮予測・実績収集用に失敗しました
    pause
    exit /b %ERRORLEVEL%
)

cd /d "%~dp0"app\編集
python "historyデータ追加.py"
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] historyデータ追加に失敗しました
    pause
    exit /b %ERRORLEVEL%
)

cd /d "%~dp0"app\取得
python "database取得.py"
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] database取得に失敗しました
    pause
    exit /b %ERRORLEVEL%
)

cd /d "%~dp0"app\編集
python "historyデータ更新.py"
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] historyデータ更新に失敗しました
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo すべての処理が正常に完了しました
pause
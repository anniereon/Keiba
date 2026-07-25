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

echo.
echo すべての処理が正常に完了しました
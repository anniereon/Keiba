:: batファイルをANSIで保存

@echo off
setlocal
cd /d %~dp0

call .venv\Scripts\activate

cd /d "%~dp0"app\取得
python "レースデータ取得_仮予測・実績収集用.py" "shutuba"
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] レースデータ取得_仮予測・実績収集用に失敗しました
    pause
    exit /b %ERRORLEVEL%
)

cd /d "%~dp0"app\業務
python "予想データ作成.py" "bck"
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] 予想データ作成に失敗しました
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo すべての処理が正常に完了しました
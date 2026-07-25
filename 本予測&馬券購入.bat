:: batファイルをANSIで保存

@echo off
setlocal
cd /d %~dp0

call .venv\Scripts\activate

cd /d "%~dp0"app\業務
python "本予測判定.py"
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] 本予測判定に失敗しました
    pause
    exit /b %ERRORLEVEL%
)

cd /d "%~dp0"app\取得
python "レースデータ取得_本予測用.py"
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] レースデータ取得_本予測用に失敗しました
    pause
    exit /b %ERRORLEVEL%
)

cd /d "%~dp0"app\業務
python "予想データ作成.py" "prd"
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] 予想データ作成に失敗しました
    pause
    exit /b %ERRORLEVEL%
)

cd /d "%~dp0"app\業務
python "馬券購入.py"
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] 馬券購入に失敗しました
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo すべての処理が正常に完了しました
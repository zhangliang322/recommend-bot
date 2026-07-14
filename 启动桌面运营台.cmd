@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%~dp0src"
py -3.11 -m product_reco_bot.desktop.app
if errorlevel 1 (
  echo.
  echo 桌面运营台启动失败，请确认已安装 requirements.txt 中的依赖。
  pause
)

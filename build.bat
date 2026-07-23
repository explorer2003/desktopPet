@echo off
chcp 65001 >nul
echo ============================================
echo   桌宠 - 打包为 EXE
echo ============================================
echo.

echo 正在打包，请稍候...

pyinstaller --onefile --windowed ^
    --name "桌宠" ^
    --hidden-import PyQt5.QtCore ^
    --hidden-import PyQt5.QtGui ^
    --hidden-import PyQt5.QtWidgets ^
    pet.py

if %errorlevel% neq 0 (
    echo 打包失败
    pause
    exit /b 1
)

echo.
echo ============================================
echo   打包完成!
echo   EXE 文件位于: dist\桌宠.exe
echo   可以将其复制到任意位置双击运行
echo ============================================
pause
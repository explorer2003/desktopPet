@echo off
chcp 65001 >nul
echo ============================================
echo   桌宠 - 环境安装
echo ============================================
echo.

echo [1/2] 安装 Python 依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 依赖安装失败，请检查网络或手动安装
    pause
    exit /b 1
)

echo.
echo [2/2] 去除图片背景...
python process_image.py
if %errorlevel% neq 0 (
    echo 图片处理失败
    pause
    exit /b 1
)

echo.
echo ============================================
echo   安装完成!
echo   现在可以双击 pet.py 运行桌宠
echo   或运行 build.bat 打包为 EXE
echo ============================================
pause
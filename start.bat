@echo off
echo ====================================
echo      论文评定系统启动脚本
echo ====================================
echo.

echo 正在检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请确保Python 3.13.1+已安装并添加到PATH
    pause
    exit /b 1
)

echo.
echo 正在检查依赖包...
pip show Flask >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误: 依赖包安装失败
        pause
        exit /b 1
    )
) else (
    echo 依赖包检查完成
)

echo.
echo 正在启动论文评定系统...
echo 系统将在 http://localhost:5000 运行
echo 默认管理员账户: admin / admin123
echo.
echo 按 Ctrl+C 停止服务器
echo ====================================
echo.

python app.py

echo.
echo 系统已停止运行
pause
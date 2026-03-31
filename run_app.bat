@echo off
chcp 65001 >nul
REM TSH代谢风险评估工具 - Windows启动脚本

echo ╔════════════════════════════════════════════════════════════════╗
echo ║         TSH代谢风险评估工具 - 启动脚本                          ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python
    echo 请安装Python 3.8+: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✓ Python已检测到

REM 检查虚拟环境
if not exist "venv" (
    echo.
    echo 📦 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo.
echo 🔌 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo.
echo 📥 检查依赖...
pip install -q -r requirements.txt

echo.
echo ✓ 依赖检查完成

REM 启动应用
echo.
echo 🚀 启动应用...
echo.
echo ══════════════════════════════════════════════════════════════════
echo   应用将在浏览器中打开
echo   地址: http://localhost:8501
echo ══════════════════════════════════════════════════════════════════
echo.

streamlit run app.py

REM 停用虚拟环境
call venv\Scripts\deactivate.bat

pause

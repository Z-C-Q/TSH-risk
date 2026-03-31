#!/bin/bash
# TSH代谢风险评估工具 - 启动脚本
# 支持macOS/Linux

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         TSH代谢风险评估工具 - 启动脚本                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 检查Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ 错误: 未找到Python"
    echo "请安装Python 3.8+: https://www.python.org/downloads/"
    exit 1
fi

echo "✓ Python已检测到: $($PYTHON_CMD --version)"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 创建虚拟环境..."
    $PYTHON_CMD -m venv venv
fi

# 激活虚拟环境
echo ""
echo "🔌 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo ""
echo "📥 检查依赖..."
pip install -q -r requirements.txt

# 检查Streamlit
if ! command -v streamlit &> /dev/null; then
    echo ""
    echo "📥 安装Streamlit..."
    pip install -q streamlit
fi

echo ""
echo "✓ 依赖检查完成"

# 启动应用
echo ""
echo "🚀 启动应用..."
echo ""
echo "══════════════════════════════════════════════════════════════════"
echo "  应用将在浏览器中打开"
echo "  地址: http://localhost:8501"
echo "══════════════════════════════════════════════════════════════════"
echo ""

streamlit run app.py

# 停用虚拟环境
deactivate

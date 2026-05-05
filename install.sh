#!/bin/bash

echo "=========================================="
echo "初中数学错题本应用 - 自动安装脚本"
echo "=========================================="
echo ""

# 检查Python版本
echo "检查Python版本..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    PIP_CMD=pip3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
    PIP_CMD=pip
else
    echo "错误: 未找到Python，请先安装Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "✓ 找到Python: $PYTHON_VERSION"
echo ""

# 创建虚拟环境（可选）
read -p "是否创建虚拟环境? (推荐) [y/N]: " create_venv
if [[ $create_venv =~ ^[Yy]$ ]]; then
    echo "创建虚拟环境..."
    $PYTHON_CMD -m venv venv

    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "✓ 虚拟环境已激活"
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
        echo "✓ 虚拟环境已激活"
    fi
    echo ""
fi

# 安装依赖
echo "安装Python依赖包..."
$PIP_CMD install -r requirements.txt
echo ""

# 创建.env文件
if [ ! -f ".env" ]; then
    echo "创建.env配置文件..."
    cp .env.example .env
    echo "✓ .env文件已创建"
    echo ""
    echo "⚠️  重要: 请编辑.env文件，填入你的Anthropic API密钥"
    echo "   获取API密钥: https://console.anthropic.com/"
    echo ""
else
    echo "✓ .env文件已存在"
    echo ""
fi

# 创建必要目录
echo "创建必要目录..."
mkdir -p data
mkdir -p static/uploads
echo "✓ 目录创建完成"
echo ""

# 运行测试
echo "运行环境测试..."
$PYTHON_CMD test_setup.py
echo ""

echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "下一步:"
echo "1. 编辑.env文件，填入你的Anthropic API密钥"
echo "2. 运行应用: $PYTHON_CMD app.py"
echo "3. 访问: http://localhost:5000"
echo ""
echo "详细使用说明请查看 QUICKSTART.md"
echo ""

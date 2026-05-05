@echo off
echo ==========================================
echo 初中数学错题本应用 - 自动安装脚本
echo ==========================================
echo.

REM 检查Python
echo 检查Python版本...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo √ 找到Python: %PYTHON_VERSION%
echo.

REM 询问是否创建虚拟环境
set /p create_venv="是否创建虚拟环境? (推荐) [y/N]: "
if /i "%create_venv%"=="y" (
    echo 创建虚拟环境...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo √ 虚拟环境已激活
    echo.
)

REM 安装依赖
echo 安装Python依赖包...
pip install -r requirements.txt
echo.

REM 创建.env文件
if not exist ".env" (
    echo 创建.env配置文件...
    copy .env.example .env
    echo √ .env文件已创建
    echo.
    echo ⚠️  重要: 请编辑.env文件，填入你的Anthropic API密钥
    echo    获取API密钥: https://console.anthropic.com/
    echo.
) else (
    echo √ .env文件已存在
    echo.
)

REM 创建必要目录
echo 创建必要目录...
if not exist "data" mkdir data
if not exist "static\uploads" mkdir static\uploads
echo √ 目录创建完成
echo.

REM 运行测试
echo 运行环境测试...
python test_setup.py
echo.

echo ==========================================
echo 安装完成！
echo ==========================================
echo.
echo 下一步:
echo 1. 编辑.env文件，填入你的Anthropic API密钥
echo 2. 运行应用: python app.py
echo 3. 访问: http://localhost:5000
echo.
echo 详细使用说明请查看 QUICKSTART.md
echo.
pause

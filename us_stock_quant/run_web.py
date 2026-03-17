"""
美股三因子量化交易系统 - 启动器
"""

import subprocess
import sys
import os

def check_streamlit():
    """检查streamlit是否安装"""
    try:
        import streamlit
        return True
    except ImportError:
        return False

def install_dependencies():
    """安装依赖"""
    print("正在安装依赖包...")
    requirements = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', requirements])
    print("✅ 依赖安装完成")

def main():
    """主函数"""
    print("=" * 60)
    print("   美股三因子量化交易系统")
    print("   Web可视化界面")
    print("=" * 60)
    print()
    
    # 检查依赖
    if not check_streamlit():
        print("首次运行，需要安装依赖...")
        install_dependencies()
    
    # 启动streamlit
    print()
    print("正在启动Web服务...")
    print("系统将在浏览器中自动打开")
    print("如果未自动打开，请访问: http://localhost:8501")
    print("按 Ctrl+C 停止服务")
    print()
    
    app_path = os.path.join(os.path.dirname(__file__), 'app.py')
    subprocess.call([
        sys.executable, '-m', 'streamlit', 'run', app_path,
        '--server.port=8501',
        '--server.address=localhost'
    ])

if __name__ == '__main__':
    main()

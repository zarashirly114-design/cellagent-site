import sys
import os

# 把项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from landing import app

# Vercel需要这个导出
if __name__ == "__main__":
    app.run()

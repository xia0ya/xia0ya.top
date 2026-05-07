#!/usr/bin/env python
"""启动Web服务"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = str(Path(__file__).parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from web.services.user_service import UserService

def main():
    # 初始化数据库
    UserService.init()

    # 启动服务
    import uvicorn
    uvicorn.run("web.main:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    main()

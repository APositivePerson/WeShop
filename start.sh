#!/bin/bash
# 启动微信小店AI助手服务

cd /home/wangziyi/.openclaw/workspace/wechat-shop-ai/backend

echo "🚀 启动微信小店AI上架助手..."

# 杀掉旧进程
pkill -f "uvicorn.*8080" 2>/dev/null || true
sleep 1

# 启动服务
python3 -c "
import sys
sys.path.insert(0, '..')
from main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8080)
" &

sleep 3

echo "✅ 服务已启动"
echo "📍 API文档: http://localhost:8080/docs"
echo "🌐 前端页面: http://localhost:8080/"
echo ""
echo "测试API配置:"
curl -s http://localhost:8080/api/config/test | python3 -m json.tool 2>/dev/null || echo "等待服务启动中..."

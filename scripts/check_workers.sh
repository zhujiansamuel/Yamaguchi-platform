#!/bin/bash
# Celery Worker 排查脚本
# 用于检测游离的 worker 进程

echo "=========================================="
echo "Celery Worker 排查工具"
echo "=========================================="
echo ""

# 1. 检查所有 celery worker 进程
echo "📋 1. 检查所有 Celery Worker 进程"
echo "---"
ps aux | grep -E "celery.*worker" | grep -v grep
echo ""

# 2. 检查 Docker 容器中的 worker
echo "📦 2. 检查 Docker 容器中的 Worker"
echo "---"
docker ps -a | grep -E "worker|celery"
echo ""

# 3. 检查进程树（找出父进程）
echo "🌳 3. 检查 Celery 进程树"
echo "---"
pgrep -af celery | while read pid cmd; do
    echo "PID: $pid"
    echo "CMD: $cmd"
    echo "Parent PID: $(ps -o ppid= -p $pid)"
    echo "---"
done
echo ""

# 4. 检查监听的队列
echo "🎯 4. 检查 Celery Worker 监听的队列"
echo "---"
echo "提示：运行以下命令查看活跃的 worker："
echo "  celery -A config inspect active_queues"
echo ""

# 5. 检查 Celery 配置文件中的队列设置
echo "⚙️  5. 检查队列配置"
echo "---"
if [ -f "apps/data_acquisition/celery.py" ]; then
    echo "yamato_tracking_10_queue 配置："
    grep -A 2 "yamato_tracking_10" apps/data_acquisition/celery.py
fi
echo ""

# 6. 提供清理建议
echo "🧹 6. 清理建议"
echo "---"
echo "如果发现多个 worker 进程，请执行以下操作："
echo ""
echo "方法 1: 停止所有 Docker 容器中的 worker"
echo "  docker-compose stop worker"
echo "  docker-compose rm -f worker"
echo "  docker-compose up -d worker"
echo ""
echo "方法 2: 杀死所有 Celery 进程（谨慎使用）"
echo "  pkill -9 -f 'celery.*worker'"
echo ""
echo "方法 3: 检查是否有多个 Docker Compose 项目"
echo "  docker ps -a --format '{{.Names}} {{.Image}} {{.Status}}' | grep worker"
echo ""
echo "方法 4: 重启整个服务栈"
echo "  docker-compose down"
echo "  docker-compose up -d"
echo ""

# 7. 检查 Redis/RabbitMQ 连接
echo "🔌 7. 检查消息队列连接"
echo "---"
echo "提示：检查有多少 worker 连接到消息队列："
if command -v redis-cli &> /dev/null; then
    echo "Redis 客户端连接数："
    redis-cli CLIENT LIST | grep -c "celery"
else
    echo "redis-cli 未安装，跳过检查"
fi
echo ""

# 8. 检查代码版本
echo "📝 8. 检查代码版本"
echo "---"
echo "当前 Git commit:"
git log --oneline -1
echo ""
echo "最后修改时间:"
git log -1 --format="%ai" apps/data_acquisition/tasks.py
echo ""

echo "=========================================="
echo "排查完成！"
echo "=========================================="

#!/bin/bash
# Celery Worker 快速清理脚本
# 警告：此脚本会停止所有 worker 进程，请谨慎使用

set -e

echo "=========================================="
echo "⚠️  Celery Worker 清理脚本"
echo "=========================================="
echo ""
echo "此脚本将："
echo "1. 停止所有 Docker 容器中的 Celery worker"
echo "2. 删除所有 Celery worker 容器"
echo "3. 杀死所有游离的 celery 进程"
echo "4. 重新启动所有 Celery worker"
echo ""

read -p "是否继续？(yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "已取消"
    exit 0
fi

echo ""
echo "📋 步骤 1: 停止 Docker Compose 中的所有 Celery worker"
echo "---"
if [ -f "docker-compose.yml" ]; then
    # 停止所有 celery worker 容器
    echo "停止所有 celery worker 容器..."
    docker-compose ps --services | grep celery_worker | while read service; do
        echo "  - 停止 $service"
        docker-compose stop $service 2>/dev/null || echo "    ⚠️  停止失败，继续..."
        docker-compose rm -f $service 2>/dev/null || echo "    ⚠️  删除失败，继续..."
    done
    
    # 兼容旧的 worker 命名
    docker-compose stop worker 2>/dev/null || true
    docker-compose rm -f worker 2>/dev/null || true
else
    echo "⚠️  未找到 docker-compose.yml，跳过"
fi
echo ""

echo "🔍 步骤 2: 查找所有 celery/worker 容器"
echo "---"
WORKER_CONTAINERS=$(docker ps -a --filter "name=celery" --format "{{.ID}}" || true)
if [ -n "$WORKER_CONTAINERS" ]; then
    echo "找到以下 celery 容器："
    docker ps -a --filter "name=celery" --format "{{.ID}}\t{{.Names}}\t{{.Status}}"
    echo ""
    echo "停止并删除这些容器..."
    echo "$WORKER_CONTAINERS" | xargs docker rm -f || echo "⚠️  删除容器失败"
else
    echo "✅ 没有找到 celery 容器"
fi
echo ""

echo "🔍 步骤 3: 查找游离的 celery 进程"
echo "---"
CELERY_PIDS=$(pgrep -f "celery.*worker" || true)
if [ -n "$CELERY_PIDS" ]; then
    echo "找到以下 celery 进程："
    ps aux | grep "celery.*worker" | grep -v grep || true
    echo ""
    echo "杀死这些进程..."
    echo "$CELERY_PIDS" | xargs kill -9 || echo "⚠️  杀死进程失败"
    sleep 2
    
    # 再次检查
    REMAINING=$(pgrep -f "celery.*worker" || true)
    if [ -n "$REMAINING" ]; then
        echo "⚠️  仍有进程残留："
        ps aux | grep "celery.*worker" | grep -v grep || true
    else
        echo "✅ 所有 celery 进程已清理"
    fi
else
    echo "✅ 没有找到游离的 celery 进程"
fi
echo ""

echo "🚀 步骤 4: 重新启动所有 Celery worker"
echo "---"
if [ -f "docker-compose.yml" ]; then
    echo "启动所有 celery worker 容器..."
    docker-compose ps --services | grep celery_worker | while read service; do
        echo "  - 启动 $service"
        docker-compose up -d $service
    done
    
    echo ""
    echo "等待 worker 启动..."
    sleep 5
    echo ""
    echo "所有 Celery Worker 状态："
    docker-compose ps | grep celery
    echo ""
    echo "Yamato Tracking 10 Worker 日志（最后 20 行）："
    docker-compose logs --tail 20 celery_worker_yamato_tracking_10 2>/dev/null || echo "⚠️  未找到 yamato_tracking_10 worker"
else
    echo "⚠️  未找到 docker-compose.yml，请手动启动 worker"
fi
echo ""

echo "✅ 步骤 5: 验证清理结果"
echo "---"
echo "Docker 容器："
docker ps | grep celery || echo "没有运行中的 celery 容器"
echo ""
echo "进程："
ps aux | grep "celery.*worker" | grep -v grep || echo "没有 celery 进程"
echo ""
echo "Yamato Tracking 10 Worker 详情："
docker ps --filter "name=yamato-tracking-10" --format "{{.Names}}\t{{.Status}}\t{{.Image}}" || echo "未找到"
echo ""

echo "=========================================="
echo "✅ 清理完成！"
echo "=========================================="
echo ""
echo "建议："
echo "1. 查看 Yamato Tracking 10 worker 日志："
echo "   docker-compose logs -f celery_worker_yamato_tracking_10"
echo ""
echo "2. 检查 worker 代码版本："
echo "   docker exec -it data-platform-celery-yamato-tracking-10 git log --oneline -1"
echo ""
echo "3. 查看所有 worker 状态："
echo "   docker-compose ps | grep celery"
echo ""
echo "4. 测试任务执行："
echo "   删除旧的测试批次，重新上传 Excel 文件"
echo ""

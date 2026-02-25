#!/bin/bash
# Yamato Tracking 10 Worker 专用重启脚本

echo "=========================================="
echo "🔄 重启 Yamato Tracking 10 Worker"
echo "=========================================="
echo ""

# 检查是否在正确的目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误：未找到 docker-compose.yml"
    echo "请在项目根目录运行此脚本"
    exit 1
fi

echo "📋 当前 Yamato Tracking 10 Worker 状态："
docker-compose ps celery_worker_yamato_tracking_10
echo ""

read -p "是否重启 Yamato Tracking 10 Worker？(yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "已取消"
    exit 0
fi

echo ""
echo "🛑 步骤 1: 停止容器"
echo "---"
docker-compose stop celery_worker_yamato_tracking_10
echo "✅ 已停止"
echo ""

echo "🗑️  步骤 2: 删除容器"
echo "---"
docker-compose rm -f celery_worker_yamato_tracking_10
echo "✅ 已删除"
echo ""

echo "🚀 步骤 3: 重新创建并启动容器"
echo "---"
docker-compose up -d celery_worker_yamato_tracking_10
echo "✅ 已启动"
echo ""

echo "⏳ 等待容器启动..."
sleep 5
echo ""

echo "📊 步骤 4: 验证状态"
echo "---"
echo "容器状态："
docker-compose ps celery_worker_yamato_tracking_10
echo ""

echo "容器详情："
docker ps --filter "name=yamato-tracking-10" --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
echo ""

echo "📝 步骤 5: 查看日志（最后 30 行）"
echo "---"
docker-compose logs --tail 30 celery_worker_yamato_tracking_10
echo ""

echo "=========================================="
echo "✅ 重启完成！"
echo "=========================================="
echo ""
echo "📌 后续操作："
echo ""
echo "1. 实时查看日志："
echo "   docker-compose logs -f celery_worker_yamato_tracking_10"
echo ""
echo "2. 检查代码版本："
echo "   docker exec -it data-platform-celery-yamato-tracking-10 git log --oneline -1"
echo ""
echo "3. 进入容器调试："
echo "   docker exec -it data-platform-celery-yamato-tracking-10 bash"
echo ""
echo "4. 验证修复："
echo "   - 删除旧的测试批次（在 Django Admin 中）"
echo "   - 重新上传包含 11 个追踪号的 Excel 文件"
echo "   - 查看日志，应该看到："
echo "     * Processing batch 1/2 (10 numbers) - Progress: 0.0%"
echo "     * Processing batch 2/2 (1 numbers) - Progress: 90.9%"
echo "   - 检查数据库，所有 11 个 TrackingJob 应该都是 completed 状态"
echo ""

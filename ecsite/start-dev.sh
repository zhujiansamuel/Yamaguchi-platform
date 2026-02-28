#!/bin/bash

# FastAdmin 开发服务器启动脚本
# 修复 /admin 404 问题

echo "========================================="
echo "FastAdmin 开发服务器"
echo "========================================="
echo ""

PORT=8080

# 检查端口
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  端口 $PORT 被占用，尝试终止..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null
    sleep 1
fi

echo "启动方式选择："
echo "1. 方式一: 从项目根目录启动（-t public 参数）"
echo "2. 方式二: 从 public 目录启动"
echo "3. 方式三: 使用 ThinkPHP think run 命令"
echo ""
read -p "请选择 (1-3, 默认1): " METHOD
METHOD=${METHOD:-1}

case $METHOD in
    1)
        echo ""
        echo "=== 方式一: 从项目根目录启动 ==="
        echo ""
        echo "访问地址："
        echo "  前台: http://localhost:$PORT"
        echo "  后台: http://localhost:$PORT/admin"
        echo ""
        echo "按 Ctrl+C 停止"
        echo ""

        # 从项目根目录启动，使用 router.php
        php -S localhost:$PORT -t public public/router.php
        ;;

    2)
        echo ""
        echo "=== 方式二: 从 public 目录启动 ==="
        echo ""
        echo "访问地址："
        echo "  前台: http://localhost:$PORT"
        echo "  后台: http://localhost:$PORT/admin"
        echo ""
        echo "按 Ctrl+C 停止"
        echo ""

        # 切换到 public 目录启动
        cd public
        php -S localhost:$PORT router.php
        ;;

    3)
        echo ""
        echo "=== 方式三: 使用 ThinkPHP 命令 ==="
        echo ""

        if [ -f "think" ]; then
            php think run -p $PORT
        else
            echo "❌ think 命令不存在"
            exit 1
        fi
        ;;

    *)
        echo "无效选项"
        exit 1
        ;;
esac

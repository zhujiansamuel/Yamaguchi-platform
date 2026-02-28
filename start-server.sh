#!/bin/bash

# FastAdmin 项目快速启动脚本

echo "========================================="
echo "FastAdmin 项目启动"
echo "========================================="
echo ""

# 检查端口是否被占用
PORT=8001
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  端口 $PORT 已被占用"
    echo ""
    echo "正在使用的进程："
    lsof -Pi :$PORT -sTCP:LISTEN
    echo ""
    echo "⚠️  端口 $PORT 已被占用，正在终止占用进程..."
    lsof -ti:$PORT | xargs kill -9
    sleep 1
fi

# 检查 public 目录
if [ ! -d "public" ]; then
    echo "❌ 错误: public 目录不存在"
    exit 1
fi

# 检查 index.php
if [ ! -f "public/index.php" ]; then
    echo "❌ 错误: public/index.php 不存在"
    exit 1
fi

echo "✅ 启动 PHP 内置服务器..."
echo ""
echo "访问地址："
echo "  前台: http://localhost:$PORT"
echo "  后台: http://localhost:$PORT/admin"
echo ""
echo "默认管理员账号:"
echo "  用户名: admin"
echo "  密码: [安装时设置的密码]"
echo ""
echo "按 Ctrl+C 停止服务器"
echo "========================================="
echo ""

# 启动服务器（从 public 目录启动，确保路由正常工作）
(cd public && php -S localhost:$PORT router.php > ../server.log 2>&1) &

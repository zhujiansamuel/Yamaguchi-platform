#!/bin/bash

# FastAdmin 项目快速启动脚本（修复版）

echo "========================================="
echo "FastAdmin 项目启动"
echo "========================================="
echo ""

# 检查端口是否被占用
PORT=8080
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  端口 $PORT 已被占用"
    echo ""
    echo "正在使用的进程："
    lsof -Pi :$PORT -sTCP:LISTEN
    echo ""
    read -p "是否终止占用端口的进程并重新启动? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "终止进程..."
        lsof -ti:$PORT | xargs kill -9
        sleep 1
    else
        echo "已取消启动"
        exit 0
    fi
fi

# 检查 public 目录
if [ ! -d "public" ]; then
    echo "❌ 错误: public 目录不存在"
    exit 1
fi

# 检查必要文件
if [ ! -f "public/index.php" ]; then
    echo "❌ 错误: public/index.php 不存在"
    exit 1
fi

if [ ! -f "public/router.php" ]; then
    echo "❌ 错误: public/router.php 不存在"
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
echo "  密码: [数据库中的密码]"
echo ""
echo "提示:"
echo "  - 使用 Ctrl+C 停止服务器"
echo "  - 查看日志以诊断问题"
echo "========================================="
echo ""

# 切换到项目根目录
cd "$(dirname "$0")"

# 启动服务器（使用完整路径）
# 方式 1: 使用 router.php（推荐）
php -S localhost:$PORT -t public public/router.php

# 如果上面的方式不工作，可以尝试：
# php -S localhost:$PORT public/router.php

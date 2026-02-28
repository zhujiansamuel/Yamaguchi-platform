#!/bin/bash

# macOS PHP 扩展安装指南

echo "检测到你使用的是 macOS 系统"
echo "PHP 版本: $(php -v | head -n 1)"
echo ""

# 检查 Homebrew
if command -v brew &> /dev/null; then
    echo "✓ Homebrew 已安装"
    echo ""
    echo "安装缺失的 PHP 扩展："
    echo ""

    # 检测 PHP 版本
    PHP_VERSION=$(php -r "echo PHP_MAJOR_VERSION.'.'.PHP_MINOR_VERSION;")

    echo "方法 1: 使用 Homebrew 重新安装 PHP (推荐)"
    echo "----------------------------------------"
    echo "brew reinstall php@${PHP_VERSION}"
    echo ""
    echo "这会安装完整的 PHP 及所有常用扩展"
    echo ""

    echo "方法 2: 使用 PECL 安装扩展"
    echo "----------------------------------------"
    echo "pecl install pdo"
    echo "pecl install bcmath"
    echo ""

    echo "方法 3: 检查扩展是否已存在但未启用"
    echo "----------------------------------------"
    echo "查找 php.ini 位置:"
    php --ini
    echo ""
    echo "编辑 php.ini 文件，确保以下行未被注释："
    echo "extension=pdo"
    echo "extension=bcmath"

else
    echo "✗ 未检测到 Homebrew"
    echo "建议先安装 Homebrew: https://brew.sh"
    echo "然后运行: brew install php"
fi

echo ""
echo "================================"
echo "验证扩展是否安装成功："
echo "php -m | grep -E '(pdo|bcmath)'"
echo "================================"

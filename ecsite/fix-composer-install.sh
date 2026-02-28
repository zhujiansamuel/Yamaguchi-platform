#!/bin/bash

echo "修复 Composer 依赖安装问题"
echo "========================================"
echo ""

echo "问题: Gitee 仓库访问被拒绝 (403 错误)"
echo "解决方案: 使用 Packagist 中国镜像"
echo ""

# 方法 1: 使用阿里云镜像
echo "方法 1: 配置阿里云 Composer 镜像 (推荐)"
echo "----------------------------------------"
echo "composer config -g repo.packagist composer https://mirrors.aliyun.com/composer/"
echo ""

# 方法 2: 使用腾讯云镜像
echo "方法 2: 配置腾讯云 Composer 镜像"
echo "----------------------------------------"
echo "composer config -g repo.packagist composer https://mirrors.cloud.tencent.com/composer/"
echo ""

# 方法 3: 临时禁用有问题的仓库
echo "方法 3: 临时禁用 Gitee 仓库"
echo "----------------------------------------"
echo "这会创建一个临时的 composer.json，移除有问题的 Gitee 仓库配置"
echo ""

read -p "是否执行方法 1（配置阿里云镜像）? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "配置阿里云 Composer 镜像..."
    composer config -g repo.packagist composer https://mirrors.aliyun.com/composer/

    echo ""
    echo "✓ 镜像配置完成"
    echo ""

    read -p "是否现在安装依赖? (y/n): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "安装依赖中..."
        composer install --ignore-platform-reqs

        if [ $? -eq 0 ]; then
            echo ""
            echo "✓ 依赖安装成功！"
        else
            echo ""
            echo "✗ 依赖安装失败，请查看错误信息"
            echo ""
            echo "提示: 如果仍然失败，可以尝试："
            echo "1. 删除 composer.lock: rm composer.lock"
            echo "2. 清除 Composer 缓存: composer clear-cache"
            echo "3. 重试安装: composer install --ignore-platform-reqs"
        fi
    fi
else
    echo ""
    echo "跳过自动配置"
    echo ""
    echo "你可以手动执行以下命令："
    echo "1. composer config -g repo.packagist composer https://mirrors.aliyun.com/composer/"
    echo "2. composer install --ignore-platform-reqs"
fi

echo ""
echo "========================================"
echo "说明:"
echo "- 使用 --ignore-platform-reqs 可以忽略 PHP 扩展检查"
echo "- 安装完成后，记得安装缺失的 PHP 扩展"
echo "- 运行 ./install-php-extensions-macos.sh 查看扩展安装指南"
echo "========================================"

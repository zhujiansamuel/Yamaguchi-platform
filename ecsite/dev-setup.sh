#!/bin/bash

# Mobile Zone Website - 开发环境快速配置脚本
# 使用方法: bash dev-setup.sh

echo "========================================="
echo "Mobile Zone Website 开发环境配置"
echo "========================================="
echo ""

# 检查 PHP 版本
echo "1. 检查 PHP 环境..."
if command -v php &> /dev/null; then
    PHP_VERSION=$(php -v | head -n 1)
    echo "✓ PHP 已安装: $PHP_VERSION"

    # 检查 PHP 版本是否满足要求
    PHP_VERSION_NUM=$(php -r "echo PHP_VERSION;" | cut -d. -f1,2)
    if (( $(echo "$PHP_VERSION_NUM >= 7.4" | bc -l) )); then
        echo "✓ PHP 版本满足要求 (>= 7.4)"
    else
        echo "✗ PHP 版本过低，需要 >= 7.4"
        exit 1
    fi
else
    echo "✗ PHP 未安装，请先安装 PHP >= 7.4"
    exit 1
fi

echo ""

# 检查必需的 PHP 扩展
echo "2. 检查 PHP 扩展..."
REQUIRED_EXTENSIONS=("json" "curl" "pdo" "bcmath" "mbstring")
MISSING_EXTENSIONS=()

for ext in "${REQUIRED_EXTENSIONS[@]}"; do
    if php -m | grep -qi "^$ext$"; then
        echo "✓ $ext 扩展已安装"
    else
        echo "✗ $ext 扩展未安装"
        MISSING_EXTENSIONS+=($ext)
    fi
done

if [ ${#MISSING_EXTENSIONS[@]} -gt 0 ]; then
    echo ""
    echo "请安装以下缺失的 PHP 扩展: ${MISSING_EXTENSIONS[*]}"
    echo "Ubuntu/Debian: sudo apt-get install php-${MISSING_EXTENSIONS[*]}"
    echo "CentOS/RHEL: sudo yum install php-${MISSING_EXTENSIONS[*]}"
fi

echo ""

# 检查 Composer
echo "3. 检查 Composer..."
if command -v composer &> /dev/null; then
    COMPOSER_VERSION=$(composer --version)
    echo "✓ Composer 已安装: $COMPOSER_VERSION"
else
    echo "✗ Composer 未安装"
    echo "请访问 https://getcomposer.org/ 安装 Composer"
    echo "或运行以下命令安装："
    echo "curl -sS https://getcomposer.org/installer | php"
    echo "sudo mv composer.phar /usr/local/bin/composer"
    exit 1
fi

echo ""

# 安装 Composer 依赖
echo "4. 安装 Composer 依赖..."
if [ -d "vendor" ]; then
    echo "vendor 目录已存在，是否重新安装依赖？ (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "安装依赖中..."
        composer install
    else
        echo "跳过依赖安装"
    fi
else
    echo "安装依赖中..."
    composer install
fi

echo ""

# 检查并创建 .env 文件
echo "5. 配置环境文件..."
if [ ! -f ".env" ]; then
    if [ -f ".env.sample" ]; then
        cp .env.sample .env
        echo "✓ 已创建 .env 文件（基于 .env.sample）"
        echo "! 请编辑 .env 文件配置数据库连接信息"
    else
        echo "✗ .env.sample 文件不存在"
    fi
else
    echo "✓ .env 文件已存在"
fi

echo ""

# 设置目录权限
echo "6. 设置目录权限..."
if [ -d "runtime" ]; then
    chmod -R 755 runtime
    echo "✓ runtime 目录权限已设置"
fi

if [ -d "public/uploads" ]; then
    chmod -R 755 public/uploads
    echo "✓ public/uploads 目录权限已设置"
else
    mkdir -p public/uploads
    chmod -R 755 public/uploads
    echo "✓ public/uploads 目录已创建并设置权限"
fi

echo ""

# 检查 MySQL
echo "7. 检查 MySQL..."
if command -v mysql &> /dev/null; then
    MYSQL_VERSION=$(mysql --version)
    echo "✓ MySQL 已安装: $MYSQL_VERSION"
else
    echo "! MySQL 命令未找到，请确保 MySQL 已安装并运行"
fi

echo ""
echo "========================================="
echo "配置完成！"
echo "========================================="
echo ""
echo "下一步操作："
echo "1. 编辑 .env 文件，配置数据库连接信息"
echo "2. 创建数据库: CREATE DATABASE fastadmin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
echo "3. 在 PhpStorm 中打开项目"
echo "4. 参考 PHPSTORM_SETUP.md 文档完成 PhpStorm 配置"
echo "5. 访问 http://localhost:端口/install.php 进行安装"
echo ""
echo "详细配置说明请查看 PHPSTORM_SETUP.md 文件"
echo ""

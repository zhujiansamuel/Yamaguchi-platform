<?php
// 路由测试脚本

echo "=== ThinkPHP 路由测试 ===\n\n";

// 设置环境
$_SERVER['SCRIPT_NAME'] = '/index.php';
$_SERVER['DOCUMENT_ROOT'] = __DIR__ . '/public';
$_SERVER['HTTP_HOST'] = 'localhost:8080';

// 测试不同的 URL
$test_urls = [
    '/',
    '/index',
    '/admin',
    '/admin/index/login',
    '/api',
];

foreach ($test_urls as $url) {
    echo "测试 URL: $url\n";
    $_SERVER['REQUEST_URI'] = $url;

    // 模拟 router.php 的逻辑
    $script = $_SERVER["DOCUMENT_ROOT"] . $_SERVER["SCRIPT_NAME"];

    if (is_file($script)) {
        echo "  -> 文件存在: $script (直接返回)\n";
    } else {
        echo "  -> 需要路由到: public/index.php\n";
        $_SERVER["SCRIPT_FILENAME"] = __DIR__ . '/public/index.php';

        // 检查是否会被 ThinkPHP 处理
        $pathinfo = parse_url($url, PHP_URL_PATH);
        echo "  -> PATH_INFO: $pathinfo\n";
    }
    echo "\n";
}

echo "\n=== 检查关键文件 ===\n";
$files = [
    'public/index.php',
    'public/router.php',
    'application/admin/controller/Index.php',
    'application/route.php',
];

foreach ($files as $file) {
    if (file_exists($file)) {
        echo "✓ $file\n";
    } else {
        echo "✗ $file (不存在)\n";
    }
}

echo "\n=== 检查路由配置 ===\n";
if (file_exists('application/route.php')) {
    echo "route.php 内容:\n";
    echo file_get_contents('application/route.php');
} else {
    echo "route.php 不存在，使用默认路由\n";
}

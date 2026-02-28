<?php
// +----------------------------------------------------------------------
// | ThinkPHP [ WE CAN DO IT JUST THINK ]
// +----------------------------------------------------------------------
// | Copyright (c) 2006~2016 http://thinkphp.cn All rights reserved.
// +----------------------------------------------------------------------
// | Licensed ( http://www.apache.org/licenses/LICENSE-2.0 )
// +----------------------------------------------------------------------
// | Author: liu21st <liu21st@gmail.com>
// +----------------------------------------------------------------------
// $Id$

// 获取请求的 URI
$uri = urldecode(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));

// 如果请求的是真实存在的文件（静态资源），直接返回
if ($uri !== '/' && file_exists(__DIR__ . $uri)) {
    return false;
}

// 否则路由到 index.php 处理
$_SERVER["SCRIPT_FILENAME"] = __DIR__ . '/index.php';
require __DIR__ . "/index.php";

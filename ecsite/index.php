<?php

// +----------------------------------------------------------------------
// | ThinkPHP [ WE CAN DO IT JUST THINK ]
// +----------------------------------------------------------------------
// | Copyright (c) 2006-2016 http://thinkphp.cn All rights reserved.
// +----------------------------------------------------------------------
// | Licensed ( http://www.apache.org/licenses/LICENSE-2.0 )
// +----------------------------------------------------------------------
// | Author: liu21st <liu21st@gmail.com>
// +----------------------------------------------------------------------
// [ アプリケーションエントリーファイル ]
// アプリケーションディレクトリを定義
define('APP_PATH', __DIR__ . '/application/');

// インストール済みかどうかを判断
// if (!is_file(APP_PATH . 'admin/command/Install/install.lock')) {
//     header("location:./install.php");
//     exit;
// }

// フレームワークのブートストラップファイルを読み込む
require __DIR__ . '/thinkphp/start.php';

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
// [ バックエンドエントリーファイル ]
// このファイルを使用することで非表示にできますadminモジュールの効果
// あなたの安全のために，このファイル名を変更することは強く推奨しませんadmin.php
// アプリケーションディレクトリを定義
define('APP_PATH', __DIR__ . '/application/');

// インストール済みかどうかを判断
if (!is_file(APP_PATH . 'admin/command/Install/install.lock')) {
   // header("location:./install.php");
    exit;
}

// フレームワークのブートストラップファイルを読み込む
require __DIR__ . '/thinkphp/base.php';

// にバインドadminモジュール
\think\Route::bind('admin');

// ルーティングを無効化
\think\App::route(false);

// ルートを設定url
\think\Url::root('');

// アプリケーションを実行
\think\App::run()->send();

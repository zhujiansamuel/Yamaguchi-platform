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
// アプリケーション動作拡張定義ファイル
return [
    // アプリケーション初期化
    'app_init'     => [
        'app\\common\\behavior\\Common',
    ],
    // アプリケーション開始
    'app_begin'    => [],
    // アプリケーションディスパッチ
    'app_dispatch' => [
        'app\\common\\behavior\\Common',
    ],
    // モジュール初期化
    'module_init'  => [
        'app\\common\\behavior\\Common',
    ],
    // プラグイン開始
    'addon_begin'  => [
        'app\\common\\behavior\\Common',
    ],
    // アクション実行開始
    'action_begin' => [],
    // ビュー内容フィルタリング
    'view_filter'  => [],
    // ログ書き込み
    'log_write'    => [],
    // アプリケーション終了
    'app_end'      => [],
];

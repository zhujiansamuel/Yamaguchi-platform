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

use think\Env;

return [
    // データベースタイプ
    'type'            => Env::get('database.type', 'mysql'),
    // サーバーアドレス
    'hostname'        => Env::get('database.hostname', '127.0.0.1'),
    // データベース名
    'database'        => Env::get('database.database', 'fastadmin'),
    // ユーザー名
    'username'        => Env::get('database.username', 'root'),
    // パスワード
    'password'        => Env::get('database.password', ''),
    // ポート
    'hostport'        => Env::get('database.hostport', ''),
    // 接続dsn
    'dsn'             => '',
    // データベース接続パラメーター
    'params'          => [],
    // データベースのエンコーディングはデフォルトで使用 utf8mb4
    'charset'         => Env::get('database.charset', 'utf8mb4'),
    // データベーステーブルプレフィックス
    'prefix'          => Env::get('database.prefix', 'fa_'),
    // データベースデバッグモード
    'debug'           => Env::get('database.debug', false),
    // データベース配置方式:0 集中型(単一サーバー),1 分散型(マスター・スレーブサーバー)
    'deploy'          => 0,
    // データベースの読み書きを分離するかどうか マスター・スレーブ方式で有効
    'rw_separate'     => false,
    // 読み書き分離後 マスターサーバー数
    'master_num'      => 1,
    // スレーブサーバー番号を指定
    'slave_no'        => '',
    // フィールドの存在を厳密にチェックするかどうか
    'fields_strict'   => true,
    // データセットの返却タイプ
    'resultset_type'  => 'array',
    // タイムスタンプフィールドを自動書き込み
    'auto_timestamp'  => false,
    // 時刻フィールド取得後のデフォルト形式,デフォルトはY-m-d H:i:s
    'datetime_format' => false,
    // 実行するかどうかSQLパフォーマンス解析
    'sql_explain'     => false,
];

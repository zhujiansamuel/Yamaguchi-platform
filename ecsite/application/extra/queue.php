<?php
return [
    'connector'  => 'Redis',          // Redis ドライバ
    'expire'     => 0,             // タスクの有効期限，デフォルトは60秒; 無効にする場合，に設定 null
    'default'    => 'default',    // デフォルトのキュー名
    'host'       => '127.0.0.1',       // redis ホストip
    'port'       => 6379,        // redis ポート
    'password'   => '',             // redis パスワード
    'select'     => 0,          // どの db，デフォルトは db0
    'timeout'    => 0,          // redis接続のタイムアウト時間
    'persistent' => false,
];

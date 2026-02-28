<?php

//アップロード設定
return [
    /**
     * アップロード先アドレス,デフォルトはローカルアップロード
     */
    'uploadurl' => 'ajax/upload',
    /**
     * CDNアドレス
     */
    'cdnurl'    => '',
    /**
     * ファイル保存形式
     */
    'savekey'   => '/uploads/{year}{mon}{day}/{filemd5}{.suffix}',
    /**
     * 最大アップロードサイズ
     */
    'maxsize'   => '10mb',
    /**
     * アップロード可能なファイルタイプ
     */
    'mimetype'  => 'jpg,png,bmp,jpeg,gif,webp,zip,rar,wav,mp4,mp3,webm,pdf',
    /**
     * 一括アップロードをサポートするかどうか
     */
    'multiple'  => false,
    /**
     * アップロードのタイムアウト時間，ここではのみ使用JSアップロードのタイムアウト制御
     */
    'timeout'  => 60000,
    /**
     * 分割アップロードをサポートするかどうか
     */
    'chunking'  => false,
    /**
     * デフォルトのチャンクサイズ
     */
    'chunksize' => 2097152,
    /**
     * フルURLモード
     */
    'fullmode' => false,
    /**
     * サムネイルスタイル
     */
    'thumbstyle' => '',
];

<?php

namespace app\common\model;

use think\Model;

/**
 * 会員ポイントログモデル
 */
class ScoreLog extends Model
{

    // テーブル名
    protected $name = 'user_score_log';
    // 自動タイムスタンプ書き込みを有効にする
    protected $autoWriteTimestamp = 'int';
    // タイムスタンプフィールド名を定義
    protected $createTime = 'createtime';
    protected $updateTime = '';
    // 追加属性
    protected $append = [
    ];
}

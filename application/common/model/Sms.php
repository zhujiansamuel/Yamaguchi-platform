<?php

namespace app\common\model;

use think\Model;

/**
 * SMS認証コード
 */
class Sms extends Model
{

    // 自動タイムスタンプ書き込みを有効にする
    protected $autoWriteTimestamp = 'int';
    // タイムスタンプフィールド名を定義
    protected $createTime = 'createtime';
    protected $updateTime = false;
    // 追加属性
    protected $append = [
    ];
}

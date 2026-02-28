<?php

namespace app\common\model;

use think\Model;

class UserGroup extends Model
{

    // テーブル名
    protected $name = 'user_group';
    // タイムスタンプフィールドを自動書き込み
    protected $autoWriteTimestamp = 'int';
    // タイムスタンプフィールド名を定義
    protected $createTime = 'createtime';
    protected $updateTime = 'updatetime';
    // 追加属性
    protected $append = [
    ];

}

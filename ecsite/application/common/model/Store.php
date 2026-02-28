<?php

namespace app\common\model;

use think\Model;


class Store extends Model
{

    // テーブル名
    protected $name = 'store';
    // 自動タイムスタンプ書き込みを有効にする
    protected $autoWriteTimestamp = 'int';
    // タイムスタンプフィールド名を定義
    protected $createTime = 'createtime';
    protected $updateTime = '';
    // 追加属性
    protected $append = [
    ];
}

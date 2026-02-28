<?php

namespace app\common\model;

use think\Model;


class OrderDetails extends Model
{

    // テーブル名
    protected $name = 'order_details';
    // 自動タイムスタンプ書き込みを有効にする
    protected $autoWriteTimestamp = 'int';
    // タイムスタンプフィールド名を定義
    protected $createTime = 'createtime';
    protected $updateTime = '';
    // 追加属性
    protected $append = [
    ];

    public function getPriceAttr($value, $row)
    {
        return number_format($value);
    }

    public function getPriceZgAttr($value, $row)
    {
        return number_format($value);
    }

    public function goods()
    {
        return $this->belongsTo('Goods', 'goods_id')->field('id,jan');
    }

    

}

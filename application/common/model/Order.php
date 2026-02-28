<?php

namespace app\common\model;

use think\Model;
use custom\ConfigStatus as CS;


class Order extends Model
{

    // テーブル名
    protected $name = 'order';
    // 自動タイムスタンプ書き込みを有効にする
    protected $autoWriteTimestamp = 'int';
    // タイムスタンプフィールド名を定義
    protected $createTime = 'createtime';
    protected $updateTime = '';
    // 追加属性
    protected $append = [
        'status_text'
    ];

    public function getPriceAttr($value, $row)
    {
        return number_format($value);
    }

    public function getTotalPriceAttr($value, $row)
    {
        return number_format($value);
    }

    public function getPriceZgAttr($value, $row)
    {
        return number_format($value);
    }

    public function getStatusTextAttr($value, $row)
    {
        if(isset($row['status']))
          return CS::ORDER_STATUS_LIST[$row['status']] ?? '';
    }

    public function details()
    {
        return $this->hasMany('OrderDetails', 'order_id')->with('goods')->field('id,order_id,goods_id,title,image,price,num,color,specs_name,type,jan');
    }

    public function user()
    {
        return $this->belongsTo('User', 'user_id');
    }

    public function store()
    {
        return $this->belongsTo('Store', 'store_id')->field('id,name,address');
    }

}

<?php

namespace app\common\model;

use think\Model;


class OrderDetails extends Model
{

    // 表名
    protected $name = 'order_details';
    // 开启自动写入时间戳字段
    protected $autoWriteTimestamp = 'int';
    // 定义时间戳字段名
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

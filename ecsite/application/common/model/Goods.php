<?php

namespace app\common\model;

use think\Model;

// 公共模型定义
class Goods extends Model
{

    // テーブル名
    protected $name = 'goods';
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

    public function getSpecInfoAttr($value, $row)
    {
        if($value){
            $value = json_decode($value, true);
            foreach ($value as $key => $val) {
                $value[$key]['handle_price'] = number_format($val['price']);
            }
        }
        return $value;
    }

}

<?php

namespace app\admin\model;

use think\Model;


class BuyWay extends Model
{

    

    

    // テーブル名
    protected $name = 'buy_way';
    
    // タイムスタンプフィールドを自動書き込み
    protected $autoWriteTimestamp = 'integer';

    // タイムスタンプフィールド名を定義
    protected $createTime = 'createtime';
    protected $updateTime = false;
    protected $deleteTime = false;

    // 追加属性
    protected $append = [

    ];
    

    protected static function init()
    {
        self::afterInsert(function ($row) {
            if (!$row['weigh']) {
                $pk = $row->getPk();
                $row->getQuery()->where($pk, $row[$pk])->update(['weigh' => $row[$pk]]);
            }
        });
    }

    public function category()
    {
        return $this->belongsTo('\app\common\model\Category', 'category_id', 'id', [], 'LEFT')->setEagerlyType(0);
    }







}

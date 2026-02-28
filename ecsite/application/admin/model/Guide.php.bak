<?php

namespace app\admin\model;

use think\Model;


class Guide extends Model
{

    

    

    // 表名
    protected $name = 'guide';
    
    // 自动写入时间戳字段
    protected $autoWriteTimestamp = 'integer';

    // 定义时间戳字段名
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

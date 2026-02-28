<?php

namespace app\admin\model;

use think\Model;


class Goods extends Model
{

    

    

    // 表名
    protected $name = 'goods';
    
    // 自动写入时间戳字段
    protected $autoWriteTimestamp = 'integer';

    // 定义时间戳字段名
    protected $createTime = 'createtime';
    protected $updateTime = false;
    protected $deleteTime = false;

    // 追加属性
    protected $append = [
        'status_text'
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

    
    public function getStatusList()
    {
        return ['1' => __('Status 1'), '0' => __('Status 0')];
    }


    public function getStatusTextAttr($value, $data)
    {
        $value = $value ?: ($data['status'] ?? '');
        $list = $this->getStatusList();
        return $list[$value] ?? '';
    }

    public function category()
    {
        return $this->belongsTo('\app\common\model\Category', 'category_id', 'id', [], 'LEFT')->setEagerlyType(0);
    }

    public function second()
    {
        return $this->belongsTo('\app\common\model\Category', 'category_second', 'id', [], 'LEFT')->setEagerlyType(0);
    }

    public function three()
    {
        return $this->belongsTo('\app\common\model\Category', 'category_three', 'id', [], 'LEFT')->setEagerlyType(0);
    }


}

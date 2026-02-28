<?php

namespace app\admin\model;

use think\Model;
use traits\model\SoftDelete;

class Order extends Model
{

    use SoftDelete;

    

    // 表名
    protected $name = 'order';
    
    // 自动写入时间戳字段
    protected $autoWriteTimestamp = 'integer';

    // 定义时间戳字段名
    protected $createTime = 'createtime';
    protected $updateTime = false;
    protected $deleteTime = 'deletetime';

    // 追加属性
    protected $append = [
        'bank_account_type_text',
        'go_store_time_text',
        'pay_mode_text',
        'type_text'
    ];
    

    
    public function getBankAccountTypeList()
    {
        return ['1' => __('Bank_account_type 1'), '2' => __('Bank_account_type 2')];
    }

    public function getPayModeList()
    {
        return ['1' => __('Pay_mode 1'), '2' => __('Pay_mode 2')];
    }

    public function getTypeList()
    {
        return ['1' => __('Type 1'), '2' => __('Type 2')];
    }


    public function getBankAccountTypeTextAttr($value, $data)
    {
        $value = $value ?: ($data['bank_account_type'] ?? '');
        $list = $this->getBankAccountTypeList();
        return $list[$value] ?? '';
    }


    public function getGoStoreTimeTextAttr($value, $data)
    {
        $value = $value ?: ($data['go_store_time'] ?? '');
        return is_numeric($value) ? date("Y-m-d H:i:s", $value) : $value;
    }


    public function getPayModeTextAttr($value, $data)
    {
        $value = $value ?: ($data['pay_mode'] ?? '');
        $list = $this->getPayModeList();
        return $list[$value] ?? '';
    }


    public function getTypeTextAttr($value, $data)
    {
        $value = $value ?: ($data['type'] ?? '');
        $list = $this->getTypeList();
        return $list[$value] ?? '';
    }

    protected function setGoStoreTimeAttr($value)
    {
        return $value === '' ? null : ($value && !is_numeric($value) ? strtotime($value) : $value);
    }

    public function user()
    {
        return $this->belongsTo('\app\common\model\User', 'user_id', 'id', [], 'LEFT')->setEagerlyType(0);
    }


}

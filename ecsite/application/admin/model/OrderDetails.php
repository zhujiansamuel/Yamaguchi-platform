<?php

namespace app\admin\model;

use think\Model;


class OrderDetails extends Model
{

    

    

    // テーブル名
    protected $name = 'order_details';
    
    // タイムスタンプフィールドを自動書き込み
    protected $autoWriteTimestamp = 'integer';

    // タイムスタンプフィールド名を定義
    protected $createTime = 'createtime';
    protected $updateTime = false;
    protected $deleteTime = false;

    // 追加属性
    protected $append = [
        'type_text'
    ];
    

    
    public function getTypeList()
    {
        return ['1' => __('Type 1'), '2' => __('Type 2')];
    }


    public function getTypeTextAttr($value, $data)
    {
        $value = $value ?: ($data['type'] ?? '');
        $list = $this->getTypeList();
        return $list[$value] ?? '';
    }




}

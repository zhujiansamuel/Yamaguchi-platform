<?php

namespace app\admin\model;

use think\Model;


class Contactus extends Model
{

    

    

    // テーブル名
    protected $name = 'contactus';
    
    // タイムスタンプフィールドを自動書き込み
    protected $autoWriteTimestamp = 'integer';

    // タイムスタンプフィールド名を定義
    protected $createTime = 'createtime';
    protected $updateTime = false;
    protected $deleteTime = false;

    // 追加属性
    protected $append = [

    ];
    

    







}

<?php

namespace app\admin\validate;

use think\Validate;

class OrderDetails extends Validate
{
    /**
     * 検証ルール
     */
    protected $rule = [
    ];
    /**
     * メッセージ
     */
    protected $message = [
    ];
    /**
     * 検証シナリオ
     */
    protected $scene = [
        'add'  => [],
        'edit' => [],
    ];
    
}

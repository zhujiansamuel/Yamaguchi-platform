<?php

namespace app\admin\validate;

use think\Validate;

class User extends Validate
{
    /**
     * 検証ルール
     */
    protected $rule = [
        'username' => 'require|regex:\w{3,30}|unique:user',
        'nickname' => 'require|unique:user',
        'password' => 'regex:\S{6,30}',
        'email'    => 'require|email|unique:user',
        'mobile'   => 'unique:user'
    ];

    /**
     * フィールドの説明
     */
    protected $field = [
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
        'edit' => ['username', 'nickname', 'password', 'email', 'mobile'],
    ];

    public function __construct(array $rules = [], $message = [], $field = [])
    {
        $this->field = [
            'username' => __('Username'),
            'nickname' => __('Nickname'),
            'password' => __('Password'),
            'email'    => __('Email'),
            'mobile'   => __('Mobile')
        ];
        parent::__construct($rules, $message, $field);
    }

}

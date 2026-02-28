<?php

namespace app\admin\validate;

use think\Validate;

class AuthRule extends Validate
{

    /**
     * 正規表現
     */
    protected $regex = ['format' => '[a-z0-9_\/]+'];

    /**
     * 検証ルール
     */
    protected $rule = [
        'name'  => 'require|unique:AuthRule',
        'title' => 'require',
    ];

    /**
     * メッセージ
     */
    protected $message = [
        'name.format' => 'URLルールは小文字のアルファベットのみ使用可能、数値、アンダースコアと/から構成'
    ];

    /**
     * フィールドの説明
     */
    protected $field = [
    ];

    /**
     * 検証シナリオ
     */
    protected $scene = [
    ];

    public function __construct(array $rules = [], $message = [], $field = [])
    {
        $this->field = [
            'name'  => __('Name'),
            'title' => __('Title'),
        ];
        $this->message['name.format'] = __('Name only supports letters, numbers, underscore and slash');
        parent::__construct($rules, $message, $field);
    }

}

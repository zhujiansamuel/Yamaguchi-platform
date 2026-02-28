<?php

namespace app\admin\model;

use think\Cache;
use think\Model;

class AuthRule extends Model
{

    // 自動タイムスタンプ書き込みを有効にする
    protected $autoWriteTimestamp = 'int';
    // タイムスタンプフィールド名を定義
    protected $createTime = 'createtime';
    protected $updateTime = 'updatetime';
    // データ自動補完フィールド
    protected $insert = ['py', 'pinyin'];
    protected $update = ['py', 'pinyin'];
    // ピンインオブジェクト
    protected static $pinyin = null;

    protected static function init()
    {
        self::$pinyin = new \Overtrue\Pinyin\Pinyin('Overtrue\Pinyin\MemoryFileDictLoader');

        self::beforeWrite(function ($row) {
            if (isset($_POST['row']) && is_array($_POST['row']) && isset($_POST['row']['condition'])) {
                $originRow = $_POST['row'];
                $row['condition'] = $originRow['condition'] ?? '';
            }
        });
        self::afterWrite(function ($row) {
            Cache::rm('__menu__');
        });
    }

    public function getTitleAttr($value, $data)
    {
        return __($value);
    }

    public function getMenutypeList()
    {
        return ['addtabs' => __('Addtabs'), 'dialog' => __('Dialog'), 'ajax' => __('Ajax'), 'blank' => __('Blank')];
    }

    public function setPyAttr($value, $data)
    {
        if (isset($data['title']) && $data['title']) {
            return self::$pinyin->abbr(__($data['title']));
        }
        return '';
    }

    public function setPinyinAttr($value, $data)
    {
        if (isset($data['title']) && $data['title']) {
            return self::$pinyin->permalink(__($data['title']), '');
        }
        return '';
    }
}

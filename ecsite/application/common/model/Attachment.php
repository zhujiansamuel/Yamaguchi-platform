<?php

namespace app\common\model;

use think\Model;

class Attachment extends Model
{

    // 自動タイムスタンプ書き込みを有効にする
    protected $autoWriteTimestamp = 'int';
    // タイムスタンプフィールド名を定義
    protected $createTime = 'createtime';
    protected $updateTime = 'updatetime';
    // フィールドタイプを定義
    protected $type = [
    ];
    protected $append = [
        'thumb_style'
    ];

    protected static function init()
    {
        // すでにこのリソースがアップロードされている場合，それ以上記録しない
        self::beforeInsert(function ($model) {
            if (self::where('url', '=', $model['url'])->where('storage', $model['storage'])->find()) {
                return false;
            }
        });
        self::beforeWrite(function ($row) {
            if (isset($row['category']) && $row['category'] == 'unclassed') {
                $row['category'] = '';
            }
        });
    }

    public function setUploadtimeAttr($value)
    {
        return is_numeric($value) ? $value : strtotime($value);
    }

    public function getCategoryAttr($value)
    {
        return $value == '' ? 'unclassed' : $value;
    }

    public function setCategoryAttr($value)
    {
        return $value == 'unclassed' ? '' : $value;
    }

    /**
     * クラウドストレージのサムネイルスタイル文字列を取得
     */
    public function getThumbStyleAttr($value, $data)
    {
        if (!isset($data['storage']) || $data['storage'] == 'local') {
            return '';
        } else {
            $config = get_addon_config($data['storage']);
            if ($config && isset($config['thumbstyle'])) {
                return $config['thumbstyle'];
            }
        }
        return '';
    }

    /**
     * 取得Mimetypeリスト
     * @return array
     */
    public static function getMimetypeList()
    {
        $data = [
            "image/*"        => __("Image"),
            "audio/*"        => __("Audio"),
            "video/*"        => __("Video"),
            "text/*"         => __("Text"),
            "application/*"  => __("Application"),
            "zip,rar,7z,tar" => __("Zip"),
        ];
        return $data;
    }

    /**
     * 定義済みの添付ファイルカテゴリ一覧を取得
     * @return array
     */
    public static function getCategoryList()
    {
        $data = config('site.attachmentcategory') ?? [];
        foreach ($data as $index => &$datum) {
            $datum = __($datum);
        }
        $data['unclassed'] = __('Unclassed');
        return $data;
    }
}

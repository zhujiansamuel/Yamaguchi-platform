<?php

namespace app\common\model;

use think\Model;

class Version extends Model
{

    // 自動タイムスタンプ書き込みを有効にする
    protected $autoWriteTimestamp = 'int';
    // タイムスタンプフィールド名を定義
    protected $createTime = 'createtime';
    protected $updateTime = 'updatetime';
    // フィールドタイプを定義
    protected $type = [
    ];

    /**
     * バージョン番号をチェック
     *
     * @param string $version クライアントのバージョン番号
     * @return array
     */
    public static function check($version)
    {
        $versionlist = self::where('status', 'normal')->cache('__version__')->order('weigh desc,id desc')->select();
        foreach ($versionlist as $k => $v) {
            // バージョンが正常で、新バージョン番号が検証対象のバージョン番号と異なり、一致する旧バージョンが見つかった場合
            if ($v['status'] == 'normal' && $v['newversion'] !== $version && \fast\Version::check($version, $v['oldversion'])) {
                $updateversion = $v;
                break;
            }
        }
        if (isset($updateversion)) {
            $search = ['{version}', '{newversion}', '{downloadurl}', '{url}', '{packagesize}'];
            $replace = [$version, $updateversion['newversion'], $updateversion['downloadurl'], $updateversion['downloadurl'], $updateversion['packagesize']];
            $upgradetext = str_replace($search, $replace, $updateversion['content']);
            return [
                "enforce"     => $updateversion['enforce'],
                "version"     => $version,
                "newversion"  => $updateversion['newversion'],
                "downloadurl" => $updateversion['downloadurl'],
                "packagesize" => $updateversion['packagesize'],
                "upgradetext" => $upgradetext
            ];
        }
        return null;
    }
}

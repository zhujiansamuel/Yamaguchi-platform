<?php

namespace addons\summernote;

use think\Addons;

/**
 * Summernoteリッチテキストエディター
 */
class Summernote extends Addons
{

    /**
     * プラグインのインストール方法
     * @return bool
     */
    public function install()
    {
        return true;
    }

    /**
     * プラグインのアンインストール方法
     * @return bool
     */
    public function uninstall()
    {
        return true;
    }

    /**
     * @param $params
     */
    public function configInit(&$params)
    {
        $config = $this->getConfig();
        $params['summernote'] = [
            'classname'        => $config['classname'] ?? '.editor',
            'height'           => $config['height'] ?? 250,
            'minHeight'        => $config['minHeight'] ?? 250,
            'placeholder'      => $config['placeholder'] ?? '',
            'followingToolbar' => $config['followingToolbar'] ?? 0,
            'airMode'          => $config['airMode'] ?? 0,
            'toolbar'          => (array)json_decode($config['toolbar'] ?? '', true),
        ];
    }

}

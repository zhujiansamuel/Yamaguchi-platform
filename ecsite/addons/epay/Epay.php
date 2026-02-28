<?php

namespace addons\epay;

use addons\epay\library\Service;
use think\Addons;
use think\Config;
use think\Loader;

/**
 * WeChat・Alipay 統合プラグイン
 */
class Epay extends Addons
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
     * プラグイン有効化方法
     * @return bool
     */
    public function enable()
    {
        return true;
    }

    /**
     * プラグイン無効化方法
     * @return bool
     */
    public function disable()
    {
        return true;
    }

    // カスタム読み込みに対応
    public function epayConfigInit()
    {
        $this->actionBegin();
    }

    // プラグインメソッド読み込み開始
    public function addonActionBegin()
    {
        $this->actionBegin();
    }

    // モジュールコントローラーメソッド読み込み開始
    public function actionBegin()
    {
        //名前空間を追加
        if (!class_exists('\Yansongda\Pay\Pay')) {

            //SDKバージョン
            $version = Service::getSdkVersion();

            $libraryDir = ADDON_PATH . 'epay' . DS . 'library' . DS;
            Loader::addNamespace('Yansongda\Pay', $libraryDir . $version . DS . 'Yansongda' . DS . 'Pay' . DS);

            $checkArr = [
                '\Hyperf\Context\Context'     => 'context',
                '\Hyperf\Contract\Castable'   => 'contract',
                '\Hyperf\Engine\Constant'     => 'engine',
                '\Hyperf\Macroable\Macroable' => 'macroable',
                '\Hyperf\Pimple\Container'    => 'pimple',
                '\Hyperf\Utils\Arr'           => 'utils',
            ];
            foreach ($checkArr as $index => $item) {
                if (!class_exists($index)) {
                    Loader::addNamespace(substr($index, 1, strrpos($index, '\\') - 1), $libraryDir . 'hyperf' . DS . $item . DS . 'src' . DS);
                }
            }

            if (!class_exists('\Yansongda\Supports\Logger')) {
                Loader::addNamespace('Yansongda\Supports', $libraryDir . $version . DS . 'Yansongda' . DS . 'Supports' . DS);
            }

            // V3補助関数を読み込む必要があります
            if ($version == Service::SDK_VERSION_V3) {
                require_once $libraryDir . $version . DS . 'Yansongda' . DS . 'Pay' . DS . 'Functions.php';
            }
        }
    }
}

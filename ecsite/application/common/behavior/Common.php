<?php

namespace app\common\behavior;

use think\Config;
use think\Lang;
use think\Loader;

class Common
{

    public function appInit()
    {
        $allowLangList = Config::get('allow_lang_list') ?? ['zh-cn', 'en'];
        Lang::setAllowLangList($allowLangList);
    }

    public function appDispatch(&$dispatch)
    {
        $pathinfoArr = explode('/', request()->pathinfo());
        if (!Config::get('url_domain_deploy') && $pathinfoArr && in_array($pathinfoArr[0], ['index', 'api'])) {
            //もしindexまたはapiで始まる場合URLはルーティング検出を無効にする
            \think\App::route(false);
        }
    }

    public function moduleInit(&$request)
    {
        // 設定を行うmbstring文字エンコード
        mb_internal_encoding("UTF-8");

        // もし変更した場合index.phpエントリーパス，は手動で変更する必要がありますcdnurlの値
        $url = preg_replace("/\/(\w+)\.php$/i", '', $request->root());
        // 未設定の場合__CDN__自動的にマッチングして取得します
        if (is_null(Config::get('view_replace_str.__CDN__'))) {
            Config::set('view_replace_str.__CDN__', $url);
        }
        // 未設定の場合__PUBLIC__自動的にマッチングして取得します
        if (is_null(Config::get('view_replace_str.__PUBLIC__'))) {
            Config::set('view_replace_str.__PUBLIC__', $url . '/');
        }
        // 未設定の場合__ROOT__自動的にマッチングして取得します
        if (is_null(Config::get('view_replace_str.__ROOT__'))) {
            Config::set('view_replace_str.__ROOT__', preg_replace("/\/public\/$/", '', $url . '/'));
        }
        // 未設定の場合cdnurl自動的にマッチングして取得します
        if (is_null(Config::get('site.cdnurl'))) {
            Config::set('site.cdnurl', $url);
        }
        // 未設定の場合cdnurl自動的にマッチングして取得します
        if (is_null(Config::get('upload.cdnurl'))) {
            Config::set('upload.cdnurl', $url);
        }
        if (Config::get('app_debug')) {
            // デバッグモードの場合はversionを現在のタイムスタンプに設定してキャッシュを回避する
            Config::set('site.version', time());
            // 開発モードの場合は例外テンプレートを公式のものに変更する
            Config::set('exception_tmpl', THINK_PATH . 'tpl' . DS . 'think_exception.tpl');
        }
        // もし〜ならtraceモードかつAjaxの場合は trace を無効にするtrace
        if (Config::get('app_trace') && $request->isAjax()) {
            Config::set('app_trace', false);
        }
        // 多言語切り替え
        if (Config::get('lang_switch_on')) {
            $lang = $request->get('lang', '');
            if (preg_match("/^([a-zA-Z\-_]{2,10})\$/i", $lang)) {
                \think\Cookie::set('think_var', $lang);
            }
        }
        // Formエイリアス
        if (!class_exists('Form')) {
            class_alias('fast\\Form', 'Form');
        }
    }

    public function addonBegin(&$request)
    {
        // プラグイン言語パックを読み込む
        $lang = request()->langset();
        $lang = preg_match("/^([a-zA-Z\-_]{2,10})\$/i", $lang) ? $lang : 'zh-cn';
        Lang::load([
            APP_PATH . 'common' . DS . 'lang' . DS . $lang . DS . 'addon' . EXT,
        ]);
        $this->moduleInit($request);
    }
}

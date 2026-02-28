<?php

namespace app\index\controller;

use app\common\controller\Frontend;
use think\Lang;
use think\Loader;
use think\Response;

/**
 * Ajax非同期リクエストAPI
 * @internal
 */
class Ajax extends Frontend
{

    protected $noNeedLogin = ['lang', 'upload'];
    protected $noNeedRight = ['*'];
    protected $layout = '';

    /**
     * 言語パックを読み込む
     */
    public function lang()
    {
        $this->request->get(['callback' => 'define']);
        $header = ['Content-Type' => 'application/javascript'];
        if (!config('app_debug')) {
            $offset = 30 * 60 * 60 * 24; // 1か月間キャッシュ
            $header['Cache-Control'] = 'public';
            $header['Pragma'] = 'cache';
            $header['Expires'] = gmdate("D, d M Y H:i:s", time() + $offset) . " GMT";
        }

        $controllername = $this->request->get('controllername');
        $lang = $this->request->get('lang');
        if (!$lang || !in_array($lang, config('allow_lang_list')) || !$controllername || !preg_match("/^[a-z0-9_\.]+$/i", $controllername)) {
            return jsonp(['errmsg' => 'パラメーターエラー'], 200, [], ['json_encode_param' => JSON_FORCE_OBJECT | JSON_UNESCAPED_UNICODE]);
        }

        $controllername = input("controllername");
        $className = Loader::parseClass($this->request->module(), 'controller', $controllername, false);

        //対応するクラスが存在する場合のみ読み込む
        if (class_exists($className)) {
            $this->loadlang($controllername);
        }

        //強制出力JSON Object
        return jsonp(Lang::get(), 200, $header, ['json_encode_param' => JSON_FORCE_OBJECT | JSON_UNESCAPED_UNICODE]);
    }

    /**
     * 拡張子アイコンを生成
     */
    public function icon()
    {
        $suffix = $this->request->request("suffix");
        $suffix = $suffix ? $suffix : "FILE";
        $data = build_suffix_image($suffix);
        $header = ['Content-Type' => 'image/svg+xml'];
        $offset = 30 * 60 * 60 * 24; // 1か月間キャッシュ
        $header['Cache-Control'] = 'public';
        $header['Pragma'] = 'cache';
        $header['Expires'] = gmdate("D, d M Y H:i:s", time() + $offset) . " GMT";
        $response = Response::create($data, '', 200, $header);
        return $response;
    }

    /**
     * アップロードファイル
     */
    public function upload()
    {
        return action('api/common/upload');
    }

}

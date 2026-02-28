<?php

namespace app\common\controller;

use app\common\library\Auth;
use think\Config;
use think\Controller;
use think\Hook;
use think\Lang;
use think\Loader;
use think\Validate;

/**
 * フロントエンドコントローラー基底クラス
 */
class Frontend extends Controller
{

    /**
     * レイアウトテンプレート
     * @var string
     */
    protected $layout = '';

    /**
     * ログイン不要のメソッド,同時に権限認証も不要となる
     * @var array
     */
    protected $noNeedLogin = [];

    /**
     * 認証不要のメソッド,ただしログインは必要
     * @var array
     */
    protected $noNeedRight = [];

    /**
     * 権限Auth
     * @var Auth
     */
    protected $auth = null;

    public function _initialize()
    {
        //削除HTMLラベル
        $this->request->filter('trim,strip_tags,htmlspecialchars');
        $modulename = $this->request->module();
        $controllername = Loader::parseName($this->request->controller());
        $actionname = strtolower($this->request->action());

        // チェックIP許可するかどうか
        check_ip_allowed();

        // テンプレートレイアウトを使用している場合
        if ($this->layout) {
            $this->view->engine->layout('layout/' . $this->layout);
        }
        $this->auth = Auth::instance();

        // token
        $token = $this->request->server('HTTP_TOKEN', $this->request->request('token', \think\Cookie::get('token')));

        $path = str_replace('.', '/', $controllername) . '/' . $actionname;
        // 現在のリクエストのURI
        $this->auth->setRequestUri($path);
        // ログイン検証が必要かをチェック
        if (!$this->auth->match($this->noNeedLogin)) {
            //初期化
            $this->auth->init($token);
            //ログインしているか確認
            if (!$this->auth->isLogin()) {
                $this->error(__('Please login first'), '/');
            }
            // 権限検証が必要かを判定
            if (!$this->auth->match($this->noNeedRight)) {
                // コントローラーとメソッドに対応権限があるか判定
                if (!$this->auth->check($path)) {
                    $this->error(__('You have no permission'));
                }
            }
        } else {
            // が渡された場合のみtokenログイン状態を検証する
            if ($token) {
                $this->auth->init($token);
            }
        }

        $this->view->assign('user', $this->auth->getUser());

        // 言語検出
        $lang = $this->request->langset();
        $lang = preg_match("/^([a-zA-Z\-_]{2,10})\$/i", $lang) ? $lang : 'zh-cn';

        $site = Config::get("site");

        $upload = \app\common\model\Config::upload();

        // アップロード情報設定後
        Hook::listen("upload_config_init", $upload);

        // 設定情報
        $config = [
            'site'           => array_intersect_key($site, array_flip(['name', 'cdnurl', 'version', 'timezone', 'languages'])),
            'upload'         => $upload,
            'modulename'     => $modulename,
            'controllername' => $controllername,
            'actionname'     => $actionname,
            'jsname'         => 'frontend/' . str_replace('.', '/', $controllername),
            'moduleurl'      => rtrim(url("/{$modulename}", '', false), '/'),
            'language'       => $lang
        ];
        $config = array_merge($config, Config::get("view_replace_str"));

        Config::set('upload', array_merge(Config::get('upload'), $upload));

        // 設定情報の後
        Hook::listen("config_init", $config);
        // 現在のコントローラーの言語パックを読み込み
        $this->loadlang($controllername);
        $this->assign('site', $site);
        $this->assign('config', $config);
    }

    /**
     * 言語ファイルを読み込む
     * @param string $name
     */
    protected function loadlang($name)
    {
        $name = Loader::parseName($name);
        $name = preg_match("/^([a-zA-Z0-9_\.\/]+)\$/i", $name) ? $name : 'index';
        $lang = $this->request->langset();
        $lang = preg_match("/^([a-zA-Z\-_]{2,10})\$/i", $lang) ? $lang : 'zh-cn';
        Lang::load(APP_PATH . $this->request->module() . '/lang/' . $lang . '/' . str_replace('.', '/', $name) . '.php');
    }

    /**
     * 設定情報をレンダリング
     * @param mixed $name  キー名または配列
     * @param mixed $value 値
     */
    protected function assignconfig($name, $value = '')
    {
        $this->view->config = array_merge($this->view->config ? $this->view->config : [], is_array($name) ? $name : [$name => $value]);
    }

    /**
     * 更新Token
     */
    protected function token()
    {
        $token = $this->request->param('__token__');

        //検証Token
        if (!Validate::make()->check(['__token__' => $token], ['__token__' => 'require|token'])) {
            $this->error(__('Token verification error'), '', ['__token__' => $this->request->token()]);
        }

        //更新Token
        $this->request->token();
    }
}

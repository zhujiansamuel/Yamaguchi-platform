<?php

namespace app\common\controller;

use app\common\library\Auth;
use think\Config;
use think\exception\HttpResponseException;
use think\exception\ValidateException;
use think\Hook;
use think\Lang;
use think\Loader;
use think\Request;
use think\Response;
use think\Route;
use think\Validate;

/**
 * APIコントローラー基底クラス
 */
class Api
{

    /**
     * @var Request Request インスタンス
     */
    protected $request;

    /**
     * @var bool 検証失敗時に例外をスローするかどうか
     */
    protected $failException = false;

    /**
     * @var bool 一括検証を行うかどうか
     */
    protected $batchValidate = false;

    /**
     * @var array 前処理メソッド一覧
     */
    protected $beforeActionList = [];

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

    /**
     * デフォルトのレスポンス出力形式,サポートjson/xml
     * @var string
     */
    protected $responseType = 'json';

    /**
     * コンストラクタ
     * @access public
     * @param Request $request Request オブジェクト
     */
    public function __construct(Request $request = null)
    {
        $this->request = is_null($request) ? Request::instance() : $request;

        // コントローラー初期化
        $this->_initialize();

        // 前処理メソッド
        if ($this->beforeActionList) {
            foreach ($this->beforeActionList as $method => $options) {
                is_numeric($method) ?
                    $this->beforeAction($options) :
                    $this->beforeAction($method, $options);
            }
        }
    }

    /**
     * 初期化処理
     * @access protected
     */
    protected function _initialize()
    {
        //クロスドメインリクエストの検査
        check_cors_request();

        // チェックIP許可するかどうか
        check_ip_allowed();

        //削除HTMLラベル
        $this->request->filter('trim,strip_tags,htmlspecialchars');

        $this->auth = Auth::instance();

        $modulename = $this->request->module();
        $controllername = Loader::parseName($this->request->controller());
        $actionname = strtolower($this->request->action());

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
                $this->error(__('Please login first'), null, 401);
            }
            // 権限検証が必要かを判定
            if (!$this->auth->match($this->noNeedRight)) {
                // コントローラーとメソッドに対応権限があるか判定
                if (!$this->auth->check($path)) {
                    $this->error(__('You have no permission'), null, 403);
                }
            }
        } else {
            // が渡された場合のみtokenログイン状態を検証する
            if ($token) {
                $this->auth->init($token);
            }
        }

        $upload = \app\common\model\Config::upload();

        // アップロード情報設定後
        Hook::listen("upload_config_init", $upload);

        Config::set('upload', array_merge(Config::get('upload'), $upload));

        // 現在のコントローラーの言語パックを読み込み
        $this->loadlang($controllername);
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
     * 操作成功時に返すデータ
     * @param string $msg    メッセージ
     * @param mixed  $data   返却するデータ
     * @param int    $code   エラーコード，デフォルトは1
     * @param string $type   出力タイプ
     * @param array  $header 送信する Header 情報
     */
    protected function success($msg = '', $data = null, $code = 1, $type = null, array $header = [])
    {
        $this->result($msg, $data, $code, $type, $header);
    }

    /**
     * 操作失敗時に返されるデータ
     * @param string $msg    メッセージ
     * @param mixed  $data   返却するデータ
     * @param int    $code   エラーコード，デフォルトは0
     * @param string $type   出力タイプ
     * @param array  $header 送信する Header 情報
     */
    protected function error($msg = '', $data = null, $code = 0, $type = null, array $header = [])
    {
        $this->result($msg, $data, $code, $type, $header);
    }

    /**
     * ラップ済み API データをクライアントへ
     * @access protected
     * @param mixed  $msg    メッセージ
     * @param mixed  $data   返却するデータ
     * @param int    $code   エラーコード，デフォルトは0
     * @param string $type   出力タイプ，サポートjson/xml/jsonp
     * @param array  $header 送信する Header 情報
     * @return void
     * @throws HttpResponseException
     */
    protected function result($msg, $data = null, $code = 0, $type = null, array $header = [])
    {
        $result = [
            'code' => $code,
            'msg'  => $msg,
            'time' => Request::instance()->server('REQUEST_TIME'),
            'data' => $data,
        ];
        // タイプが未設定の場合はデフォルトタイプで判定します
        $type = $type ? : $this->responseType;

        if (isset($header['statuscode'])) {
            $code = $header['statuscode'];
            unset($header['statuscode']);
        } else {
            //ステータスコードが未設定,に基づいてcode値の判定
            $code = $code >= 1000 || $code < 200 ? 200 : $code;
        }
        $response = Response::create($result, $type, $code)->header($header);
        throw new HttpResponseException($response);
    }

    /**
     * 前処理
     * @access protected
     * @param string $method  前処理メソッド名
     * @param array  $options 呼び出しパラメーター ['only'=>[...]] または ['except'=>[...]]
     * @return void
     */
    protected function beforeAction($method, $options = [])
    {
        if (isset($options['only'])) {
            if (is_string($options['only'])) {
                $options['only'] = explode(',', $options['only']);
            }

            if (!in_array($this->request->action(), $options['only'])) {
                return;
            }
        } elseif (isset($options['except'])) {
            if (is_string($options['except'])) {
                $options['except'] = explode(',', $options['except']);
            }

            if (in_array($this->request->action(), $options['except'])) {
                return;
            }
        }

        call_user_func([$this, $method]);
    }

    /**
     * 検証失敗時に例外をスローするかどうかを設定
     * @access protected
     * @param bool $fail 例外をスローするかどうか
     * @return $this
     */
    protected function validateFailException($fail = true)
    {
        $this->failException = $fail;

        return $this;
    }

    /*
    
     $validate = [
        'category_id' => 'require,サービス分類を選択してください',
        'name' => 'require,連絡担当者名を入力してください',
        'mobile' => 'require,携帯番号を入力してください',
    ];

    $result = $this->verify($data, $validate);
     */
    protected function verify($data, $validate)
    {
        $verify = $msg = [];
        foreach ($validate as $key => $val) {
            list($one, $two) = explode(',', $val);
            $verify[$key] = $one;
            if(strpos($one, '|') !== false){
                $explode = explode('|', $one);
                $explodeMsg = explode('|', $two);
                foreach ($explode as $k => $v) {
                    $kItem = explode(':',$v)[0];
                    $msg[$key.'.'.$kItem] = $explodeMsg[$k] ?? '';
                }
            }else{
                $msg[$key] = $two;
            }
            
        }

        $result = $this->validate($data, $verify, $msg);
        if($result !== true){
            
            throw new \think\Exception($result);
        }
    }

    /**
     * データを検証
     * @access protected
     * @param array        $data     データ
     * @param string|array $validate バリデータ名または検証ルール配列
     * @param array        $message  メッセージ
     * @param bool         $batch    一括検証を行うかどうか
     * @param mixed        $callback コールバックメソッド（クロージャ）
     * @return array|string|true
     * @throws ValidateException
     */
    protected function validate($data, $validate, $message = [], $batch = false, $callback = null)
    {
        if (is_array($validate)) {
            $v = Loader::validate();
            $v->rule($validate);
        } else {
            // シーンをサポート
            if (strpos($validate, '.')) {
                list($validate, $scene) = explode('.', $validate);
            }

            $v = Loader::validate($validate);

            !empty($scene) && $v->scene($scene);
        }

        // 一括検証
        if ($batch || $this->batchValidate) {
            $v->batch(true);
        }
        // エラーメッセージを設定
        if (is_array($message)) {
            $v->message($message);
        }
        // コールバックによる検証を使用
        if ($callback && is_callable($callback)) {
            call_user_func_array($callback, [$v, &$data]);
        }

        if (!$v->check($data)) {
            if ($this->failException) {
                throw new ValidateException($v->getError());
            }

            return $v->getError();
        }

        return true;
    }

    /**
     * 更新Token
     */
    protected function token()
    {
        $token = $this->request->param('__token__');

        //検証Token
        if (!Validate::make()->check(['__token__' => $token], ['__token__' => 'require|token'])) {
            $this->error(__('Token verification error'), ['__token__' => $this->request->token()]);
        }

        //更新Token
        $this->request->token();
    }
}

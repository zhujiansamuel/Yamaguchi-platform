<?php

namespace app\common\library;

use app\common\model\User;
use app\common\model\UserRule;
use fast\Random;
use think\Config;
use think\Db;
use think\Exception;
use think\Hook;
use think\Request;
use think\Validate;

class Auth
{
    protected static $instance = null;
    protected $_error = '';
    protected $_logined = false;
    protected $_user = null;
    protected $_token = '';
    //Tokenデフォルト有効期間
    protected $keeptime = 2592000;
    protected $requestUri = '';
    protected $rules = [];
    //デフォルト設定
    protected $config = [];
    protected $options = [];
    protected $allowFields = ['id', 'name', 'persion_type', 'email', 'zip_code','address','szb','mobile','birthday','profile_type_locked','corporate_name','corporate_szb_1','corporate_szb_image_1','corporate_szb_image_2','corporate_szb_image_3'];

    public function __construct($options = [])
    {
        if ($config = Config::get('user')) {
            $this->config = array_merge($this->config, $config);
        }
        $this->options = array_merge($this->config, $options);
    }

    /**
     *
     * @param array $options パラメーター
     * @return Auth
     */
    public static function instance($options = [])
    {
        if (is_null(self::$instance)) {
            self::$instance = new static($options);
        }

        return self::$instance;
    }

    /**
     * 取得Userモデル
     * @return User
     */
    public function getUser()
    {
        return $this->_user;
    }

    /**
     * userモデルのプロパティを互換呼び出しuserモデルのプロパティ
     *
     * @param string $name
     * @return mixed
     */
    public function __get($name)
    {
        return $this->_user ? $this->_user->$name : null;
    }

    /**
     * userモデルのプロパティを互換呼び出しuserモデルのプロパティ
     */
    public function __isset($name)
    {
        return isset($this->_user) ? isset($this->_user->$name) : false;
    }

    /**
     * に基づいてToken初期化
     *
     * @param string $token Token
     * @return boolean
     */
    public function init($token)
    {
        if ($this->_logined) {
            return true;
        }
        if ($this->_error) {
            return false;
        }
        $data = Token::get($token);
        if (!$data) {
            return false;
        }
        $user_id = intval($data['user_id']);
        if ($user_id > 0) {
            $user = User::get($user_id);
            if (!$user) {
                $this->setError('Account not exist');
                return false;
            }
            if ($user['status'] != 'normal') {
                $this->setError('Account is locked');
                return false;
            }
            $this->_user = $user;
            $this->_logined = true;
            $this->_token = $token;

            //初期化成功イベント
            Hook::listen("user_init_successed", $this->_user);

            return true;
        } else {
            $this->setError('You are not logged in');
            return false;
        }
    }

    /**
     * ユーザー登録
     *
     * @param string $username ユーザー名
     * @param string $password パスワード
     * @param string $email    メールアドレス
     * @param string $mobile   携帯番号
     * @param array  $extend   拡張パラメータ
     * @return boolean
     */
    public function register($username, $password, $email = '', $mobile = '', $extend = [])
    {
        // ユーザー名を検証、ニックネーム、メールアドレス、携帯番号の存在を確認
        if (User::getByUsername($username)) {
            $this->setError('Username already exist');
            return false;
        }
        if ($email && User::getByEmail($email)) {
            $this->setError('Email already exist');
            return false;
        }


        $ip = request()->ip();
        $time = time();

        $data = [
            'username' => $username,
            'password' => $password,
            'email'    => $email,
            'mobile'   => $mobile,
            'level'    => 1,
            'score'    => 0,
            'avatar'   => '',
        ];
        $params = array_merge($data, [
            'nickname'  => preg_match("/^1[3-9]{1}\d{9}$/", $username) ? substr_replace($username, '****', 3, 4) : $username,
            'salt'      => Random::alnum(),
            'jointime'  => $time,
            'joinip'    => $ip,
            'logintime' => $time,
            'loginip'   => $ip,
            'prevtime'  => $time,
            'status'    => 'normal'
        ]);
        $params['password'] = $this->getEncryptPassword($password, $params['salt']);
        $params = array_merge($params, $extend);

        //アカウント登録時はトランザクションを開始する必要があります,不要データの発生を防ぐ
        Db::startTrans();
        try {
            $user = User::create($params, true);

            $this->_user = User::get($user->id);

            //設定を行うToken
            $this->_token = Random::uuid();
            Token::set($this->_token, $user->id, $this->keeptime);

            //ログイン状態を設定
            $this->_logined = true;

            //登録成功時のイベント
            Hook::listen("user_register_successed", $this->_user, $data);
            Db::commit();
        } catch (Exception $e) {
            $this->setError($e->getMessage());
            Db::rollback();
            return false;
        }
        return true;
    }

    /**
     * ユーザーログイン
     *
     * @param string $account  アカウント,ユーザー名、メールアドレス、携帯番号
     * @param string $password パスワード
     * @return boolean
     */
    public function login($account, $password)
    {
        $field = Validate::is($account, 'email') ? 'email' : (Validate::regex($account, '/^1\d{10}$/') ? 'mobile' : 'username');
        $user = User::get([$field => $account]);
        if (!$user) {
            $this->setError('Account is incorrect');
            return false;
        }

        if ($user->status != 'normal') {
            $this->setError('Account is locked');
            return false;
        }

        if ($user->loginfailure >= 10 && time() - $user->loginfailuretime < 86400) {
            $this->setError('Please try again after 1 day');
            return false;
        }

        if ($user->password != $this->getEncryptPassword($password, $user->salt)) {
            $user->save(['loginfailure' => $user->loginfailure + 1, 'loginfailuretime' => time()]);
            $this->setError('Password is incorrect');
            return false;
        }

        //会員を直接ログイン
        return $this->direct($user->id);
    }

    /**
     * ログアウト
     *
     * @return boolean
     */
    public function logout()
    {
        if (!$this->_logined) {
            $this->setError('You are not logged in');
            return false;
        }
        //ログインフラグを設定
        $this->_logined = false;
        //削除Token
        Token::delete($this->_token);
        //ログアウト成功時のイベント
        Hook::listen("user_logout_successed", $this->_user);
        return true;
    }

    /**
     * パスワードを変更
     * @param string $newpassword       新しいパスワード
     * @param string $oldpassword       旧パスワード
     * @param bool   $ignoreoldpassword 旧パスワードを無視
     * @return boolean
     */
    public function changepwd($newpassword, $oldpassword = '', $ignoreoldpassword = false)
    {
        if (!$this->_logined) {
            $this->setError('You are not logged in');
            return false;
        }
        //旧パスワードが正しいか判定
        if ($this->_user->password == $this->getEncryptPassword($oldpassword, $this->_user->salt) || $ignoreoldpassword) {
            Db::startTrans();
            try {
                $salt = Random::alnum();
                $newpassword = $this->getEncryptPassword($newpassword, $salt);
                $this->_user->save(['loginfailure' => 0, 'password' => $newpassword, 'salt' => $salt]);

                Token::delete($this->_token);
                //パスワード変更成功時のイベント
                Hook::listen("user_changepwd_successed", $this->_user);
                Db::commit();
            } catch (Exception $e) {
                Db::rollback();
                $this->setError($e->getMessage());
                return false;
            }
            return true;
        } else {
            $this->setError('Password is incorrect');
            return false;
        }
    }

    /**
     * アカウントに直接ログイン
     * @param int $user_id
     * @return boolean
     */
    public function direct($user_id)
    {
        $user = User::get($user_id);
        if ($user) {
            Db::startTrans();
            try {
                $ip = request()->ip();
                $time = time();

                //連続ログインおよび最大連続ログインを判定
                if ($user->logintime < \fast\Date::unixtime('day')) {
                    $user->successions = $user->logintime < \fast\Date::unixtime('day', -1) ? 1 : $user->successions + 1;
                    $user->maxsuccessions = max($user->successions, $user->maxsuccessions);
                }

                $user->prevtime = $user->logintime;
                //今回のログインのIPと時間を記録
                $user->loginip = $ip;
                $user->logintime = $time;
                //ログイン失敗回数をリセット
                $user->loginfailure = 0;

                $user->save();

                $this->_user = $user;

                $this->_token = Random::uuid();
                Token::set($this->_token, $user->id, $this->keeptime);

                $this->_logined = true;

                //ログイン成功時のイベント
                Hook::listen("user_login_successed", $this->_user);
                Db::commit();
            } catch (Exception $e) {
                Db::rollback();
                $this->setError($e->getMessage());
                return false;
            }
            return true;
        } else {
            return false;
        }
    }

    /**
     * 対応する権限があるかを検証
     * @param string $path   コントローラー/メソッド
     * @param string $module モジュール 默认为当前モジュール
     * @return boolean
     */
    public function check($path = null, $module = null)
    {
        if (!$this->_logined) {
            return false;
        }

        $ruleList = $this->getRuleList();
        $rules = [];
        foreach ($ruleList as $k => $v) {
            $rules[] = $v['name'];
        }
        $url = ($module ? $module : request()->module()) . '/' . (is_null($path) ? $this->getRequestUri() : $path);
        $url = strtolower(str_replace('.', '/', $url));
        return in_array($url, $rules);
    }

    /**
     * ログインしているか判定
     * @return boolean
     */
    public function isLogin()
    {
        if ($this->_logined) {
            return true;
        }
        return false;
    }

    /**
     * 現在の取得Token
     * @return string
     */
    public function getToken()
    {
        return $this->_token;
    }

    /**
     * 会員の基本情報を取得
     */
    public function getUserinfo()
    {
        $data = $this->_user->toArray();
        $allowFields = $this->getAllowFields();
        $userinfo = array_intersect_key($data, array_flip($allowFields));
        $userinfo = array_merge($userinfo, Token::get($this->_token));
        return $userinfo;
    }

    /**
     * 会員グループのルール一覧を取得
     * @return array|bool|\PDOStatement|string|\think\Collection
     */
    public function getRuleList()
    {
        if ($this->rules) {
            return $this->rules;
        }
        $group = $this->_user->group;
        if (!$group) {
            return [];
        }
        $rules = explode(',', $group->rules);
        $this->rules = UserRule::where('status', 'normal')->where('id', 'in', $rules)->field('id,pid,name,title,ismenu')->select();
        return $this->rules;
    }

    /**
     * 現在のリクエストの〜を取得URI
     * @return string
     */
    public function getRequestUri()
    {
        return $this->requestUri;
    }

    /**
     * 現在のリクエストのURI
     * @param string $uri
     */
    public function setRequestUri($uri)
    {
        $this->requestUri = $uri;
    }

    /**
     * 出力を許可する項目を取得
     * @return array
     */
    public function getAllowFields()
    {
        return $this->allowFields;
    }

    /**
     * 出力を許可する項目を設定
     * @param array $fields
     */
    public function setAllowFields($fields)
    {
        $this->allowFields = $fields;
    }

    /**
     * 指定した会員を削除
     * @param int $user_id 会員ID
     * @return boolean
     */
    public function delete($user_id)
    {
        $user = User::get($user_id);
        if (!$user) {
            return false;
        }
        Db::startTrans();
        try {
            // 会員を削除
            User::destroy($user_id);
            // 会員指定のすべてのToken
            Token::clear($user_id);

            Hook::listen("user_delete_successed", $user);
            Db::commit();
        } catch (Exception $e) {
            Db::rollback();
            $this->setError($e->getMessage());
            return false;
        }
        return true;
    }

    /**
     * パスワードを暗号化した文字列を取得
     * @param string $password パスワード
     * @param string $salt     ソルト
     * @return string
     */
    public function getEncryptPassword($password, $salt = '')
    {
        return md5(md5($password) . $salt);
    }

    /**
     * 現在のコントローラーとメソッドが渡された配列と一致するかを検出
     *
     * @param array $arr 権限検証が必要な配列
     * @return boolean
     */
    public function match($arr = [])
    {
        $request = Request::instance();
        $arr = is_array($arr) ? $arr : explode(',', $arr);
        if (!$arr) {
            return false;
        }
        $arr = array_map('strtolower', $arr);
        // 存在するかどうか
        if (in_array(strtolower($request->action()), $arr) || in_array('*', $arr)) {
            return true;
        }

        // 一致が見つかりません
        return false;
    }

    /**
     * セッション有効期間を設定
     * @param int $keeptime デフォルトは無期限
     */
    public function keeptime($keeptime = 0)
    {
        $this->keeptime = $keeptime;
    }

    /**
     * ユーザーデータをレンダリング
     * @param array  $datalist  2次元配列
     * @param mixed  $fields    読み込む項目リスト
     * @param string $fieldkey  レンダリングする項目
     * @param string $renderkey 結果項目
     * @return array
     */
    public function render(&$datalist, $fields = [], $fieldkey = 'user_id', $renderkey = 'userinfo')
    {
        $fields = !$fields ? ['id', 'nickname', 'level', 'avatar'] : (is_array($fields) ? $fields : explode(',', $fields));
        $ids = [];
        foreach ($datalist as $k => $v) {
            if (!isset($v[$fieldkey])) {
                continue;
            }
            $ids[] = $v[$fieldkey];
        }
        $list = [];
        if ($ids) {
            if (!in_array('id', $fields)) {
                $fields[] = 'id';
            }
            $ids = array_unique($ids);
            $selectlist = User::where('id', 'in', $ids)->column($fields);
            foreach ($selectlist as $k => $v) {
                $list[$v['id']] = $v;
            }
        }
        foreach ($datalist as $k => &$v) {
            $v[$renderkey] = $list[$v[$fieldkey]] ?? null;
        }
        unset($v);
        return $datalist;
    }

    /**
     * エラーメッセージを設定
     *
     * @param string $error エラーメッセージ
     * @return Auth
     */
    public function setError($error)
    {
        $this->_error = $error;
        return $this;
    }

    /**
     * エラーメッセージを取得
     * @return string
     */
    public function getError()
    {
        return $this->_error ? __($this->_error) : '';
    }
}

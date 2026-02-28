<?php

// +----------------------------------------------------------------------
// | ThinkPHP [ WE CAN DO IT JUST THINK IT ]
// +----------------------------------------------------------------------
// | Copyright (c) 2011 http://thinkphp.cn All rights reserved.
// +----------------------------------------------------------------------
// | Licensed ( http://www.apache.org/licenses/LICENSE-2.0 )
// +----------------------------------------------------------------------
// | Author: luofei614 <weibo.com/luofei614>
// +----------------------------------------------------------------------
// | 修正者: anuo (本権限クラスは元の3.2.3をベースに修正されたものです)
// +----------------------------------------------------------------------

namespace fast;

use think\Db;
use think\Config;
use think\Session;
use think\Request;

/**
 * 権限認証クラス
 * 機能特性：
 * 1，はルールに対して認証を行うものであり，ノードに対して認証を行うものではありません。ユーザーはノードをルール名として扱うことでノードに対する認証を実現できます。
 *      $auth=new Auth();  $auth->check('ルール名','ユーザーid')
 * 2，複数のルールを同時に認証できます，かつ複数ルール間の関係を設定できます（orまたはand）
 *      $auth=new Auth();  $auth->check('ルール1,ルール2','ユーザーid','and')
 *      3番目のパラメータがandのときは，ユーザーは同時にルール1とルール2の権限を持っている必要があります。 当3番目のパラメータがorのときは，ユーザーはいずれか一つの条件を満たせばよいことを意味します。デフォルトはor
 * 3，1人のユーザーは複数のユーザーグループに所属できます(think_auth_group_accessテーブル はユーザーが所属するユーザーグループを定義します)。各ユーザーグループがどのルールを持つかを設定する必要があります(think_auth_group はユーザーグループの権限を定義します)
 * 4，ルール式をサポート。
 *      でthink_auth_rule テーブルに1件のルールを定義し，conditionフィールドでルール式を定義できます。 例えば{score}>5  and {score}<100
 * ユーザーのスコアが5-100の範囲にある場合のみこのルールが通過します。
 */
class Auth
{

    /**
     * @var object オブジェクトインスタンス
     */
    protected static $instance;
    protected $rules = [];

    /**
     * 現在のリクエストインスタンス
     * @var Request
     */
    protected $request;
    //デフォルト設定
    protected $config = [
        'auth_on'           => 1, // 権限スイッチ
        'auth_type'         => 1, // 認証方式，1リアルタイム認証；2ログイン時認証。
        'auth_group'        => 'auth_group', // ユーザーグループテーブル名
        'auth_group_access' => 'auth_group_access', // ユーザー-ユーザー组关系表
        'auth_rule'         => 'auth_rule', // 権限ルールテーブル
        'auth_user'         => 'user', // ユーザー情報テーブル
    ];

    public function __construct()
    {
        if ($auth = Config::get('auth')) {
            $this->config = array_merge($this->config, $auth);
        }
        // 初期化request
        $this->request = Request::instance();
    }

    /**
     * 初期化
     * @access public
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
     * 権限チェック
     * @param string|array $name     検証が必要なルール一覧,カンマ区切りの権限ルールまたはインデックス配列をサポート
     * @param int          $uid      認証ユーザーのid
     * @param string       $relation もし 'or' いずれか1つのルールを満たせば検証を通過することを示す;もし 'and'すべてのルールを満たしてはじめて検証を通過できることを示す
     * @param string       $mode     検証を実行するモード,はurl,normal
     * @return bool 検証に合格した場合はtrue;失敗した場合はfalse
     */
    public function check($name, $uid, $relation = 'or', $mode = 'url')
    {
        if (!$this->config['auth_on']) {
            return true;
        }
        // ユーザーが検証する必要のあるすべての有効なルール一覧を取得
        $rulelist = $this->getRuleList($uid);
        if (in_array('*', $rulelist)) {
            return true;
        }

        if (is_string($name)) {
            $name = strtolower($name);
            if (strpos($name, ',') !== false) {
                $name = explode(',', $name);
            } else {
                $name = [$name];
            }
        }
        $list = []; //検証を通過したルール名を保存
        if ('url' == $mode) {
            $REQUEST = unserialize(strtolower(serialize($this->request->param())));
        }
        foreach ($rulelist as $rule) {
            $query = preg_replace('/^.+\?/U', '', $rule);
            if ('url' == $mode && $query != $rule) {
                parse_str($query, $param); //ルール内のparam
                $intersect = array_intersect_assoc($REQUEST, $param);
                $rule = preg_replace('/\?.*$/U', '', $rule);
                if (in_array($rule, $name) && $intersect == $param) {
                    //ノードが一致し、かつurlパラメーターが満たされる場合
                    $list[] = $rule;
                }
            } else {
                if (in_array($rule, $name)) {
                    $list[] = $rule;
                }
            }
        }
        if ('or' == $relation && !empty($list)) {
            return true;
        }
        $diff = array_diff($name, $list);
        if ('and' == $relation && empty($diff)) {
            return true;
        }

        return false;
    }

    /**
     * ユーザーに応じてidユーザーグループを取得,戻り値は配列
     * @param int $uid  ユーザーid
     * @return array       ユーザーが所属するユーザーグループ array(
     *                  array('uid'=>'ユーザーid','group_id'=>'ユーザー组id','name'=>'ユーザー组名称','rules'=>'ユーザー组拥有的规则id,複数を,で区切る'),
     *                  ...)
     */
    public function getGroups($uid)
    {
        static $groups = [];
        if (isset($groups[$uid])) {
            return $groups[$uid];
        }

        // クエリを実行
        $user_groups = Db::name($this->config['auth_group_access'])
            ->alias('aga')
            ->join('__' . strtoupper($this->config['auth_group']) . '__ ag', 'aga.group_id = ag.id', 'LEFT')
            ->field('aga.uid,aga.group_id,ag.id,ag.pid,ag.name,ag.rules')
            ->where("aga.uid='{$uid}' and ag.status='normal'")
            ->select();
        $groups[$uid] = $user_groups ?: [];
        return $groups[$uid];
    }

    /**
     * 権限ルール一覧を取得
     * @param int $uid ユーザーid
     * @return array
     */
    public function getRuleList($uid)
    {
        static $_rulelist = []; //ユーザーが検証を通過した権限一覧を保存
        if (isset($_rulelist[$uid])) {
            return $_rulelist[$uid];
        }
        if (2 == $this->config['auth_type'] && Session::has('_rule_list_' . $uid)) {
            return Session::get('_rule_list_' . $uid);
        }

        // ユーールノードを読み込む
        $ids = $this->getRuleIds($uid);
        if (empty($ids)) {
            $_rulelist[$uid] = [];
            return [];
        }

        // 絞り込み条件
        $where = [
            'status' => 'normal'
        ];
        if (!in_array('*', $ids)) {
            $where['id'] = ['in', $ids];
        }
        //ユーザーグループのすべての権限ルールを読み込む
        $this->rules = Db::name($this->config['auth_rule'])->where($where)->field('id,pid,condition,icon,name,title,ismenu')->select();

        //ルールをループ，結果を判定。
        $rulelist = []; //
        if (in_array('*', $ids)) {
            $rulelist[] = "*";
        }
        foreach ($this->rules as $rule) {
            //スーパー管理者は検証不要condition
            if (!empty($rule['condition']) && !in_array('*', $ids)) {
                //に基づいてcondition検証を行う
                $user = $this->getUserInfo($uid); //ユーザー情報を取得,一次元配列
                $nums = 0;
                $condition = str_replace(['&&', '||'], "\r\n", $rule['condition']);
                $condition = preg_replace('/\{(\w*?)\}/', '\\1', $condition);
                $conditionArr = explode("\r\n", $condition);
                foreach ($conditionArr as $index => $item) {
                    preg_match("/^(\w+)\s?([\>\<\=]+)\s?(.*)$/", trim($item), $matches);
                    if ($matches && isset($user[$matches[1]]) && version_compare($user[$matches[1]], $matches[3], $matches[2])) {
                        $nums++;
                    }
                }
                if ($conditionArr && ((stripos($rule['condition'], "||") !== false && $nums > 0) || count($conditionArr) == $nums)) {
                    $rulelist[$rule['id']] = strtolower($rule['name']);
                }
            } else {
                //存在していれば記録する
                $rulelist[$rule['id']] = strtolower($rule['name']);
            }
        }
        $_rulelist[$uid] = $rulelist;
        //ログイン認証の場合はルールリストを保存する必要があります
        if (2 == $this->config['auth_type']) {
            //ルールリストの結果を保存する場所session
            Session::set('_rule_list_' . $uid, $rulelist);
        }
        return array_unique($rulelist);
    }

    public function getRuleIds($uid)
    {
        //ユーザーが所属するユーザーグループを読み込む
        $groups = $this->getGroups($uid);
        $ids = []; //ユーザーが所属するユーザーグループで設定されたすべての権限ルールを保存id
        foreach ($groups as $g) {
            $ids = array_merge($ids, explode(',', trim($g['rules'], ',')));
        }
        $ids = array_unique($ids);
        return $ids;
    }

    /**
     * ユーザー情報を取得
     * @param int $uid ユーザーid
     * @return mixed
     */
    protected function getUserInfo($uid)
    {
        static $user_info = [];

        $user = Db::name($this->config['auth_user']);
        // ユーザーテーブルの主キーを取得
        $_pk = is_string($user->getPk()) ? $user->getPk() : 'uid';
        if (!isset($user_info[$uid])) {
            $user_info[$uid] = $user->where($_pk, $uid)->find();
        }

        return $user_info[$uid];
    }
}

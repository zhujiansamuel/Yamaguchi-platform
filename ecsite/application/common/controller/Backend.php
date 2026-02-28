<?php

namespace app\common\controller;

use app\admin\library\Auth;
use think\Config;
use think\Controller;
use think\Hook;
use think\Lang;
use think\Loader;
use think\Model;
use think\Session;
use fast\Tree;
use think\Validate;

/**
 * バックエンドコントローラー基底クラス
 */
class Backend extends Controller
{

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
     * レイアウトテンプレート
     * @var string
     */
    protected $layout = 'default';

    /**
     * 権限制御クラス
     * @var Auth
     */
    protected $auth = null;

    /**
     * モデルオブジェクト
     * @var \think\Model
     */
    protected $model = null;

    /**
     * クイック検索時に検索を実行するフィールド
     */
    protected $searchFields = 'id';

    /**
     * 関連クエリかどうか
     */
    protected $relationSearch = false;

    /**
     * データ制限を有効にするかどうか
     * サポートauth/personal
     * 権限に基づいて判定することを示します/個人のみ
     * デフォルトは無効,有効にする場合は必ずテーブルに存在していることを保証してくださいadmin_idフィールド
     */
    protected $dataLimit = false;

    /**
     * データ制限フィールド
     */
    protected $dataLimitField = 'admin_id';

    /**
     * データ制限が有効な場合に制限フィールド値を自動入力
     */
    protected $dataLimitFieldAutoFill = true;

    /**
     * 有効かどうかValidate検証
     */
    protected $modelValidate = false;

    /**
     * モデルシーン検証を有効にするかどうか
     */
    protected $modelSceneValidate = false;

    /**
     * Multiメソッドで一括変更可能なフィールド
     */
    protected $multiFields = 'status';

    /**
     * Selectpage表示可能なフィールド
     */
    protected $selectpageFields = '*';

    /**
     * フロントエンドから送信されてきた,除外が必要なフィールドデータ
     */
    protected $excludeFields = "";

    /**
     * インポートファイルの先頭行のタイプ
     * サポートcomment/name
     * コメントまたはフィールド名を表します
     */
    protected $importHeadType = 'comment';

    /**
     * バックエンドコントローラーのトレイトをインポートtraits
     */
    use \app\admin\library\traits\Backend;

    public function _initialize()
    {
        $modulename = $this->request->module();
        $controllername = Loader::parseName($this->request->controller());
        $actionname = strtolower($this->request->action());

        $path = str_replace('.', '/', $controllername) . '/' . $actionname;

        // かどうかを定義Addtabsリクエスト
        !defined('IS_ADDTABS') && define('IS_ADDTABS', (bool)input("addtabs"));

        // かどうかを定義Dialogリクエスト
        !defined('IS_DIALOG') && define('IS_DIALOG', (bool)input("dialog"));

        // かどうかを定義AJAXリクエスト
        !defined('IS_AJAX') && define('IS_AJAX', $this->request->isAjax());

        // チェックIP許可するかどうか
        check_ip_allowed();

        $this->auth = Auth::instance();

        // 現在のリクエストのURI
        $this->auth->setRequestUri($path);
        // ログイン検証が必要かをチェック
        if (!$this->auth->match($this->noNeedLogin)) {
            //ログインしているか確認
            if (!$this->auth->isLogin()) {
                Hook::listen('admin_nologin', $this);
                $url = Session::get('referer');
                $url = $url ? $url : $this->request->url();
                if (in_array($this->request->pathinfo(), ['/', 'index/index'])) {
                    $this->redirect('index/login', [], 302, ['referer' => $url]);
                    exit;
                }
                $this->error(__('Please login first'), url('index/login', ['url' => $url]));
            }
            // 権限検証が必要かを判定
            if (!$this->auth->match($this->noNeedRight)) {
                // コントローラーとメソッドに対応する権限があるかどうかを判定
                if (!$this->auth->check($path)) {
                    Hook::listen('admin_nopermission', $this);
                    $this->error(__('You have no permission'), '');
                }
            }
        }

        // タブでない場合にリダイレクト
        if (!$this->request->isPost() && !IS_AJAX && !IS_ADDTABS && !IS_DIALOG && input("ref") == 'addtabs') {
            $url = preg_replace_callback("/([\?|&]+)ref=addtabs(&?)/i", function ($matches) {
                return $matches[2] == '&' ? $matches[1] : '';
            }, $this->request->url());
            if (Config::get('url_domain_deploy')) {
                if (stripos($url, $this->request->server('SCRIPT_NAME')) === 0) {
                    $url = substr($url, strlen($this->request->server('SCRIPT_NAME')));
                }
                $url = url($url, '', false);
            }
            $this->redirect('index/index', [], 302, ['referer' => $url]);
            exit;
        }

        // パンくずナビゲーションデータを設定
        $breadcrumb = [];
        if (!IS_DIALOG && !config('fastadmin.multiplenav') && config('fastadmin.breadcrumb')) {
            $breadcrumb = $this->auth->getBreadCrumb($path);
            array_pop($breadcrumb);
        }
        $this->view->breadcrumb = $breadcrumb;

        // テンプレートレイアウトを使用している場合
        if ($this->layout) {
            $this->view->engine->layout('layout/' . $this->layout);
        }

        // 言語検出
        $lang = $this->request->langset();
        $lang = preg_match("/^([a-zA-Z\-_]{2,10})\$/i", $lang) ? $lang : 'zh-cn';

        $site = Config::get("site");

        $upload = \app\common\model\Config::upload();

        // アップロード情報設定後
        Hook::listen("upload_config_init", $upload);

        // 設定情報
        $config = [
            'site'           => array_intersect_key($site, array_flip(['name', 'indexurl', 'cdnurl', 'version', 'timezone', 'languages'])),
            'upload'         => $upload,
            'modulename'     => $modulename,
            'controllername' => $controllername,
            'actionname'     => $actionname,
            'jsname'         => 'backend/' . str_replace('.', '/', $controllername),
            'moduleurl'      => rtrim(url("/{$modulename}", '', false), '/'),
            'language'       => $lang,
            'referer'        => Session::get("referer")
        ];
        $config = array_merge($config, Config::get("view_replace_str"));

        Config::set('upload', array_merge(Config::get('upload'), $upload));

        // 設定情報の後
        Hook::listen("config_init", $config);
        //現在のコントローラーの言語パックを読み込み
        $this->loadlang($controllername);
        //サイト設定をレンダリング
        $this->assign('site', $site);
        //設定情報をレンダリング
        $this->assign('config', $config);
        //権限オブジェクトをレンダリング
        $this->assign('auth', $this->auth);
        //管理者オブジェクトをレンダリング
        $this->assign('admin', Session::get('admin'));
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
     * クエリに必要な条件を生成,ソート方法
     * @param mixed   $searchfields   クイック検索のフィールド
     * @param boolean $relationSearch 関連クエリかどうか
     * @return array
     */
    protected function buildparams($searchfields = null, $relationSearch = null)
    {
        $searchfields = is_null($searchfields) ? $this->searchFields : $searchfields;
        $relationSearch = is_null($relationSearch) ? $this->relationSearch : $relationSearch;
        $search = $this->request->get("search", '');
        $filter = $this->request->get("filter", '');
        $op = $this->request->get("op", '', 'trim');
        $sort = $this->request->get("sort", !empty($this->model) && $this->model->getPk() ? $this->model->getPk() : 'id');
        $order = $this->request->get("order", "DESC");
        $offset = max(0, $this->request->get("offset/d", 0));
        $limit = max(0, $this->request->get("limit/d", 0));
        $limit = $limit ?: 999999;
        //ページ番号の自動計算を追加
        $page = $limit ? intval($offset / $limit) + 1 : 1;
        if ($this->request->has("page")) {
            $page = max(0, $this->request->get("page/d", 1));
        }
        $this->request->get([config('paginate.var_page') => $page]);
        $filter = (array)json_decode($filter, true);
        $op = (array)json_decode($op, true);
        $filter = $filter ? $filter : [];
        if(isset($this->customizeSeach)){
            $customizeSeach = $this->customizeSeach;
            foreach ($customizeSeach as $key => $val) {
                if(isset($filter[$val])){
                    unset($filter[$val]);
                }
            }
        }
        $where = [];
        $alias = [];
        $bind = [];
        $name = '';
        $aliasName = '';
        if (!empty($this->model) && $relationSearch) {
            $name = $this->model->getTable();
            $alias[$name] = Loader::parseName(basename(str_replace('\\', '/', get_class($this->model))));
            $aliasName = $alias[$name] . '.';
        }
        $sortArr = explode(',', $sort);
        foreach ($sortArr as $index => & $item) {
            $item = stripos($item, ".") === false ? $aliasName . trim($item) : $item;
        }
        unset($item);
        $sort = implode(',', $sortArr);
        $adminIds = $this->getDataLimitAdminIds();
        if (is_array($adminIds)) {
            $where[] = [$aliasName . $this->dataLimitField, 'in', $adminIds];
        }
        if ($search) {
            $searcharr = is_array($searchfields) ? $searchfields : explode(',', $searchfields);
            foreach ($searcharr as $k => &$v) {
                $v = stripos($v, ".") === false ? $aliasName . $v : $v;
            }
            unset($v);
            $where[] = [implode("|", $searcharr), "LIKE", "%{$search}%"];
        }
        $index = 0;
        foreach ($filter as $k => $v) {
            if (!preg_match('/^[a-zA-Z0-9_\-\.]+$/', $k)) {
                continue;
            }
            $sym = $op[$k] ?? '=';
            if (stripos($k, ".") === false) {
                $k = $aliasName . $k;
            }
            $v = !is_array($v) ? trim($v) : $v;
            $sym = strtoupper($op[$k] ?? $sym);
            //nullnull と空文字列の特別処理
            if (!is_array($v)) {
                if (in_array(strtoupper($v), ['NULL', 'NOT NULL'])) {
                    $sym = strtoupper($v);
                }
                if (in_array($v, ['""', "''"])) {
                    $v = '';
                    $sym = '=';
                }
            }

            switch ($sym) {
                case '=':
                case '<>':
                    $where[] = [$k, $sym, (string)$v];
                    break;
                case 'LIKE':
                case 'NOT LIKE':
                case 'LIKE %...%':
                case 'NOT LIKE %...%':
                    $where[] = [$k, trim(str_replace('%...%', '', $sym)), "%{$v}%"];
                    break;
                case '>':
                case '>=':
                case '<':
                case '<=':
                    $where[] = [$k, $sym, intval($v)];
                    break;
                case 'FINDIN':
                case 'FINDINSET':
                case 'FIND_IN_SET':
                    $v = is_array($v) ? $v : explode(',', str_replace(' ', ',', $v));
                    $findArr = array_values($v);
                    foreach ($findArr as $idx => $item) {
                        $bindName = "item_" . $index . "_" . $idx;
                        $bind[$bindName] = $item;
                        $where[] = "FIND_IN_SET(:{$bindName}, `" . str_replace('.', '`.`', $k) . "`)";
                    }
                    break;
                case 'IN':
                case 'IN(...)':
                case 'NOT IN':
                case 'NOT IN(...)':
                    $where[] = [$k, str_replace('(...)', '', $sym), is_array($v) ? $v : explode(',', $v)];
                    break;
                case 'BETWEEN':
                case 'NOT BETWEEN':
                    $arr = array_slice(explode(',', $v), 0, 2);
                    if (stripos($v, ',') === false || !array_filter($arr, function ($v) {
                        return $v != '' && $v !== false && $v !== null;
                    })) {
                        continue 2;
                    }
                    //一方が空の場合に演算子を変更
                    if ($arr[0] === '') {
                        $sym = $sym == 'BETWEEN' ? '<=' : '>';
                        $arr = $arr[1];
                    } elseif ($arr[1] === '') {
                        $sym = $sym == 'BETWEEN' ? '>=' : '<';
                        $arr = $arr[0];
                    }
                    $where[] = [$k, $sym, $arr];
                    break;
                case 'RANGE':
                case 'NOT RANGE':
                    $v = str_replace(' - ', ',', $v);
                    $arr = array_slice(explode(',', $v), 0, 2);
                    if (stripos($v, ',') === false || !array_filter($arr)) {
                        continue 2;
                    }
                    //一方が空の場合に演算子を変更
                    if ($arr[0] === '') {
                        $sym = $sym == 'RANGE' ? '<=' : '>';
                        $arr = $arr[1];
                    } elseif ($arr[1] === '') {
                        $sym = $sym == 'RANGE' ? '>=' : '<';
                        $arr = $arr[0];
                    }
                    $tableArr = explode('.', $k);
                    if (count($tableArr) > 1 && $tableArr[0] != $name && !in_array($tableArr[0], $alias)
                        && !empty($this->model) && $this->relationSearch) {
                        //関連モデル下で時間が検索できないバグを修正BUG
                        $relation = Loader::parseName($tableArr[0], 1, false);
                        $alias[$this->model->$relation()->getTable()] = $tableArr[0];
                    }
                    $where[] = [$k, str_replace('RANGE', 'BETWEEN', $sym) . ' TIME', $arr];
                    break;
                case 'NULL':
                case 'IS NULL':
                case 'NOT NULL':
                case 'IS NOT NULL':
                    $where[] = [$k, strtolower(str_replace('IS ', '', $sym))];
                    break;
                default:
                    break;
            }
            $index++;
        }
        if (!empty($this->model)) {
            $this->model->alias($alias);
        }
        $model = $this->model;
        $where = function ($query) use ($where, $alias, $bind, &$model) {
            if (!empty($model)) {
                $model->alias($alias);
                $model->bind($bind);
            }
            foreach ($where as $k => $v) {
                if (is_array($v)) {
                    call_user_func_array([$query, 'where'], $v);
                } else {
                    $query->where($v);
                }
            }
        };
        return [$where, $sort, $order, $offset, $limit, $page, $alias, $bind];
    }

    /**
     * データ制限の管理者IDを取得ID
     * データ制限を無効にした場合に返されるのはnull
     * @return mixed
     */
    protected function getDataLimitAdminIds()
    {
        if (!$this->dataLimit) {
            return null;
        }
        if ($this->auth->isSuperAdmin()) {
            return null;
        }
        $adminIds = [];
        if (in_array($this->dataLimit, ['auth', 'personal'])) {
            $adminIds = $this->dataLimit == 'auth' ? $this->auth->getChildrenAdminIds(true) : [$this->auth->id];
        }
        return $adminIds;
    }

    /**
     * Selectpageの実装方法
     *
     * 現在のメソッドはあくまで汎用的な検索マッチングであり,必要に応じてこのメソッドをオーバーライドして、独自の検索ロジックを実装してください,$where要件に応じて記述すれば問題ありません
     * ここではすべてのパラメーターを例示しています，そのため少し複雑です，実装としては、実際には数行だけで簡単に実現できます
     *
     */
    protected function selectpage()
    {
        //フィルターメソッドを設定
        $this->request->filter(['trim', 'strip_tags', 'htmlspecialchars']);

        //検索キーワード,クライアント側の入力はスペースで区切ります,ここでは配列として受け取ります
        $word = (array)$this->request->request("q_word/a");
        //現在のページ
        $page = $this->request->request("pageNumber");
        //ページサイズ
        $pagesize = $this->request->request("pageSize");
        //検索条件
        $andor = $this->request->request("andOr", "and", "strtoupper");
        //ソート方法
        $orderby = (array)$this->request->request("orderBy/a");
        //表示フィールド
        $field = $this->request->request("showField");
        //主キー
        $primarykey = $this->request->request("keyField");
        //主キー値
        $primaryvalue = $this->request->request("keyValue");
        //検索フィールド
        $searchfield = (array)$this->request->request("searchField/a");
        //カスタム検索条件
        $custom = (array)$this->request->request("custom/a");
        foreach ($custom as $key => $val) {
            if($key == 'extend'){
                list($keys, $values) = $this->{$val}($custom);
                $custom[$keys] = $values;
                unset($custom[$key]);
            }
        }
        //ツリー構造で返すかどうか
        $istree = $this->request->request("isTree", 0);
        $ishtml = $this->request->request("isHtml", 0);
        if ($istree) {
            $word = [];
            $pagesize = 999999;
        }
        $order = [];
        foreach ($orderby as $k => $v) {
            $order[$v[0]] = $v[1];
        }
        $field = $field ? $field : 'name';

        //存在する場合primaryvalue,現在は初期値の受け渡しであることを示します
        if ($primaryvalue !== null) {
            $where = [$primarykey => ['in', $primaryvalue]];
            $pagesize = 999999;
        } else {
            $where = function ($query) use ($word, $andor, $field, $searchfield, $custom) {
                $logic = $andor == 'AND' ? '&' : '|';
                $searchfield = is_array($searchfield) ? implode($logic, $searchfield) : $searchfield;
                $searchfield = str_replace(',', $logic, $searchfield);
                $word = array_filter(array_unique($word));
                if (count($word) == 1) {
                    $query->where($searchfield, "like", "%" . reset($word) . "%");
                } else {
                    $query->where(function ($query) use ($word, $searchfield) {
                        foreach ($word as $index => $item) {
                            $query->whereOr(function ($query) use ($item, $searchfield) {
                                $query->where($searchfield, "like", "%{$item}%");
                            });
                        }
                    });
                }
                if ($custom && is_array($custom)) {
                    foreach ($custom as $k => $v) {
                        if (is_array($v) && 2 == count($v)) {
                            $query->where($k, trim($v[0]), $v[1]);
                        } else {
                            $query->where($k, '=', $v);
                        }
                    }
                }
            };
        }
        $adminIds = $this->getDataLimitAdminIds();
        if (is_array($adminIds)) {
            $this->model->where($this->dataLimitField, 'in', $adminIds);
        }
        $list = [];
        $total = $this->model->where($where)->count();
        if ($total > 0) {
            if (is_array($adminIds)) {
                $this->model->where($this->dataLimitField, 'in', $adminIds);
            }

            $fields = is_array($this->selectpageFields) ? $this->selectpageFields : ($this->selectpageFields && $this->selectpageFields != '*' ? explode(',', $this->selectpageFields) : []);

            //存在する場合primaryvalue,現在は初期値の受け渡しであることを示します,選択順にソートします
            if ($primaryvalue !== null && preg_match("/^[a-z0-9_\-]+$/i", $primarykey)) {
                $primaryvalue = array_unique(is_array($primaryvalue) ? $primaryvalue : explode(',', $primaryvalue));
                //カスタムの修正data-primary-key文字列内容である場合，ソートフィールドに引用符を付与します
                $primaryvalue = array_map(function ($value) {
                    return '\'' . $value . '\'';
                }, $primaryvalue);

                $primaryvalue = implode(',', $primaryvalue);

                $this->model->orderRaw("FIELD(`{$primarykey}`, {$primaryvalue})");
            } else {
                $this->model->order($order);
            }

            $datalist = $this->model->where($where)
                ->page($page, $pagesize)
                ->select();

            foreach ($datalist as $index => $item) {
                unset($item['password'], $item['salt']);
                if ($this->selectpageFields == '*') {
                    $result = [
                        $primarykey => $item[$primarykey] ?? '',
                        $field      => $item[$field] ?? '',
                    ];
                } else {
                    $result = array_intersect_key(($item instanceof Model ? $item->toArray() : (array)$item), array_flip($fields));
                    if(isset($this->selectpageFieldsJson)){
                        $result[$this->selectpageFieldsJson] = json_decode($result[$this->selectpageFieldsJson], true);
                    }
                }
                $result['pid'] = isset($item['pid']) ? $item['pid'] : (isset($item['parent_id']) ? $item['parent_id'] : 0);
                $result = array_map("htmlentities", $result);
                $list[] = $result;
            }
            if ($istree && !$primaryvalue) {
                $tree = Tree::instance();
                $tree->init(collection($list)->toArray(), 'pid');
                $list = $tree->getTreeList($tree->getTreeArray(0), $field);
                if (!$ishtml) {
                    foreach ($list as &$item) {
                        $item = str_replace('&nbsp;', ' ', $item);
                    }
                    unset($item);
                }
            }
        }
        //ここでは必ずlistこのフィールドを返す必要があります,totalは任意です,もしtotal<=listの件数,の場合はページネーションボタンを非表示にします
        return json(['list' => $list, 'total' => $total]);
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

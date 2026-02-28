<?php

namespace fast;

use think\Config;

/**
 * 汎用ツリークラス
 * @author XiaoYao <476552238li@gmail.com>
 */
class Tree
{
    protected static $instance;
    //デフォルト設定
    protected $config = [];
    public $options = [];

    /**
     * ツリー構造を生成するために必要な2次元配列
     * @var array
     */
    public $arr = [];

    /**
     * ツリー構造生成用の装飾記号，画像に置き換えることも可能
     * @var array
     */
    public $icon = array('│', '├', '└');
    public $nbsp = "&nbsp;";
    public $pidname = 'pid';

    public function __construct($options = [])
    {
        if ($config = Config::get('tree')) {
            $this->options = array_merge($this->config, $config);
        }
        $this->options = array_merge($this->config, $options);
    }

    /**
     * 初期化
     * @access public
     * @param array $options パラメーター
     * @return Tree
     */
    public static function instance($options = [])
    {
        if (is_null(self::$instance)) {
            self::$instance = new static($options);
        }

        return self::$instance;
    }

    /**
     * 初期化メソッド
     * @param array  $arr     2次元配列，例えば：
     *      array(
     *      1 => array('id'=>'1','pid'=>0,'name'=>'第1階層カテゴリ1'),
     *      2 => array('id'=>'2','pid'=>0,'name'=>'第1階層カテゴリ2'),
     *      3 => array('id'=>'3','pid'=>1,'name'=>'第2階層カテゴリ1'),
     *      4 => array('id'=>'4','pid'=>1,'name'=>'第2階層メニュー2'),
     *      5 => array('id'=>'5','pid'=>2,'name'=>'第2階層メニュー3'),
     *      6 => array('id'=>'6','pid'=>3,'name'=>'第3階層メニュー1'),
     *      7 => array('id'=>'7','pid'=>3,'name'=>'第3階層メニュー2')
     *      )
     * @param string $pidname 親フィールド名
     * @param string $nbsp    空白プレースホルダー
     * @return Tree
     */
    public function init($arr = [], $pidname = null, $nbsp = null)
    {
        $this->arr = $arr;
        if (!is_null($pidname)) {
            $this->pidname = $pidname;
        }
        if (!is_null($nbsp)) {
            $this->nbsp = $nbsp;
        }
        return $this;
    }

    /**
     * 子レベル配列を取得
     * @param int
     * @return array
     */
    public function getChild($myid)
    {
        $newarr = [];
        foreach ($this->arr as $value) {
            if (!isset($value['id'])) {
                continue;
            }
            if ($value[$this->pidname] == $myid) {
                $newarr[$value['id']] = $value;
            }
        }
        return $newarr;
    }

    /**
     * 指定ノードのすべての子ノードを読み込む
     * @param int     $myid     ノードID
     * @param boolean $withself 自身を含めるかどうか
     * @return array
     */
    public function getChildren($myid, $withself = false)
    {
        $newarr = [];
        foreach ($this->arr as $value) {
            if (!isset($value['id'])) {
                continue;
            }
            if ((string)$value[$this->pidname] == (string)$myid) {
                $newarr[] = $value;
                $newarr = array_merge($newarr, $this->getChildren($value['id']));
            } elseif ($withself && (string)$value['id'] == (string)$myid) {
                $newarr[] = $value;
            }
        }
        return $newarr;
    }

    /**
     * 指定ノードのすべての子ノードを読み込むID
     * @param int     $myid     ノードID
     * @param boolean $withself 自身を含めるかどうか
     * @return array
     */
    public function getChildrenIds($myid, $withself = false)
    {
        $childrenlist = $this->getChildren($myid, $withself);
        $childrenids = [];
        foreach ($childrenlist as $k => $v) {
            $childrenids[] = $v['id'];
        }
        return $childrenids;
    }

    /**
     * 現在位置の親レベル配列を取得
     * @param int
     * @return array
     */
    public function getParent($myid)
    {
        $pid = 0;
        $newarr = [];
        foreach ($this->arr as $value) {
            if (!isset($value['id'])) {
                continue;
            }
            if ($value['id'] == $myid) {
                $pid = $value[$this->pidname];
                break;
            }
        }
        if ($pid) {
            foreach ($this->arr as $value) {
                if ($value['id'] == $pid) {
                    $newarr[] = $value;
                    break;
                }
            }
        }
        return $newarr;
    }

    /**
     * 現在位置のすべての親レベル配列を取得
     * @param int
     * @param bool $withself 自分自身を含めるかどうか
     * @return array
     */
    public function getParents($myid, $withself = false)
    {
        $pid = 0;
        $newarr = [];
        foreach ($this->arr as $value) {
            if (!isset($value['id'])) {
                continue;
            }
            if ($value['id'] == $myid) {
                if ($withself) {
                    $newarr[] = $value;
                }
                $pid = $value[$this->pidname];
                break;
            }
        }
        if ($pid) {
            $arr = $this->getParents($pid, true);
            $newarr = array_merge($arr, $newarr);
        }
        return $newarr;
    }

    /**
     * 指定ノードのすべての親ノードを読み込むID
     * @param int     $myid
     * @param boolean $withself
     * @return array
     */
    public function getParentsIds($myid, $withself = false)
    {
        $parentlist = $this->getParents($myid, $withself);
        $parentsids = [];
        foreach ($parentlist as $k => $v) {
            $parentsids[] = $v['id'];
        }
        return $parentsids;
    }

    /**
     * ツリー構造Option
     * @param int    $myid        これを取得することを表すID配下のすべての子レベル
     * @param string $itemtpl     項目テンプレート 例："<option value=@id @selected @disabled>@spacer@name</option>"
     * @param mixed  $selectedids 選択されたID，ツリー型セレクトボックスを作成するときなどに使用
     * @param mixed  $disabledids 無効化されたID，ツリー型セレクトボックスを作成するときなどに使用
     * @param string $itemprefix  各項目のプレフィックス
     * @param string $toptpl      トップレベルメニューのテンプレート
     * @return string
     */
    public function getTree($myid, $itemtpl = "<option value=@id @selected @disabled>@spacer@name</option>", $selectedids = '', $disabledids = '', $itemprefix = '', $toptpl = '')
    {
        $ret = '';
        $number = 1;
        $childs = $this->getChild($myid);
        if ($childs) {
            $total = count($childs);
            foreach ($childs as $value) {
                $id = $value['id'];
                $j = $k = '';
                if ($number == $total) {
                    $j .= $this->icon[2];
                    $k = $itemprefix ? $this->nbsp : '';
                } else {
                    $j .= $this->icon[1];
                    $k = $itemprefix ? $this->icon[0] : '';
                }
                $spacer = $itemprefix ? $itemprefix . $j : '';
                $selected = $selectedids && in_array($id, (is_array($selectedids) ? $selectedids : explode(',', $selectedids))) ? 'selected' : '';
                $disabled = $disabledids && in_array($id, (is_array($disabledids) ? $disabledids : explode(',', $disabledids))) ? 'disabled' : '';
                $value = array_merge($value, array('selected' => $selected, 'disabled' => $disabled, 'spacer' => $spacer));
                $value = array_combine(array_map(function ($k) {
                    return '@' . $k;
                }, array_keys($value)), $value);
                $nstr = strtr((($value["@{$this->pidname}"] == 0 || $this->getChild($id)) && $toptpl ? $toptpl : $itemtpl), $value);
                $ret .= $nstr;
                $ret .= $this->getTree($id, $itemtpl, $selectedids, $disabledids, $itemprefix . $k . $this->nbsp, $toptpl);
                $number++;
            }
        }
        return $ret;
    }

    /**
     * ツリー構造UL
     * @param int    $myid        これを取得することを表すID配下のすべての子レベル
     * @param string $itemtpl     項目テンプレート 例："<li value=@id @selected @disabled>@name @childlist</li>"
     * @param string $selectedids 選択中ID
     * @param string $disabledids 無効ID
     * @param string $wraptag     子リストのラップ用タグ
     * @param string $wrapattr    子リストのラップ用属性
     * @return string
     */
    public function getTreeUl($myid, $itemtpl, $selectedids = '', $disabledids = '', $wraptag = 'ul', $wrapattr = '')
    {
        $str = '';
        $childs = $this->getChild($myid);
        if ($childs) {
            foreach ($childs as $value) {
                $id = $value['id'];
                unset($value['child']);
                $selected = $selectedids && in_array($id, (is_array($selectedids) ? $selectedids : explode(',', $selectedids))) ? 'selected' : '';
                $disabled = $disabledids && in_array($id, (is_array($disabledids) ? $disabledids : explode(',', $disabledids))) ? 'disabled' : '';
                $value = array_merge($value, array('selected' => $selected, 'disabled' => $disabled));
                $value = array_combine(array_map(function ($k) {
                    return '@' . $k;
                }, array_keys($value)), $value);
                $nstr = strtr($itemtpl, $value);
                $childdata = $this->getTreeUl($id, $itemtpl, $selectedids, $disabledids, $wraptag, $wrapattr);
                $childlist = $childdata ? "<{$wraptag} {$wrapattr}>" . $childdata . "</{$wraptag}>" : "";
                $str .= strtr($nstr, array('@childlist' => $childlist));
            }
        }
        return $str;
    }

    /**
     * メニューデータ
     * @param int    $myid
     * @param string $itemtpl
     * @param mixed  $selectedids
     * @param mixed  $disabledids
     * @param string $wraptag
     * @param string $wrapattr
     * @param int    $deeplevel
     * @return string
     */
    public function getTreeMenu($myid, $itemtpl, $selectedids = '', $disabledids = '', $wraptag = 'ul', $wrapattr = '', $deeplevel = 0)
    {
        $str = '';
        $childs = $this->getChild($myid);
        if ($childs) {
            foreach ($childs as $value) {
                $id = $value['id'];
                unset($value['child']);
                $selected = in_array($id, (is_array($selectedids) ? $selectedids : explode(',', $selectedids))) ? 'selected' : '';
                $disabled = in_array($id, (is_array($disabledids) ? $disabledids : explode(',', $disabledids))) ? 'disabled' : '';
                $value = array_merge($value, array('selected' => $selected, 'disabled' => $disabled));
                $value = array_combine(array_map(function ($k) {
                    return '@' . $k;
                }, array_keys($value)), $value);
                $bakvalue = array_intersect_key($value, array_flip(['@url', '@caret', '@class']));
                $value = array_diff_key($value, $bakvalue);
                $nstr = strtr($itemtpl, $value);
                $value = array_merge($value, $bakvalue);
                $childdata = $this->getTreeMenu($id, $itemtpl, $selectedids, $disabledids, $wraptag, $wrapattr, $deeplevel + 1);
                $childlist = $childdata ? "<{$wraptag} {$wrapattr}>" . $childdata . "</{$wraptag}>" : "";
                $childlist = strtr($childlist, array('@class' => $childdata ? 'last' : ''));
                $value = array(
                    '@childlist' => $childlist,
                    '@url'       => $childdata || !isset($value['@url']) ? "javascript:;" : $value['@url'],
                    '@addtabs'   => $childdata || !isset($value['@url']) ? "" : (stripos($value['@url'], "?") !== false ? "&" : "?") . "ref=addtabs",
                    '@caret'     => ($childdata && (!isset($value['@badge']) || !$value['@badge']) ? '<i class="fa fa-angle-left"></i>' : ''),
                    '@badge'     => $value['@badge'] ?? '',
                    '@class'     => ($selected ? ' active' : '') . ($disabled ? ' disabled' : '') . ($childdata ? ' treeview' . (config('fastadmin.show_submenu') ? ' treeview-open' : '') : ''),
                );
                $str .= strtr($nstr, $value);
            }
        }
        return $str;
    }

    /**
     * 特殊
     * @param integer $myid        検索対象のID
     * @param string  $itemtpl1    第1種HTMLコード方式
     * @param string  $itemtpl2    第2種HTMLコード方式
     * @param mixed   $selectedids デフォルト選択
     * @param mixed   $disabledids 無効化
     * @param string  $itemprefix  プレフィックス
     * @return string
     */
    public function getTreeSpecial($myid, $itemtpl1, $itemtpl2, $selectedids = 0, $disabledids = 0, $itemprefix = '')
    {
        $ret = '';
        $number = 1;
        $childs = $this->getChild($myid);
        if ($childs) {
            $total = count($childs);
            foreach ($childs as $id => $value) {
                $j = $k = '';
                if ($number == $total) {
                    $j .= $this->icon[2];
                    $k = $itemprefix ? $this->nbsp : '';
                } else {
                    $j .= $this->icon[1];
                    $k = $itemprefix ? $this->icon[0] : '';
                }
                $spacer = $itemprefix ? $itemprefix . $j : '';
                $selected = $selectedids && in_array($id, (is_array($selectedids) ? $selectedids : explode(',', $selectedids))) ? 'selected' : '';
                $disabled = $disabledids && in_array($id, (is_array($disabledids) ? $disabledids : explode(',', $disabledids))) ? 'disabled' : '';
                $value = array_merge($value, array('selected' => $selected, 'disabled' => $disabled, 'spacer' => $spacer));
                $value = array_combine(array_map(function ($k) {
                    return '@' . $k;
                }, array_keys($value)), $value);
                $nstr = strtr(!isset($value['@disabled']) || !$value['@disabled'] ? $itemtpl1 : $itemtpl2, $value);

                $ret .= $nstr;
                $ret .= $this->getTreeSpecial($id, $itemtpl1, $itemtpl2, $selectedids, $disabledids, $itemprefix . $k . $this->nbsp);
                $number++;
            }
        }
        return $ret;
    }

    /**
     *
     * ツリー配列を取得
     * @param string $myid       検索対象のID
     * @param string $itemprefix プレフィックス
     * @return array
     */
    public function getTreeArray($myid, $itemprefix = '')
    {
        $childs = $this->getChild($myid);
        $n = 0;
        $data = [];
        $number = 1;
        if ($childs) {
            $total = count($childs);
            foreach ($childs as $id => $value) {
                $j = $k = '';
                if ($number == $total) {
                    $j .= $this->icon[2];
                    $k = $itemprefix ? $this->nbsp : '';
                } else {
                    $j .= $this->icon[1];
                    $k = $itemprefix ? $this->icon[0] : '';
                }
                $spacer = $itemprefix ? $itemprefix . $j : '';
                $value['spacer'] = $spacer;
                $data[$n] = $value;
                $data[$n]['childlist'] = $this->getTreeArray($id, $itemprefix . $k . $this->nbsp);
                $n++;
                $number++;
            }
        }
        return $data;
    }

    /**
     * をgetTreeArrayの結果を2次元配列として返す
     * @param array  $data
     * @param string $field
     * @return array
     */
    public function getTreeList($data = [], $field = 'name')
    {
        $arr = [];
        foreach ($data as $k => $v) {
            $childlist = $v['childlist'] ?? [];
            unset($v['childlist']);
            $v[$field] = $v['spacer'] . ' ' . $v[$field];
            $v['haschild'] = $childlist ? 1 : 0;
            if ($v['id']) {
                $arr[] = $v;
            }
            if ($childlist) {
                $arr = array_merge($arr, $this->getTreeList($childlist, $field));
            }
        }
        return $arr;
    }
}

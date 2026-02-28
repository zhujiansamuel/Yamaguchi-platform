<?php

namespace app\common\library;

use app\admin\model\AuthRule;
use fast\Tree;
use think\addons\Service;
use think\Db;
use think\Exception;
use think\exception\PDOException;

class Menu
{

    /**
     * メニューを作成
     * @param array $menu
     * @param mixed $parent 親クラスのnameまたはpid
     */
    public static function create($menu = [], $parent = 0)
    {
        $old = [];
        self::menuUpdate($menu, $old, $parent);

        //メニュー更新処理
        $info = debug_backtrace(DEBUG_BACKTRACE_IGNORE_ARGS, 2)[1];
        preg_match('/addons\\\\([a-z0-9]+)\\\\/i', $info['class'], $matches);
        if ($matches && isset($matches[1])) {
            Menu::refresh($matches[1], $menu);
        }
    }

    /**
     * メニューを削除
     * @param string $name ルールname
     * @return boolean
     */
    public static function delete($name)
    {
        $ids = self::getAuthRuleIdsByName($name);
        if (!$ids) {
            return false;
        }
        AuthRule::destroy($ids);
        return true;
    }

    /**
     * メニューを有効化
     * @param string $name
     * @return boolean
     */
    public static function enable($name)
    {
        $ids = self::getAuthRuleIdsByName($name);
        if (!$ids) {
            return false;
        }
        AuthRule::where('id', 'in', $ids)->update(['status' => 'normal']);
        return true;
    }

    /**
     * メニューを無効化
     * @param string $name
     * @return boolean
     */
    public static function disable($name)
    {
        $ids = self::getAuthRuleIdsByName($name);
        if (!$ids) {
            return false;
        }
        AuthRule::where('id', 'in', $ids)->update(['status' => 'hidden']);
        return true;
    }

    /**
     * メニューをアップグレード
     * @param string $name プラグイン名
     * @param array  $menu 新規メニュー
     * @return bool
     */
    public static function upgrade($name, $menu)
    {
        $ids = self::getAuthRuleIdsByName($name);
        $old = AuthRule::where('id', 'in', $ids)->select();
        $old = collection($old)->toArray();
        $old = array_column($old, null, 'name');

        Db::startTrans();
        try {
            self::menuUpdate($menu, $old);
            $ids = [];
            foreach ($old as $index => $item) {
                if (!isset($item['keep'])) {
                    $ids[] = $item['id'];
                }
            }
            if ($ids) {
                //旧バージョンのメニューは削除処理が必要
                $config = Service::config($name);
                $menus = $config['menus'] ?? [];
                $where = ['id' => ['in', $ids]];
                if ($menus) {
                    //必ず旧バージョンのメニューである必要があります,ユーザーが独自に作成したメニューは除外可能
                    $where['name'] = ['in', $menus];
                }
                AuthRule::where($where)->delete();
            }

            Db::commit();
        } catch (PDOException $e) {
            Db::rollback();
            return false;
        }

        Menu::refresh($name, $menu);
        return true;
    }

    /**
     * プラグインメニュー設定キャッシュを更新
     * @param string $name
     * @param array  $menu
     */
    public static function refresh($name, $menu = [])
    {
        if (!$menu) {
            // $menu空の場合は初回インストールを示す，初回インストール時はプラグインメニュー識別キャッシュを更新する必要があります
            $menuIds = Menu::getAuthRuleIdsByName($name);
            $menus = Db::name("auth_rule")->where('id', 'in', $menuIds)->column('name');
        } else {
            // 新しいメニューキャッシュを更新
            $getMenus = function ($menu) use (&$getMenus) {
                $result = [];
                foreach ($menu as $index => $item) {
                    $result[] = $item['name'];
                    $result = array_merge($result, isset($item['sublist']) && is_array($item['sublist']) ? $getMenus($item['sublist']) : []);
                }
                return $result;
            };
            $menus = $getMenus($menu);
        }

        //新しいプラグインコアメニューキャッシュを更新
        Service::config($name, ['menus' => $menus]);
    }

    /**
     * 指定した名称のメニュールールをエクスポート
     * @param string $name
     * @return array
     */
    public static function export($name)
    {
        $ids = self::getAuthRuleIdsByName($name);
        if (!$ids) {
            return [];
        }
        $menuList = [];
        $menu = AuthRule::getByName($name);
        if ($menu) {
            $ruleList = collection(AuthRule::where('id', 'in', $ids)->select())->toArray();
            $menuList = Tree::instance()->init($ruleList)->getTreeArray($menu['id']);
        }
        return $menuList;
    }

    /**
     * メニューアップグレード
     * @param array $newMenu
     * @param array $oldMenu
     * @param int   $parent
     * @throws Exception
     */
    private static function menuUpdate($newMenu, &$oldMenu, $parent = 0)
    {
        if (!is_numeric($parent)) {
            $parentRule = AuthRule::getByName($parent);
            $pid = $parentRule ? $parentRule['id'] : 0;
        } else {
            $pid = $parent;
        }
        $allow = array_flip(['file', 'name', 'title', 'url', 'icon', 'condition', 'remark', 'ismenu', 'menutype', 'extend', 'weigh', 'status']);
        foreach ($newMenu as $k => $v) {
            $hasChild = isset($v['sublist']) && $v['sublist'];
            $data = array_intersect_key($v, $allow);
            $data['ismenu'] = $data['ismenu'] ?? ($hasChild ? 1 : 0);
            $data['icon'] = $data['icon'] ?? ($hasChild ? 'fa fa-list' : 'fa fa-circle-o');
            $data['pid'] = $pid;
            $data['status'] = $data['status'] ?? 'normal';
            if (!isset($oldMenu[$data['name']])) {
                $menu = AuthRule::create($data);
            } else {
                $menu = $oldMenu[$data['name']];
                //旧メニューを更新
                AuthRule::update($data, ['id' => $menu['id']]);
                $oldMenu[$data['name']]['keep'] = true;
            }
            if ($hasChild) {
                self::menuUpdate($v['sublist'], $oldMenu, $menu['id']);
            }
        }
    }

    /**
     * 名称に基づきルールを取得IDS
     * @param string $name
     * @return array
     */
    public static function getAuthRuleIdsByName($name)
    {
        $ids = [];
        $menu = AuthRule::getByName($name);
        if ($menu) {
            // 結果セットを必ず配列に変換する必要がある
            $ruleList = collection(AuthRule::order('weigh', 'desc')->field('id,pid,name')->select())->toArray();
            // メニューデータを構築
            $ids = Tree::instance()->init($ruleList)->getChildrenIds($menu['id'], true);
        }
        return $ids;
    }

}

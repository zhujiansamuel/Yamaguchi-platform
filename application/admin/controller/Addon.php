<?php

namespace app\admin\controller;

use app\common\controller\Backend;
use fast\Http;
use think\addons\AddonException;
use think\addons\Service;
use think\Cache;
use think\Config;
use think\Db;
use think\Exception;

/**
 * プラグイン管理
 *
 * @icon   fa fa-cube
 * @remark オンラインでインストール可能、アンインストール、無効化、有効化、設定、プラグインのアップグレード，プラグインをアップグレードする前に必ずバックアップを取ってください。
 */
class Addon extends Backend
{
    protected $model = null;
    protected $noNeedRight = ['get_table_list'];

    public function _initialize()
    {
        parent::_initialize();
        if (!$this->auth->isSuperAdmin() && in_array($this->request->action(), ['install', 'uninstall', 'local', 'upgrade', 'authorization', 'testdata'])) {
            $this->error(__('Access is allowed only to the super management group'));
        }
    }

    /**
     * プラグイン一覧
     */
    public function index()
    {
        $addons = get_addon_list();
        foreach ($addons as $k => &$v) {
            $config = get_addon_config($v['name']);
            $v['config'] = $config ? 1 : 0;
            $v['url'] = str_replace($this->request->server('SCRIPT_NAME'), '', $v['url']);
        }
        $this->assignconfig(['addons' => $addons, 'api_url' => config('fastadmin.api_url'), 'faversion' => config('fastadmin.version'), 'domain' => request()->host(true)]);
        return $this->view->fetch();
    }

    /**
     * 設定
     */
    public function config($name = null)
    {
        $name = $name ? $name : $this->request->get("name");
        if (!$name) {
            $this->error(__('Parameter %s can not be empty', 'name'));
        }
        if (!preg_match("/^[a-zA-Z0-9]+$/", $name)) {
            $this->error(__('Addon name incorrect'));
        }
        $info = get_addon_info($name);
        $config = get_addon_fullconfig($name);
        if (!$info) {
            $this->error(__('Addon not exists'));
        }
        if ($this->request->isPost()) {
            $params = $this->request->post("row/a", [], 'trim');
            if ($params) {
                foreach ($config as $k => &$v) {
                    if (isset($params[$v['name']])) {
                        if ($v['type'] == 'array') {
                            $params[$v['name']] = is_array($params[$v['name']]) ? $params[$v['name']] : (array)json_decode($params[$v['name']], true);
                            $value = $params[$v['name']];
                        } else {
                            $value = is_array($params[$v['name']]) ? implode(',', $params[$v['name']]) : $params[$v['name']];
                        }
                        $v['value'] = $value;
                    }
                }
                try {
                    $addon = get_addon_instance($name);
                    //プラグインのカスタム設定ロジックを実装
                    if (method_exists($addon, 'config')) {
                        $addon->config($name, $config);
                    } else {
                        //設定ファイルを更新
                        set_addon_fullconfig($name, $config);
                        Service::refresh();
                    }
                } catch (Exception $e) {
                    $this->error(__($e->getMessage()));
                }
                $this->success();
            }
            $this->error(__('Parameter %s can not be empty', ''));
        }
        $tips = [];
        $groupList = [];
        $ungroupList = [];
        foreach ($config as $index => &$item) {
            //グループが設定されている場合
            if (isset($item['group']) && $item['group']) {
                if (!in_array($item['group'], $groupList)) {
                    $groupList["custom" . (count($groupList) + 1)] = $item['group'];
                }
            } elseif ($item['name'] != '__tips__') {
                $ungroupList[] = $item['name'];
            }
            if ($item['name'] == '__tips__') {
                $tips = $item;
                unset($config[$index]);
            }
        }
        if ($ungroupList) {
            $groupList['other'] = 'その他';
        }
        $this->view->assign("groupList", $groupList);
        $this->view->assign("addon", ['info' => $info, 'config' => $config, 'tips' => $tips]);
        $configFile = ADDON_PATH . $name . DS . 'config.html';
        $viewFile = is_file($configFile) ? $configFile : '';
        return $this->view->fetch($viewFile);
    }

    /**
     * インストール
     */
    public function install()
    {
        $name = $this->request->post("name");
        $force = (int)$this->request->post("force");
        if (!$name) {
            $this->error(__('Parameter %s can not be empty', 'name'));
        }
        if (!preg_match("/^[a-zA-Z0-9]+$/", $name)) {
            $this->error(__('Addon name incorrect'));
        }

        $info = [];
        try {
            $uid = $this->request->post("uid");
            $token = $this->request->post("token");
            $version = $this->request->post("version");
            $faversion = $this->request->post("faversion");
            $extend = [
                'uid'       => $uid,
                'token'     => $token,
                'version'   => $version,
                'faversion' => $faversion
            ];
            $info = Service::install($name, $force, $extend);
        } catch (AddonException $e) {
            $this->result($e->getData(), $e->getCode(), __($e->getMessage()));
        } catch (Exception $e) {
            $this->error(__($e->getMessage()), $e->getCode());
        }
        $this->success(__('Install successful'), '', ['addon' => $info]);
    }

    /**
     * アンインストール
     */
    public function uninstall()
    {
        $name = $this->request->post("name");
        $force = (int)$this->request->post("force");
        $droptables = (int)$this->request->post("droptables");
        if (!$name) {
            $this->error(__('Parameter %s can not be empty', 'name'));
        }
        if (!preg_match("/^[a-zA-Z0-9]+$/", $name)) {
            $this->error(__('Addon name incorrect'));
        }
        //デバッグを有効にし、かつスーパー管理者のみ関連データベースを削除できます
        $tables = [];
        if ($droptables && Config::get("app_debug") && $this->auth->isSuperAdmin()) {
            $tables = get_addon_tables($name);
        }
        try {
            Service::uninstall($name, $force);
            if ($tables) {
                $prefix = Config::get('database.prefix');
                //プラグイン関連テーブルを削除
                foreach ($tables as $index => $table) {
                    //プラグイン識別子以外のテーブル名を無視
                    if (!preg_match("/^{$prefix}{$name}/", $table)) {
                        continue;
                    }
                    Db::execute("DROP TABLE IF EXISTS `{$table}`");
                }
            }
        } catch (AddonException $e) {
            $this->result($e->getData(), $e->getCode(), __($e->getMessage()));
        } catch (Exception $e) {
            $this->error(__($e->getMessage()));
        }
        $this->success(__('Uninstall successful'));
    }

    /**
     * 無効化/有効化
     */
    public function state()
    {
        $name = $this->request->post("name");
        $action = $this->request->post("action");
        $force = (int)$this->request->post("force");
        if (!$name) {
            $this->error(__('Parameter %s can not be empty', 'name'));
        }
        if (!preg_match("/^[a-zA-Z0-9]+$/", $name)) {
            $this->error(__('Addon name incorrect'));
        }
        try {
            $action = $action == 'enable' ? $action : 'disable';
            //有効化・無効化メソッドを呼び出す、無効化のメソッド
            Service::$action($name, $force);
            Cache::rm('__menu__');
        } catch (AddonException $e) {
            $this->result($e->getData(), $e->getCode(), __($e->getMessage()));
        } catch (Exception $e) {
            $this->error(__($e->getMessage()));
        }
        $this->success(__('Operate successful'));
    }

    /**
     * ローカルアップロード
     */
    public function local()
    {
        Config::set('default_return_type', 'json');

        $info = [];
        $file = $this->request->file('file');
        try {
            $uid = $this->request->post("uid");
            $token = $this->request->post("token");
            $faversion = $this->request->post("faversion");
            $force = $this->request->post("force");
            if (!$uid || !$token) {
                throw new Exception(__('Please login and try to install'));
            }
            $extend = [
                'uid'       => $uid,
                'token'     => $token,
                'faversion' => $faversion
            ];
            $info = Service::local($file, $extend, $force);
        } catch (AddonException $e) {
            $this->result($e->getData(), $e->getCode(), __($e->getMessage()));
        } catch (Exception $e) {
            $this->error(__($e->getMessage()));
        }
        $this->success(__('Offline installed tips'), '', ['addon' => $info]);
    }

    /**
     * プラグインを更新
     */
    public function upgrade()
    {
        $name = $this->request->post("name");
        $addonTmpDir = RUNTIME_PATH . 'addons' . DS;
        if (!$name) {
            $this->error(__('Parameter %s can not be empty', 'name'));
        }
        if (!preg_match("/^[a-zA-Z0-9]+$/", $name)) {
            $this->error(__('Addon name incorrect'));
        }
        if (!is_dir($addonTmpDir)) {
            @mkdir($addonTmpDir, 0755, true);
        }

        $info = [];
        try {
            $info = get_addon_info($name);
            $uid = $this->request->post("uid");
            $token = $this->request->post("token");
            $version = $this->request->post("version");
            $faversion = $this->request->post("faversion");
            $extend = [
                'uid'        => $uid,
                'token'      => $token,
                'version'    => $version,
                'oldversion' => $info['version'] ?? '',
                'faversion'  => $faversion
            ];
            //更新メソッドを呼び出す
            $info = Service::upgrade($name, $extend);
            Cache::rm('__menu__');
        } catch (AddonException $e) {
            $this->result($e->getData(), $e->getCode(), __($e->getMessage()));
        } catch (Exception $e) {
            $this->error(__($e->getMessage()));
        }
        $this->success(__('Operate successful'), '', ['addon' => $info]);
    }

    /**
     * テストデータ
     */
    public function testdata()
    {
        $name = $this->request->post("name");
        if (!$name) {
            $this->error(__('Parameter %s can not be empty', 'name'));
        }
        if (!preg_match("/^[a-zA-Z0-9]+$/", $name)) {
            $this->error(__('Addon name incorrect'));
        }

        try {
            Service::importsql($name, 'testdata.sql');
        } catch (AddonException $e) {
            $this->result($e->getData(), $e->getCode(), __($e->getMessage()));
        } catch (Exception $e) {
            $this->error(__($e->getMessage()), $e->getCode());
        }
        $this->success(__('Import successful'), '');
    }

    /**
     * インストール済みプラグイン
     */
    public function downloaded()
    {
        $offset = (int)$this->request->get("offset");
        $limit = (int)$this->request->get("limit");
        $filter = $this->request->get("filter", '');
        $search = $this->request->get("search", '', 'strip_tags,htmlspecialchars');
        $onlineaddons = $this->getAddonList();
        $filter = (array)json_decode($filter, true);
        $addons = get_addon_list();
        $list = [];
        foreach ($addons as $k => $v) {
            if ($search && stripos($v['name'], $search) === false && stripos($v['title'], $search) === false && stripos($v['intro'], $search) === false) {
                continue;
            }

            if (isset($onlineaddons[$v['name']])) {
                $v = array_merge($v, $onlineaddons[$v['name']]);
                $v['price'] = '-';
            } else {
                $v['category_id'] = 0;
                $v['flag'] = '';
                $v['banner'] = '';
                $v['image'] = '';
                $v['demourl'] = '';
                $v['price'] = __('None');
                $v['screenshots'] = [];
                $v['releaselist'] = [];
                $v['url'] = addon_url($v['name']);
                $v['url'] = str_replace($this->request->server('SCRIPT_NAME'), '', $v['url']);
            }
            $v['createtime'] = filemtime(ADDON_PATH . $v['name']);
            if ($filter && isset($filter['category_id']) && is_numeric($filter['category_id']) && $filter['category_id'] != $v['category_id']) {
                continue;
            }
            $list[] = $v;
        }
        $total = count($list);
        if ($limit) {
            $list = array_slice($list, $offset, $limit);
        }
        $result = array("total" => $total, "rows" => $list);

        $callback = $this->request->get('callback') ? "jsonp" : "json";
        return $callback($result);
    }

    /**
     * チェック
     */
    public function isbuy()
    {
        $name = $this->request->post("name");
        $uid = $this->request->post("uid");
        $token = $this->request->post("token");
        $version = $this->request->post("version");
        $faversion = $this->request->post("faversion");
        $extend = [
            'uid'       => $uid,
            'token'     => $token,
            'version'   => $version,
            'faversion' => $faversion
        ];
        try {
            $result = Service::isBuy($name, $extend);
        } catch (Exception $e) {
            $this->error(__($e->getMessage()));
        }
        return json($result);
    }

    /**
     * 認証を更新
     */
    public function authorization()
    {
        $params = [
            'uid'       => $this->request->post('uid'),
            'token'     => $this->request->post('token'),
            'faversion' => $this->request->post('faversion'),
        ];
        try {
            Service::authorization($params);
        } catch (Exception $e) {
            $this->error(__($e->getMessage()));
        }
        $this->success(__('Operate successful'));
    }

    /**
     * プラグイン関連テーブルを取得
     */
    public function get_table_list()
    {
        $name = $this->request->post("name");
        if (!preg_match("/^[a-zA-Z0-9]+$/", $name)) {
            $this->error(__('Addon name incorrect'));
        }
        $tables = get_addon_tables($name);
        $prefix = Config::get('database.prefix');
        foreach ($tables as $index => $table) {
            //プラグイン識別子以外のテーブル名を無視
            if (!preg_match("/^{$prefix}{$name}/", $table)) {
                unset($tables[$index]);
            }
        }
        $tables = array_values($tables);
        $this->success('', null, ['tables' => $tables]);
    }

    protected function getAddonList()
    {
        $onlineaddons = Cache::get("onlineaddons");
        if (!is_array($onlineaddons) && config('fastadmin.api_url')) {
            $onlineaddons = [];
            $params = [
                'uid'       => $this->request->post('uid'),
                'token'     => $this->request->post('token'),
                'version'   => config('fastadmin.version'),
                'faversion' => config('fastadmin.version'),
            ];
            $json = [];
            try {
                $json = Service::addons($params);
            } catch (\Exception $e) {

            }
            $rows = $json['rows'] ?? [];
            foreach ($rows as $index => $row) {
                if (!isset($row['name'])) {
                    continue;
                }
                $onlineaddons[$row['name']] = $row;
            }
            Cache::set("onlineaddons", $onlineaddons, 600);
        }
        return $onlineaddons;
    }

}

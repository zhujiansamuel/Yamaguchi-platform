<?php

namespace app\admin\controller;

use app\common\controller\Backend;
use app\common\exception\UploadException;
use app\common\library\Upload;
use fast\Random;
use think\addons\Service;
use think\Cache;
use think\Config;
use think\Db;
use think\Lang;
use think\Loader;
use think\Response;
use think\Validate;

/**
 * Ajax非同期リクエストAPI
 * @internal
 */
class Ajax extends Backend
{
    protected $noNeedLogin = ['lang'];
    protected $noNeedRight = ['*'];
    protected $layout = '';

    public function _initialize()
    {
        parent::_initialize();

        //フィルターメソッドを設定
        $this->request->filter(['trim', 'strip_tags', 'htmlspecialchars']);
    }

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

        return jsonp(Lang::get(), 200, $header, ['json_encode_param' => JSON_FORCE_OBJECT | JSON_UNESCAPED_UNICODE]);
    }

    /**
     * アップロードファイル
     */
    public function upload()
    {
        Config::set('default_return_type', 'json');

        //必ず元に戻すupload設定,そうでないと分割アップロードおよびcdnurl関数の計算が誤ります
        Config::load(APP_PATH . 'extra/upload.php', 'upload');

        $chunkid = $this->request->post("chunkid");
        if ($chunkid) {
            if (!Config::get('upload.chunking')) {
                $this->error(__('Chunk file disabled'));
            }
            $action = $this->request->post("action");
            $chunkindex = $this->request->post("chunkindex/d");
            $chunkcount = $this->request->post("chunkcount/d");
            $filename = $this->request->post("filename");
            $method = $this->request->method(true);
            if ($action == 'merge') {
                $attachment = null;
                //分割ファイルを結合する
                try {
                    $upload = new Upload();
                    $attachment = $upload->merge($chunkid, $chunkcount, $filename);
                } catch (UploadException $e) {
                    $this->error($e->getMessage());
                }
                $this->success(__('Uploaded successful'), '', ['url' => $attachment->url, 'fullurl' => cdnurl($attachment->url, true)]);
            } elseif ($method == 'clean') {
                //不要な分割ファイルを削除する
                try {
                    $upload = new Upload();
                    $upload->clean($chunkid);
                } catch (UploadException $e) {
                    $this->error($e->getMessage());
                }
                $this->success();
            } else {
                //分割ファイルをアップロードする
                //デフォルトは通常のファイルアップロード
                $file = $this->request->file('file');
                try {
                    $upload = new Upload($file);
                    $upload->chunk($chunkid, $chunkindex, $chunkcount);
                } catch (UploadException $e) {
                    $this->error($e->getMessage());
                }
                $this->success();
            }
        } else {
            $attachment = null;
            //デフォルトは通常のファイルアップロード
            $file = $this->request->file('file');
            try {
                $upload = new Upload($file);
                $attachment = $upload->upload();
            } catch (UploadException $e) {
                $this->error($e->getMessage());
            }

            $this->success(__('Uploaded successful'), '', ['url' => $attachment->url, 'fullurl' => cdnurl($attachment->url, true)]);
        }
    }

    /**
     * 汎用ソート
     */
    public function weigh()
    {
        //ソート対象の配列
        $ids = $this->request->post("ids");
        //ドラッグしたレコードID
        $changeid = $this->request->post("changeid");
        //操作フィールド
        $field = $this->request->post("field");
        //操作するデータテーブル
        $table = $this->request->post("table");
        if (!Validate::is($table, "alphaDash")) {
            $this->error();
        }
        //主キー
        $pk = $this->request->post("pk");
        //ソート方式
        $orderway = strtolower($this->request->post("orderway", ""));
        $orderway = $orderway == 'asc' ? 'ASC' : 'DESC';
        $sour = $weighdata = [];
        $ids = explode(',', $ids);
        $prikey = $pk && preg_match("/^[a-z0-9\-_]+$/i", $pk) ? $pk : (Db::name($table)->getPk() ?: 'id');
        $pid = $this->request->post("pid", "");
        //更新を制限するフィールド
        $field = in_array($field, ['weigh']) ? $field : 'weigh';

        // もし設定されている場合pidの値,この時、条件を満たすものだけをマッチさせID,その他は無視する
        if ($pid !== '') {
            $hasids = [];
            $list = Db::name($table)->where($prikey, 'in', $ids)->where('pid', 'in', $pid)->field("{$prikey},pid")->select();
            foreach ($list as $k => $v) {
                $hasids[] = $v[$prikey];
            }
            $ids = array_values(array_intersect($ids, $hasids));
        }

        $list = Db::name($table)->field("$prikey,$field")->where($prikey, 'in', $ids)->order($field, $orderway)->select();
        foreach ($list as $k => $v) {
            $sour[] = $v[$prikey];
            $weighdata[$v[$prikey]] = $v[$field];
        }
        $position = array_search($changeid, $ids);
        $desc_id = $sour[$position] ?? end($sour);    //移動先のID値,取出所处改变前位置的値
        $sour_id = $changeid;
        $weighids = [];
        $temp = array_values(array_diff_assoc($ids, $sour));
        foreach ($temp as $m => $n) {
            if ($n == $sour_id) {
                $offset = $desc_id;
            } else {
                if ($sour_id == $temp[0]) {
                    $offset = $temp[$m + 1] ?? $sour_id;
                } else {
                    $offset = $temp[$m - 1] ?? $sour_id;
                }
            }
            if (!isset($weighdata[$offset])) {
                continue;
            }
            $weighids[$n] = $weighdata[$offset];
            Db::name($table)->where($prikey, $n)->update([$field => $weighdata[$offset]]);
        }
        $this->success();
    }

    /**
     * システムキャッシュをクリア
     */
    public function wipecache()
    {
        try {
            $type = $this->request->request("type");
            switch ($type) {
                case 'all':
                case 'content':
                    //コンテンツキャッシュ
                    rmdirs(CACHE_PATH, false);
                    Cache::clear();
                    if ($type == 'content') {
                        break;
                    }
                    // no break
                case 'template':
                    // テンプレートキャッシュ
                    rmdirs(TEMP_PATH, false);
                    if ($type == 'template') {
                        break;
                    }
                    // no break
                case 'addons':
                    // プラグインキャッシュ
                    Service::refresh();
                    if ($type == 'addons') {
                        break;
                    }
                    // no break
                case 'browser':
                    // ブラウザーキャッシュ
                    // 本番環境下のみ変更する
                    if (!config('app_debug')) {
                        $version = config('site.version');
                        $newversion = preg_replace_callback("/(.*)\.([0-9]+)\$/", function ($match) {
                            return $match[1] . '.' . ($match[2] + 1);
                        }, $version);
                        if ($newversion && $newversion != $version) {
                            Db::startTrans();
                            try {
                                \app\common\model\Config::where('name', 'version')->update(['value' => $newversion]);
                                \app\common\model\Config::refreshFile();
                                Db::commit();
                            } catch (\Exception $e) {
                                Db::rollback();
                                exception($e->getMessage());
                            }
                        }
                    }
                    if ($type == 'browser') {
                        break;
                    }
            }
        } catch (\Exception $e) {
            $this->error($e->getMessage());
        }

        \think\Hook::listen("wipecache_after");
        $this->success();
    }

    /**
     * カテゴリーデータを読み込む,連動リスト
     */
    public function category()
    {
        $type = $this->request->get('type', 'goods'); // 默认为商品分类
        $pid = $this->request->get('pid', '');
        $tree = $this->request->get('tree', '0'); // 是否返回树形结构
        $where = ['status' => 'normal'];
        $categorylist = null;
        if ($pid || $pid === '0') {
            $where['pid'] = $pid;
        }
        if ($type) {
            $where['type'] = $type;
        }

        if ($tree == '1') {
            // 返回树形结构，包含所有层级
            $categorylist = Db::name('category')
                ->where($where)
                ->field('id as value,name,pid')
                ->order('weigh desc,id desc')
                ->select();

            // 构建树形结构并添加缩进
            $categorylist = $this->buildCategoryTree($categorylist);
        } else {
            $categorylist = Db::name('category')
                ->where($where)
                ->field('id as value,name')
                ->order('weigh desc,id desc')
                ->select();
        }

        $this->success('', '', $categorylist);
    }

    /**
     * 构建分类树形结构
     */
    private function buildCategoryTree($categories, $pid = 0, $level = 0)
    {
        $tree = [];
        foreach ($categories as $category) {
            if ($category['pid'] == $pid) {
                // 添加缩进前缀
                $prefix = str_repeat('　', $level); // 全角空格
                $category['name'] = $prefix . $category['name'];
                $tree[] = $category;

                // 递归查找子分类
                $children = $this->buildCategoryTree($categories, $category['value'], $level + 1);
                $tree = array_merge($tree, $children);
            }
        }
        return $tree;
    }

    /**
     * 省市区データを読み込む,連動リスト
     */
    public function area()
    {
        $params = $this->request->get("row/a");
        if (!empty($params)) {
            $province = isset($params['province']) ? $params['province'] : null;
            $city = isset($params['city']) ? $params['city'] : null;
        } else {
            $province = $this->request->get('province');
            $city = $this->request->get('city');
        }
        $where = ['pid' => 0, 'level' => 1];
        $provincelist = null;
        if ($province !== null) {
            $where['pid'] = $province;
            $where['level'] = 2;
            if ($city !== null) {
                $where['pid'] = $city;
                $where['level'] = 3;
            }
        }
        $provincelist = Db::name('area')->where($where)->field('id as value,name')->select();
        $this->success('', '', $provincelist);
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
}

<?php

namespace app\admin\model;

use app\admin\library\Auth;
use think\Model;
use think\Loader;

class AdminLog extends Model
{

    // 自動タイムスタンプ書き込みを有効にする
    protected $autoWriteTimestamp = 'int';
    // タイムスタンプフィールド名を定義
    protected $createTime = 'createtime';
    protected $updateTime = '';
    //カスタムログタイトル
    protected static $title = '';
    //カスタムログ内容
    protected static $content = '';
    //無視するリンクの正規表現リスト
    protected static $ignoreRegex = [
        '/^(.*)\/(selectpage|index)$/i',
    ];

    public static function setTitle($title)
    {
        self::$title = $title;
    }

    public static function setContent($content)
    {
        self::$content = $content;
    }

    public static function setIgnoreRegex($regex = [])
    {
        $regex = is_array($regex) ? $regex : [$regex];
        self::$ignoreRegex = array_merge(self::$ignoreRegex, $regex);
    }

    /**
     * ログを記録
     * @param string $title   ログタイトル
     * @param string $content ログ内容
     */
    public static function record($title = '', $content = '')
    {
        $auth = Auth::instance();
        $admin_id = $auth->isLogin() ? $auth->id : 0;
        $username = $auth->isLogin() ? $auth->username : __('Unknown');

        // フィルター関数を設定
        request()->filter('trim,strip_tags,htmlspecialchars');

        $controllername = Loader::parseName(request()->controller());
        $actionname = strtolower(request()->action());
        $path = str_replace('.', '/', $controllername) . '/' . $actionname;
        if (self::$ignoreRegex) {
            foreach (self::$ignoreRegex as $index => $item) {
                if (preg_match($item, $path)) {
                    return;
                }
            }
        }
        $content = $content ?: self::$content;
        if (!$content) {
            $content = request()->param('') ?: file_get_contents("php://input");
            $content = self::getPureContent($content);
        }
        $title = $title ?: self::$title;
        if (!$title) {
            $title = [];
            $breadcrumb = Auth::instance()->getBreadcrumb($path);
            foreach ($breadcrumb as $k => $v) {
                $title[] = $v['title'];
            }
            $title = implode(' / ', $title);
        }
        self::create([
            'title'     => $title,
            'content'   => !is_scalar($content) ? json_encode($content, JSON_UNESCAPED_UNICODE) : $content,
            'url'       => substr(xss_clean(strip_tags(request()->url())), 0, 1500),
            'admin_id'  => $admin_id,
            'username'  => $username,
            'useragent' => substr(request()->server('HTTP_USER_AGENT'), 0, 255),
            'ip'        => xss_clean(strip_tags(request()->ip()))
        ]);
    }

    /**
     * マスク済みの機密情報データを取得
     * @param $content
     * @return array
     */
    protected static function getPureContent($content)
    {
        if (!is_array($content)) {
            return $content;
        }
        foreach ($content as $index => &$item) {
            if (preg_match("/(password|salt|token)/i", $index)) {
                $item = "***";
            } else {
                if (is_array($item)) {
                    $item = self::getPureContent($item);
                }
            }
        }
        return $content;
    }

    public function admin()
    {
        return $this->belongsTo('Admin', 'admin_id')->setEagerlyType(0);
    }
}

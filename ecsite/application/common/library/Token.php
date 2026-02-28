<?php

namespace app\common\library;

use app\common\library\token\Driver;
use think\App;
use think\Config;
use think\Log;

/**
 * Token操作クラス
 */
class Token
{
    /**
     * @var array Tokenのインスタンス
     */
    public static $instance = [];

    /**
     * @var object 操作ハンドラ
     */
    public static $handler;

    /**
     * 接続Tokenドライバ
     * @access public
     * @param array       $options 設定配列
     * @param bool|string $name    Token接続識別子 true 強制再接続
     * @return Driver
     */
    public static function connect(array $options = [], $name = false)
    {
        $type = !empty($options['type']) ? $options['type'] : 'File';

        if (false === $name) {
            $name = md5(serialize($options));
        }

        if (true === $name || !isset(self::$instance[$name])) {
            $class = false === strpos($type, '\\') ?
                '\\app\\common\\library\\token\\driver\\' . ucwords($type) :
                $type;

            // 初期化情報を記録
            App::$debug && Log::record('[ TOKEN ] INIT ' . $type, 'info');

            if (true === $name) {
                return new $class($options);
            }

            self::$instance[$name] = new $class($options);
        }

        return self::$instance[$name];
    }

    /**
     * 自動初期化Token
     * @access public
     * @param array $options 設定配列
     * @return Driver
     */
    public static function init(array $options = [])
    {
        if (is_null(self::$handler)) {
            if (empty($options) && 'complex' == Config::get('token.type')) {
                $default = Config::get('token.default');
                // デフォルトを取得Token設定，して接続
                $options = Config::get('token.' . $default['type']) ?: $default;
            } elseif (empty($options)) {
                $options = Config::get('token');
            }

            self::$handler = self::connect($options);
        }

        return self::$handler;
    }

    /**
     * 判定Token利用可能かどうか(checkエイリアス)
     * @access public
     * @param string $token   Token識別子
     * @param int    $user_id 会員ID
     * @return bool
     */
    public static function has($token, $user_id)
    {
        return self::check($token, $user_id);
    }

    /**
     * 判定Token利用可能かどうか
     * @param string $token   Token識別子
     * @param int    $user_id 会員ID
     * @return bool
     */
    public static function check($token, $user_id)
    {
        return self::init()->check($token, $user_id);
    }

    /**
     * 読み取りToken
     * @access public
     * @param string $token   Token識別子
     * @param mixed  $default デフォルト値
     * @return mixed
     */
    public static function get($token, $default = false)
    {
        return self::init()->get($token) ?: $default;
    }

    /**
     * 書き込みToken
     * @access public
     * @param string   $token   Token識別子
     * @param mixed    $user_id 会員ID
     * @param int|null $expire  有効期間 0は永久
     * @return boolean
     */
    public static function set($token, $user_id, $expire = null)
    {
        return self::init()->set($token, $user_id, $expire);
    }

    /**
     * 削除Token(deleteエイリアス)
     * @access public
     * @param string $token Token識別子
     * @return boolean
     */
    public static function rm($token)
    {
        return self::delete($token);
    }

    /**
     * 削除Token
     * @param string $token タグ名
     * @return bool
     */
    public static function delete($token)
    {
        return self::init()->delete($token);
    }

    /**
     * クリアToken
     * @access public
     * @param int $user_id 会員ID
     * @return boolean
     */
    public static function clear($user_id = null)
    {
        return self::init()->clear($user_id);
    }

}

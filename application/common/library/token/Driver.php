<?php
// +----------------------------------------------------------------------
// | ThinkPHP [ WE CAN DO IT JUST THINK ]
// +----------------------------------------------------------------------
// | Copyright (c) 2006~2018 http://thinkphp.cn All rights reserved.
// +----------------------------------------------------------------------
// | Licensed ( http://www.apache.org/licenses/LICENSE-2.0 )
// +----------------------------------------------------------------------
// | Author: liu21st <liu21st@gmail.com>
// +----------------------------------------------------------------------

namespace app\common\library\token;

/**
 * Token基底クラス
 */
abstract class Driver
{
    protected $handler = null;
    protected $options = [];

    /**
     * 保存Token
     * @param   string $token   Token
     * @param   int    $user_id 会員ID
     * @param   int    $expire  有効期限,0無制限を表す,単位は秒
     * @return bool
     */
    abstract function set($token, $user_id, $expire = 0);

    /**
     * 取得Token内の情報
     * @param   string $token
     * @return  array
     */
    abstract function get($token);

    /**
     * 判定Token利用可能かどうか
     * @param   string $token   Token
     * @param   int    $user_id 会員ID
     * @return  boolean
     */
    abstract function check($token, $user_id);

    /**
     * 削除Token
     * @param   string $token
     * @return  boolean
     */
    abstract function delete($token);

    /**
     * 指定ユーザーのすべてのToken
     * @param   int $user_id
     * @return  boolean
     */
    abstract function clear($user_id);

    /**
     * ハンドルオブジェクトを返す，その他の高度なメソッドを実行可能
     *
     * @access public
     * @return object
     */
    public function handler()
    {
        return $this->handler;
    }

    /**
     * 暗号化後のToken
     * @param string $token Token識別子
     * @return string
     */
    protected function getEncryptedToken($token)
    {
        $config = \think\Config::get('token');
        $token = $token ?? ''; // 互換性確保のため php8
        return hash_hmac($config['hashalgo'], $token, $config['key']);
    }

    /**
     * 有効期限までの残り時間を取得
     * @param $expiretime
     * @return float|int|mixed
     */
    protected function getExpiredIn($expiretime)
    {
        return $expiretime ? max(0, $expiretime - time()) : 365 * 86400;
    }
}

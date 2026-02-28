<?php

namespace app\common\library\token\driver;

use app\common\library\token\Driver;

/**
 * Token操作クラス
 */
class Mysql extends Driver
{

    /**
     * デフォルト設定
     * @var array
     */
    protected $options = [
        'table'      => 'user_token',
        'expire'     => 2592000,
        'connection' => [],
    ];


    /**
     * コンストラクタ
     * @param array $options パラメーター
     * @access public
     */
    public function __construct($options = [])
    {
        if (!empty($options)) {
            $this->options = array_merge($this->options, $options);
        }
        if ($this->options['connection']) {
            $this->handler = \think\Db::connect($this->options['connection'])->name($this->options['table']);
        } else {
            $this->handler = \think\Db::name($this->options['table']);
        }
        $time = time();
        $tokentime = cache('tokentime');
        if (!$tokentime || $tokentime < $time - 86400) {
            cache('tokentime', $time);
            $this->handler->where('expiretime', '<', $time)->where('expiretime', '>', 0)->delete();
        }
    }

    /**
     * 保存Token
     * @param string $token   Token
     * @param int    $user_id 会員ID
     * @param int    $expire  有効期限,0無制限を表す,単位は秒
     * @return bool
     */
    public function set($token, $user_id, $expire = null)
    {
        $expiretime = !is_null($expire) && $expire !== 0 ? time() + $expire : 0;
        $token = $this->getEncryptedToken($token);
        $this->handler->insert(['token' => $token, 'user_id' => $user_id, 'createtime' => time(), 'expiretime' => $expiretime]);
        return true;
    }

    /**
     * 取得Token内の情報
     * @param string $token
     * @return  array
     */
    public function get($token)
    {
        $data = $this->handler->where('token', $this->getEncryptedToken($token))->find();
        if ($data) {
            if (!$data['expiretime'] || $data['expiretime'] > time()) {
                //暗号化されていないtokenクライアントで使用するため
                $data['token'] = $token;
                //残りの有効時間を返す
                $data['expires_in'] = $this->getExpiredIn($data['expiretime']);
                return $data;
            } else {
                self::delete($token);
            }
        }
        return [];
    }

    /**
     * 判定Token利用可能かどうか
     * @param string $token   Token
     * @param int    $user_id 会員ID
     * @return  boolean
     */
    public function check($token, $user_id)
    {
        $data = $this->get($token);
        return $data && $data['user_id'] == $user_id ? true : false;
    }

    /**
     * 削除Token
     * @param string $token
     * @return  boolean
     */
    public function delete($token)
    {
        $this->handler->where('token', $this->getEncryptedToken($token))->delete();
        return true;
    }

    /**
     * 指定ユーザーのすべてのToken
     * @param int $user_id
     * @return  boolean
     */
    public function clear($user_id)
    {
        $this->handler->where('user_id', $user_id)->delete();
        return true;
    }

}

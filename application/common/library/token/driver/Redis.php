<?php

namespace app\common\library\token\driver;

use app\common\library\token\Driver;

/**
 * Token操作クラス
 */
class Redis extends Driver
{

    protected $options = [
        'host'        => '127.0.0.1',
        'port'        => 6379,
        'password'    => '',
        'select'      => 0,
        'timeout'     => 0,
        'expire'      => 0,
        'persistent'  => false,
        'userprefix'  => 'up:',
        'tokenprefix' => 'tp:',
    ];

    /**
     * コンストラクタ
     * @param array $options キャッシュパラメータ
     * @throws \BadFunctionCallException
     * @access public
     */
    public function __construct($options = [])
    {
        if (!extension_loaded('redis')) {
            throw new \BadFunctionCallException('not support: redis');
        }
        if (!empty($options)) {
            $this->options = array_merge($this->options, $options);
        }
        $this->handler = new \Redis;
        if ($this->options['persistent']) {
            $this->handler->pconnect($this->options['host'], $this->options['port'], $this->options['timeout'], 'persistent_id_' . $this->options['select']);
        } else {
            $this->handler->connect($this->options['host'], $this->options['port'], $this->options['timeout']);
        }

        if ('' != $this->options['password']) {
            $this->handler->auth($this->options['password']);
        }

        if (0 != $this->options['select']) {
            $this->handler->select($this->options['select']);
        }
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
        return $this->options['tokenprefix'] . hash_hmac($config['hashalgo'], $token, $config['key']);
    }

    /**
     * 会員のkey
     * @param $user_id
     * @return string
     */
    protected function getUserKey($user_id)
    {
        return $this->options['userprefix'] . $user_id;
    }

    /**
     * 保存Token
     * @param   string $token   Token
     * @param   int    $user_id 会員ID
     * @param   int    $expire  有効期限,0無制限を表す,単位は秒
     * @return bool
     */
    public function set($token, $user_id, $expire = 0)
    {
        if (is_null($expire)) {
            $expire = $this->options['expire'];
        }
        if ($expire instanceof \DateTime) {
            $expire = $expire->getTimestamp() - time();
        }
        $key = $this->getEncryptedToken($token);
        if ($expire) {
            $result = $this->handler->setex($key, $expire, $user_id);
        } else {
            $result = $this->handler->set($key, $user_id);
        }
        //会員関連のを書き込みtoken
        $this->handler->sAdd($this->getUserKey($user_id), $key);
        return $result;
    }

    /**
     * 取得Token内の情報
     * @param   string $token
     * @return  array
     */
    public function get($token)
    {
        $key = $this->getEncryptedToken($token);
        $value = $this->handler->get($key);
        if (is_null($value) || false === $value) {
            return [];
        }
        //有効期限を取得
        $expire = $this->handler->ttl($key);
        $expire = $expire < 0 ? 365 * 86400 : $expire;
        $expiretime = time() + $expire;
        //の使用時の問題を解決redis方式で保存tokenのときはapiインターフェースTokenリフレッシュと検証がexpires_inスペルミスによるエラーのBUG
        $result = ['token' => $token, 'user_id' => $value, 'expiretime' => $expiretime, 'expires_in' => $expire];

        return $result;
    }

    /**
     * 判定Token利用可能かどうか
     * @param   string $token   Token
     * @param   int    $user_id 会員ID
     * @return  boolean
     */
    public function check($token, $user_id)
    {
        $data = self::get($token);
        return $data && $data['user_id'] == $user_id ? true : false;
    }

    /**
     * 削除Token
     * @param   string $token
     * @return  boolean
     */
    public function delete($token)
    {
        $data = $this->get($token);
        if ($data) {
            $key = $this->getEncryptedToken($token);
            $user_id = $data['user_id'];
            $this->handler->del($key);
            $this->handler->sRem($this->getUserKey($user_id), $key);
        }
        return true;

    }

    /**
     * 指定ユーザーのすべてのToken
     * @param   int $user_id
     * @return  boolean
     */
    public function clear($user_id)
    {
        $keys = $this->handler->sMembers($this->getUserKey($user_id));
        $this->handler->del($this->getUserKey($user_id));
        $this->handler->del($keys);
        return true;
    }

}

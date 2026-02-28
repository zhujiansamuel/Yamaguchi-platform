<?php

namespace app\api\controller;

use app\common\controller\Api;
use fast\Random;

/**
 * Tokenインターフェース
 */
class Token extends Api
{
    protected $noNeedLogin = [];
    protected $noNeedRight = '*';

    /**
     * チェックToken有効期限切れかどうか
     *
     */
    public function check()
    {
        $token = $this->auth->getToken();
        $tokenInfo = \app\common\library\Token::get($token);
        $this->success('', ['token' => $tokenInfo['token'], 'expires_in' => $tokenInfo['expires_in']]);
    }

    /**
     * 更新Token
     *
     */
    public function refresh()
    {
        //元のトークンを削除Token
        $token = $this->auth->getToken();
        \app\common\library\Token::delete($token);
        //新規を作成Token
        $token = Random::uuid();
        \app\common\library\Token::set($token, $this->auth->id, 2592000);
        $tokenInfo = \app\common\library\Token::get($token);
        $this->success('', ['token' => $tokenInfo['token'], 'expires_in' => $tokenInfo['expires_in']]);
    }
}

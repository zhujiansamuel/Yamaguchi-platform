<?php

namespace app\api\controller;

use app\common\controller\Api;

/**
 * トップページAPI
 */
class Index extends Api
{
    protected $noNeedLogin = ['*'];
    protected $noNeedRight = ['*'];

    /**
     * 最初のページ
     *
     */
    public function index()
    {
        $this->success('リクエスト成功');
    }
}

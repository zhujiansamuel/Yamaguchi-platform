<?php
namespace app\api\controller;

use app\common\controller\Api;

class Test extends Api
{
    protected $noNeedLogin = ['*'];
    protected $noNeedRight = '*';

    public function index()
    {
        $this->success('Test API works');
    }
}

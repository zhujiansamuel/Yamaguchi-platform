<?php

namespace app\api\library;

use Exception;
use think\exception\Handle;

/**
 * カスタムAPIモジュールのエラー表示
 */
class ExceptionHandle extends Handle
{

    public function render(Exception $e)
    {
        // 本番環境下では返却code情報
        if (!\think\Config::get('app_debug')) {
            $statuscode = $code = 500;
            $msg = 'An error occurred';
            // 検証例外
            if ($e instanceof \think\exception\ValidateException) {
                $code = 0;
                $statuscode = 200;
                $msg = $e->getError();
            }
            // Http例外
            if ($e instanceof \think\exception\HttpException) {
                $statuscode = $code = $e->getStatusCode();
            }
            return json(['code' => $code, 'msg' => $msg, 'time' => time(), 'data' => null], $statuscode);
        }

        //その他はシステムに処理させます
        return parent::render($e);
    }

}

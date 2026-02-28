<?php

namespace app\admin\behavior;

class AdminLog
{
    public function run(&$response)
    {
        //のみ記録POSTリクエストのログ
        if (request()->isPost() && config('fastadmin.auto_record_log')) {
            \app\admin\model\AdminLog::record();
        }
    }
}

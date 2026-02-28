<?php

namespace app\common\library;

use fast\Random;
use think\Hook;

/**
 * SMS認証コードクラス
 */
class Sms
{

    /**
     * 認証コードの有効期間
     * @var int
     */
    protected static $expire = 120;

    /**
     * 検証の最大許可回数
     * @var int
     */
    protected static $maxCheckNums = 10;

    /**
     * 最後に携帯に送信したデータを取得
     *
     * @param   int    $mobile 携帯番号
     * @param   string $event  イベント
     * @return  Sms
     */
    public static function get($mobile, $event = 'default')
    {
        $sms = \app\common\model\Sms::where(['mobile' => $mobile, 'event' => $event])
            ->order('id', 'DESC')
            ->find();
        Hook::listen('sms_get', $sms, null, true);
        return $sms ?: null;
    }

    /**
     * 認証コードを送信
     *
     * @param   int    $mobile 携帯番号
     * @param   int    $code   認証コード,空の場合は自動的に生成されます4桁の数字
     * @param   string $event  イベント
     * @return  boolean
     */
    public static function send($mobile, $code = null, $event = 'default')
    {
        $code = is_null($code) ? Random::numeric(config('captcha.length')) : $code;
        $time = time();
        $ip = request()->ip();
        $sms = \app\common\model\Sms::create(['event' => $event, 'mobile' => $mobile, 'code' => $code, 'ip' => $ip, 'createtime' => $time]);
        $result = Hook::listen('sms_send', $sms, null, true);
        if (!$result) {
            $sms->delete();
            return false;
        }
        return true;
    }

    /**
     * 通知を送信
     *
     * @param   mixed  $mobile   携帯番号,複数指定する場合は,で区切る
     * @param   string $msg      メッセージ内容
     * @param   string $template メッセージテンプレート
     * @return  boolean
     */
    public static function notice($mobile, $msg = '', $template = null)
    {
        $params = [
            'mobile'   => $mobile,
            'msg'      => $msg,
            'template' => $template
        ];
        $result = Hook::listen('sms_notice', $params, null, true);
        return (bool)$result;
    }

    /**
     * 認証コードを検証
     *
     * @param   int    $mobile 携帯番号
     * @param   int    $code   認証コード
     * @param   string $event  イベント
     * @return  boolean
     */
    public static function check($mobile, $code, $event = 'default')
    {
        $time = time() - self::$expire;
        $sms = \app\common\model\Sms::where(['mobile' => $mobile, 'event' => $event])
            ->order('id', 'DESC')
            ->find();
        if ($sms) {
            if ($sms['createtime'] > $time && $sms['times'] <= self::$maxCheckNums) {
                $correct = $code == $sms['code'];
                if (!$correct) {
                    $sms->times = $sms->times + 1;
                    $sms->save();
                    return false;
                } else {
                    $result = Hook::listen('sms_check', $sms, null, true);
                    return $result;
                }
            } else {
                // 期限切れの場合はその携帯の認証コードをクリア
                self::flush($mobile, $event);
                return false;
            }
        } else {
            return false;
        }
    }

    /**
     * 指定した携帯番号の認証コードをクリア
     *
     * @param   int    $mobile 携帯番号
     * @param   string $event  イベント
     * @return  boolean
     */
    public static function flush($mobile, $event = 'default')
    {
        \app\common\model\Sms::where(['mobile' => $mobile, 'event' => $event])
            ->delete();
        Hook::listen('sms_flush');
        return true;
    }
}

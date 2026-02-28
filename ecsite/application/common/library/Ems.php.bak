<?php

namespace app\common\library;

use fast\Random;
use think\Hook;

/**
 * 邮箱验证码类
 */
class Ems
{

    /**
     * 验证码有效时长
     * @var int
     */
    protected static $expire = 120;

    /**
     * 最大允许检测的次数
     * @var int
     */
    protected static $maxCheckNums = 10;

    /**
     * 获取最后一次邮箱发送的数据
     *
     * @param int    $email 邮箱
     * @param string $event 事件
     * @return  Ems|null
     */
    public static function get($email, $event = 'default')
    {
        $ems = \app\common\model\Ems::where(['email' => $email, 'event' => $event])
            ->order('id', 'DESC')
            ->find();
        Hook::listen('ems_get', $ems, null, true);
        return $ems ?: null;
    }

    /**
     * 发送验证码
     *
     * @param int    $email 邮箱
     * @param int    $code  验证码,为空时将自动生成4位数字
     * @param string $event 事件
     * @return  boolean
     */
    public static function send($email, $code = null, $event = 'default')
    {
        $code = is_null($code) ? Random::numeric(config('captcha.length')) : $code;
        $time = time();
        $ip = request()->ip();
        $ems = \app\common\model\Ems::create(['event' => $event, 'email' => $email, 'code' => $code, 'ip' => $ip, 'createtime' => $time]);
        $subject = $message = '';
        switch ($event) {
            case 'register':
                $subject = '新規登録「Mobile Zone」';
                $message = '
「Mobile Zone」の会員を登録していただき、誠にありがとうごさいました。<br>
下記の認証コードを会員登録欄に入カしてください。<br>
--------------------------------------------------------------<br>
新規登録用認証コード:<br>
'.$code.'<br>
--------------------------------------------------------------<br>
※このメールは送信専用のため返信はお受けできません。<br>

Mobile Zone<br>

ホームページURL<br>

TEL:'.config('site.tel').'<br>

MAIL:'.config('site.mail').'<br>

2025 Mobile Zone';
                break;
            case 'resetpwd':
                $subject = 'パスワード再設定「Mobile Zone」';
                $message = '下記の認証コードをパスワード再設定の欄に入カしてください。<br>
--------------------------------------------------------------<br>
パスワード再設定用認証コード:<br>
'.$code.'<br>
--------------------------------------------------------------<br>
※このメールは送信専用のため返信はお受けできません。<br>

Mobile Zone<br>

ホームページURL<br>

TEL:'.config('site.tel').'<br>

MAIL:'.config('site.mail').'<br>

2025 Mobile Zone';
                break;
            default:
                
                break;
        }
        $obj = new Email();
        $result = $obj
            ->to($email)
            ->from(config('site.mail_from'), 'Mobile Zone')
            ->subject($subject)
            ->message($message)
            //->subject(__('请查收你的验证码！'))
            //->message(__("你的验证码是：%s，%s分钟内有效。", $code,ceil(self::$expire / 60)))
            ->send();
     
        if (!$result) {
            $ems->delete();
            //dump($obj->getError());
            return false;
        }
        return true;
    }

    /**
     * 发送通知
     *
     * @param mixed  $email    邮箱,多个以,分隔
     * @param string $msg      消息内容
     * @param string $template 消息模板
     * @return  boolean
     */
    public static function notice($email, $msg = '', $template = null)
    {
        $params = [
            'email'    => $email,
            'msg'      => $msg,
            'template' => $template
        ];
        if (!Hook::get('ems_notice')) {
            //采用框架默认的邮件推送
            Hook::add('ems_notice', function ($params) {
                $subject = '你收到一封新的邮件！';
                $content = $params['msg'];
                $email = new Email();
                $result = $email->to($params['email'])
                    ->subject($subject)
                    ->message($content)
                    ->send();
                return $result;
            });
        }
        $result = Hook::listen('ems_notice', $params, null, true);
        return (bool)$result;
    }

    /**
     * 校验验证码
     *
     * @param int    $email 邮箱
     * @param int    $code  验证码
     * @param string $event 事件
     * @return  boolean
     */
    public static function check($email, $code, $event = 'default')
    {
        $time = time() - self::$expire;
        $ems = \app\common\model\Ems::where(['email' => $email, 'event' => $event])
            ->order('id', 'DESC')
            ->find();
        if ($ems) {
            if ($ems['createtime'] > $time && $ems['times'] <= self::$maxCheckNums) {
                $correct = $code == $ems['code'];
                if (!$correct) {
                    $ems->times = $ems->times + 1;
                    $ems->save();
                    return false;
                } else {
                    $result = Hook::listen('ems_check', $ems, null, true);
                    return true;
                }
            } else {
                // 过期则清空该邮箱验证码
                self::flush($email, $event);
                return false;
            }
        } else {
            return false;
        }
    }

    /**
     * 清空指定邮箱验证码
     *
     * @param int    $email 邮箱
     * @param string $event 事件
     * @return  boolean
     */
    public static function flush($email, $event = 'default')
    {
        \app\common\model\Ems::where(['email' => $email, 'event' => $event])
            ->delete();
        Hook::listen('ems_flush');
        return true;
    }
}

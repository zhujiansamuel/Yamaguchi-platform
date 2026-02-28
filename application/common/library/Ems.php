<?php

namespace app\common\library;

use fast\Random;
use think\Hook;

/**
 * メール認証コードクラス
 */
class Ems
{
    /**
     * 最後の送信エラー（デバッグ用）
     * @var string
     */
    public static $lastError = '';

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
     * 最後に送信したメールデータを取得
     *
     * @param int    $email メールアドレス
     * @param string $event イベント
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
     * 認証コードを送信
     *
     * @param int    $email メールアドレス
     * @param int    $code  認証コード,空の場合は自動的に生成されます4桁の数字
     * @param string $event イベント
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
「Mobile Zone」の会員にご登録いただき、誠にありがとうございました。<br>
下記の認証コードを会員登録欄に入力してください。<br>
--------------------------------------------------------------<br>
新規登録用認証コード:<br>
'.$code.'<br>
--------------------------------------------------------------<br>
※このメールは送信専用のため返信はお受けできません。<br>

<p style="color:#ff0000;font-size:20px!important;margin:1px;">Mobile Zone<br></p>

www.mobile-zone.jp<br>


<span style="width: 8ch;letter-spacing: 0.05ch;white-space: nowrap;">電話番号</span>:&nbsp;'.config('site.tel').'<br>

<span style="width: 8ch;letter-spacing: 0.3ch;white-space: nowrap;">メール</span>:&nbsp;'.config('site.email').'<br>

2026 Mobile Zone';
                break;
            case 'resetpwd':
                $subject = 'パスワード再設定「Mobile Zone」';
                $message = '下記の認証コードをパスワード再設定の欄に入力してください。<br>
--------------------------------------------------------------<br>
パスワード再設定用認証コード:<br>
'.$code.'<br>
--------------------------------------------------------------<br>
※このメールは送信専用のため返信はお受けできません。<br>

<p style="color:#ff0000;font-size:20px!important;margin:1px;">Mobile Zone<br></p>

www.mobile-zone.jp<br>


<span style="width: 8ch;letter-spacing: 0.05ch;white-space: nowrap;">電話番号</span>:&nbsp;'.config('site.tel').'<br>

<span style="width: 8ch;letter-spacing: 0.3ch;white-space: nowrap;">メール</span>:&nbsp;'.config('site.email').'<br>

2026 Mobile Zone';
                break;
            case 'changeemail':
                $subject = 'メールアドレス変更「Mobile Zone」';
                $message = '下記の認証コードをメールアドレス変更の欄に入力してください。<br>
--------------------------------------------------------------<br>
メールアドレス変更用認証コード:<br>
'.$code.'<br>
--------------------------------------------------------------<br>
※このメールは送信専用のため返信はお受けできません。<br>

<p style="color:#ff0000;font-size:20px!important;margin:1px;">Mobile Zone<br></p>

www.mobile-zone.jp<br>


<span style="width: 8ch;letter-spacing: 0.05ch;white-space: nowrap;">電話番号</span>:&nbsp;'.config('site.tel').'<br>

<span style="width: 8ch;letter-spacing: 0.3ch;white-space: nowrap;">メール</span>:&nbsp;'.config('site.email').'<br>

2026 Mobile Zone';
                break;
            case 'changepwd':
                $subject = 'パスワード変更「Mobile Zone」';
                $message = '下記の認証コードをパスワード変更の欄に入力してください。<br>
--------------------------------------------------------------<br>
パスワード変更用認証コード:<br>
'.$code.'<br>
--------------------------------------------------------------<br>
※このメールは送信専用のため返信はお受けできません。<br>

<p style="color:#ff0000;font-size:20px!important;margin:1px;">Mobile Zone<br></p>

www.mobile-zone.jp<br>


<span style="width: 8ch;letter-spacing: 0.05ch;white-space: nowrap;">電話番号</span>:&nbsp;'.config('site.tel').'<br>

<span style="width: 8ch;letter-spacing: 0.3ch;white-space: nowrap;">メール</span>:&nbsp;'.config('site.email').'<br>

2026 Mobile Zone';
                break;
            default:
                $subject = '認証コード「Mobile Zone」';
                $message = '下記の認証コードを入力してください。<br>
--------------------------------------------------------------<br>
認証コード:<br>
'.$code.'<br>
--------------------------------------------------------------<br>
※このメールは送信専用のため返信はお受けできません。<br>

<p style="color:#ff0000;font-size:20px!important;margin:1px;">Mobile Zone<br></p>

www.mobile-zone.jp<br>


<span style="width: 8ch;letter-spacing: 0.05ch;white-space: nowrap;">電話番号</span>:&nbsp;'.config('site.tel').'<br>

<span style="width: 8ch;letter-spacing: 0.3ch;white-space: nowrap;">メール</span>:&nbsp;'.config('site.email').'<br>

2026 Mobile Zone';
                break;
        }
        $obj = new Email();
        $result = $obj
            ->to($email)
            ->from(config('site.mail_from'), 'Mobile Zone')
            ->subject($subject)
            ->message($message)
            //->subject(__('認証コードをご確認ください！'))
            //->message(__("あなたの認証コードは：%s，%s分以内有効です。", $code,ceil(self::$expire / 60)))
            ->send();
     
        if (!$result) {
            self::$lastError = $obj->getError();
            \think\Log::error('[Ems] メール送信失敗: ' . self::$lastError . ' | email=' . $email . ' | event=' . $event);
            $ems->delete();
            return false;
        }
        self::$lastError = '';
        return true;
    }

    /**
     * 通知を送信
     *
     * @param mixed  $email    メールアドレス,複数指定する場合は,で区切る
     * @param string $msg      メッセージ内容
     * @param string $template メッセージテンプレート
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
            //フレームワーク標準のメール配信を採用
            Hook::add('ems_notice', function ($params) {
                $subject = '新しいメールが届いています！';
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
     * 認証コードを検証
     *
     * @param int    $email メールアドレス
     * @param int    $code  認証コード
     * @param string $event イベント
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
                // 有効期限切れの場合は該当メールの認証コードを削除
                self::flush($email, $event);
                return false;
            }
        } else {
            return false;
        }
    }

    /**
     * 指定メールアドレスの認証コードを削除
     *
     * @param int    $email メールアドレス
     * @param string $event イベント
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

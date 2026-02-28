<?php

namespace app\api\controller;

use app\common\controller\Api;
use app\common\library\Ems as Emslib;
use app\common\model\User;
use think\Hook;

/**
 * メール認証コードインターフェース
 */
class Ems extends Api
{
    protected $noNeedLogin = '*';
    protected $noNeedRight = '*';

    public function _initialize()
    {
        parent::_initialize();
    }

    /**
     * 認証コードを送信
     *
     * @ApiMethod (POST)
     * @ApiParams (name="email", type="string", required=true, description="メールアドレス")
     * @ApiParams (name="event", type="string", required=true, description="イベント名")
     */
    public function send()
    {
        $email = $this->request->post("email");
        $event = $this->request->post("event");
        $event = $event ? $event : 'register';

        if (!$email || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
            $this->error(__('メールアドレスの形式が正しくありません'));
        }
        if (!preg_match("/^[a-z0-9_\-]{3,30}\$/i", $event)) {
            $this->error(__('イベント名エラー'));
        }

        //送信前認証コード
        if (config('fastadmin.user_api_captcha')) {

            if (!preg_match("/^[a-z0-9]{4,6}\$/i", $captcha)) {
                $this->error(__('認証コード形式エラー'));
            }

            if (!\think\Validate::is($captcha, 'captcha')) {
                $this->error("認証コードが正しくありません");
            }
        }

        $last = Emslib::get($email, $event);
        if ($last && time() - $last['createtime'] < 60) {
            $this->error(__('送信が頻繁すぎます'));
        }

        $ipSendTotal = \app\common\model\Ems::where(['ip' => $this->request->ip()])->whereTime('createtime', '-1 hours')->count();
        if ($ipSendTotal >= 5) {
            $this->error(__('送信が頻繁すぎます'));
        }

        if ($event) {
            $userinfo = User::getByEmail($email);
            if ($event == 'register' && $userinfo) {
                //すでに登録されています
                $this->error(__('すでに登録されています'));
            } elseif (in_array($event, ['changeemail']) && $userinfo) {
                //占有されています
                $this->error(__('すでに占有されています'));
            } elseif (in_array($event, ['changepwd', 'resetpwd']) && !$userinfo) {
                //未登録です
                $this->error(__('未登録です'));
            }
        }
        $ret = Emslib::send($email, null, $event);
        if ($ret) {
            $this->success(__('送信に成功しました'));
        } else {
            $errMsg = Emslib::$lastError
                ? __('送信に失敗しました') . ': ' . Emslib::$lastError
                : __('送信に失敗しました');
            $this->error($errMsg);
        }
    }

    /**
     * 認証コードをチェック
     *
     * @ApiMethod (POST)
     * @ApiParams (name="email", type="string", required=true, description="メールアドレス")
     * @ApiParams (name="event", type="string", required=true, description="イベント名")
     * @ApiParams (name="captcha", type="string", required=true, description="認証コード")
     */
    public function check()
    {
        $email = $this->request->post("email");
        $event = $this->request->post("event");
        $event = $event ? $event : 'register';
        $captcha = $this->request->post("captcha");

        if (!$email || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
            $this->error(__('メールアドレスの形式が正しくありません'));
        }
        if (!preg_match("/^[a-z0-9_\-]{3,30}\$/i", $event)) {
            $this->error(__('イベント名エラー'));
        }

        if (!preg_match("/^[a-z0-9]{4,6}\$/i", $captcha)) {
            $this->error(__('認証コード形式エラー'));
        }

        if ($event) {
            $userinfo = User::getByEmail($email);
            if ($event == 'register' && $userinfo) {
                //すでに登録されています
                $this->error(__('すでに登録されています'));
            } elseif (in_array($event, ['changeemail']) && $userinfo) {
                //占有されています
                $this->error(__('すでに占有されています'));
            } elseif (in_array($event, ['changepwd', 'resetpwd']) && !$userinfo) {
                //未登録です
                $this->error(__('未登録です'));
            }
        }
        $ret = Emslib::check($email, $captcha, $event);
        if ($ret) {
            $this->success(__('成功'));
        } else {
            $this->error(__('認証コードが正しくありません'));
        }
    }
}

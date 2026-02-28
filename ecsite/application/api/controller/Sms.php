<?php

namespace app\api\controller;

use app\common\controller\Api;
use app\common\library\Sms as Smslib;
use app\common\model\User;
use think\Hook;

/**
 * 携帯SMSインターフェース
 */
class Sms extends Api
{
    protected $noNeedLogin = '*';
    protected $noNeedRight = '*';

    /**
     * 認証コードを送信
     *
     * @ApiMethod (POST)
     * @ApiParams (name="mobile", type="string", required=true, description="携帯番号")
     * @ApiParams (name="event", type="string", required=true, description="イベント名")
     */
    public function send()
    {
        $mobile = $this->request->post("mobile");
        $event = $this->request->post("event");
        $event = $event ? $event : 'register';

        if (!$mobile || !\think\Validate::regex($mobile, "^1\d{10}$")) {
            $this->error(__('携帯番号が正しくありません'));
        }
        $last = Smslib::get($mobile, $event);
        if ($last && time() - $last['createtime'] < 60) {
            $this->error(__('送信が頻繁すぎます'));
        }
        $ipSendTotal = \app\common\model\Sms::where(['ip' => $this->request->ip()])->whereTime('createtime', '-1 hours')->count();
        if ($ipSendTotal >= 5) {
            $this->error(__('送信が頻繁すぎます'));
        }
        if ($event) {
            $userinfo = User::getByMobile($mobile);
            if ($event == 'register' && $userinfo) {
                //すでに登録されています
                $this->error(__('すでに登録されています'));
            } elseif (in_array($event, ['changemobile']) && $userinfo) {
                //占有されています
                $this->error(__('すでに占有されています'));
            } elseif (in_array($event, ['changepwd', 'resetpwd']) && !$userinfo) {
                //未登録です
                $this->error(__('未登録です'));
            }
        }
        if (!Hook::get('sms_send')) {
            $this->error(__('管理画面のプラグイン管理でSMS認証プラグインをインストールしてください'));
        }
        $ret = Smslib::send($mobile, null, $event);
        if ($ret) {
            $this->success(__('送信に成功しました'));
        } else {
            $this->error(__('送信に失敗しました，SMS設定が正しいかご確認ください'));
        }
    }

    /**
     * 認証コードをチェック
     *
     * @ApiMethod (POST)
     * @ApiParams (name="mobile", type="string", required=true, description="携帯番号")
     * @ApiParams (name="event", type="string", required=true, description="イベント名")
     * @ApiParams (name="captcha", type="string", required=true, description="認証コード")
     */
    public function check()
    {
        $mobile = $this->request->post("mobile");
        $event = $this->request->post("event");
        $event = $event ? $event : 'register';
        $captcha = $this->request->post("captcha");

        if (!$mobile || !\think\Validate::regex($mobile, "^1\d{10}$")) {
            $this->error(__('携帯番号が正しくありません'));
        }
        if ($event) {
            $userinfo = User::getByMobile($mobile);
            if ($event == 'register' && $userinfo) {
                //すでに登録されています
                $this->error(__('すでに登録されています'));
            } elseif (in_array($event, ['changemobile']) && $userinfo) {
                //占有されています
                $this->error(__('すでに占有されています'));
            } elseif (in_array($event, ['changepwd', 'resetpwd']) && !$userinfo) {
                //未登録です
                $this->error(__('未登録です'));
            }
        }
        $ret = Smslib::check($mobile, $captcha, $event);
        if ($ret) {
            $this->success(__('成功'));
        } else {
            $this->error(__('認証コードが正しくありません'));
        }
    }
}

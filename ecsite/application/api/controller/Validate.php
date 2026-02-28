<?php

namespace app\api\controller;

use app\common\controller\Api;
use app\common\model\User;

/**
 * 検証インターフェース
 */
class Validate extends Api
{
    protected $noNeedLogin = '*';
    protected $layout = '';
    protected $error = null;

    public function _initialize()
    {
        parent::_initialize();
    }

    /**
     * メールをチェック
     *
     * @ApiMethod (POST)
     * @ApiParams (name="email", type="string", required=true, description="メールアドレス")
     * @ApiParams (name="id", type="string", required=true, description="除外する会員ID")
     */
    public function check_email_available()
    {
        $email = $this->request->post('email');
        $id = (int)$this->request->post('id');
        $count = User::where('email', '=', $email)->where('id', '<>', $id)->count();
        if ($count > 0) {
            $this->error(__('メールアドレスは既に使用されています'));
        }
        $this->success();
    }

    /**
     * ユーザー名を検証
     *
     * @ApiMethod (POST)
     * @ApiParams (name="username", type="string", required=true, description="ユーザー名")
     * @ApiParams (name="id", type="string", required=true, description="除外する会員ID")
     */
    public function check_username_available()
    {
        $username = $this->request->post('username');
        $id = (int)$this->request->post('id');
        $count = User::where('username', '=', $username)->where('id', '<>', $id)->count();
        if ($count > 0) {
            $this->error(__('ユーザー名は既に使用されています'));
        }
        $this->success();
    }

    /**
     * ニックネームをチェック
     *
     * @ApiMethod (POST)
     * @ApiParams (name="nickname", type="string", required=true, description="ニックネーム")
     * @ApiParams (name="id", type="string", required=true, description="除外する会員ID")
     */
    public function check_nickname_available()
    {
        $nickname = $this->request->post('nickname');
        $id = (int)$this->request->post('id');
        $count = User::where('nickname', '=', $nickname)->where('id', '<>', $id)->count();
        if ($count > 0) {
            $this->error(__('ニックネームは既に使用されています'));
        }
        $this->success();
    }

    /**
     * 携帯番号をチェック
     *
     * @ApiMethod (POST)
     * @ApiParams (name="mobile", type="string", required=true, description="携帯番号")
     * @ApiParams (name="id", type="string", required=true, description="除外する会員ID")
     */
    public function check_mobile_available()
    {
        $mobile = $this->request->post('mobile');
        $id = (int)$this->request->post('id');
        $count = User::where('mobile', '=', $mobile)->where('id', '<>', $id)->count();
        if ($count > 0) {
            $this->error(__('この携帯番号は既に使用されています'));
        }
        $this->success();
    }

    /**
     * 携帯番号をチェック
     *
     * @ApiMethod (POST)
     * @ApiParams (name="mobile", type="string", required=true, description="携帯番号")
     */
    public function check_mobile_exist()
    {
        $mobile = $this->request->post('mobile');
        $count = User::where('mobile', '=', $mobile)->count();
        if (!$count) {
            $this->error(__('携帯番号が存在しません'));
        }
        $this->success();
    }

    /**
     * メールをチェック
     *
     * @ApiMethod (POST)
     * @ApiParams (name="email", type="string", required=true, description="メールアドレス")
     */
    public function check_email_exist()
    {
        $email = $this->request->post('email');
        $count = User::where('email', '=', $email)->count();
        if (!$count) {
            $this->error(__('メールアドレスが存在しません'));
        }
        $this->success();
    }

    /**
     * SMS 認証コードをチェック
     *
     * @ApiMethod (POST)
     * @ApiParams (name="mobile", type="string", required=true, description="携帯番号")
     * @ApiParams (name="captcha", type="string", required=true, description="認証コード")
     * @ApiParams (name="event", type="string", required=true, description="イベント")
     */
    public function check_sms_correct()
    {
        $mobile = $this->request->post('mobile');
        $captcha = $this->request->post('captcha');
        $event = $this->request->post('event');
        if (!\app\common\library\Sms::check($mobile, $captcha, $event)) {
            $this->error(__('認証コードが正しくありません'));
        }
        $this->success();
    }

    /**
     * メール認証コードをチェック
     *
     * @ApiMethod (POST)
     * @ApiParams (name="email", type="string", required=true, description="メールアドレス")
     * @ApiParams (name="captcha", type="string", required=true, description="認証コード")
     * @ApiParams (name="event", type="string", required=true, description="イベント")
     */
    public function check_ems_correct()
    {
        $email = $this->request->post('email');
        $captcha = $this->request->post('captcha');
        $event = $this->request->post('event');
        if (!\app\common\library\Ems::check($email, $captcha, $event)) {
            $this->error(__('認証コードが正しくありません'));
        }
        $this->success();
    }
}

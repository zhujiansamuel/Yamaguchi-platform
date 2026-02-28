<?php

namespace app\index\controller;

use addons\wechat\model\WechatCaptcha;
use app\common\controller\Frontend;
use app\common\library\Ems;
use app\common\library\Sms;
use app\common\model\Attachment;
use think\Config;
use think\Cookie;
use think\Hook;
use think\Session;
use think\Validate;
use app\common\model\Shopping;
use app\common\model\Order;
use custom\ConfigStatus as CS;

/**
 * 会员中心
 */
class User extends Base
{
    //protected $layout = 'default';
    protected $noNeedLogin = ['login', 'register', 'third'];
    protected $noNeedRight = ['*'];

    public function _initialize()
    {
        parent::_initialize();
        $auth = $this->auth;

        if (!Config::get('fastadmin.usercenter')) {
            $this->error(__('User center already closed'), '/');
        }

        //监听注册登录退出的事件
        Hook::add('user_login_successed', function ($user) use ($auth) {
            $expire = input('post.keeplogin') ? 30 * 86400 : 0;
            Cookie::set('uid', $user->id, $expire);
            Cookie::set('token', $auth->getToken(), $expire);
        });
        Hook::add('user_register_successed', function ($user) use ($auth) {
            Cookie::set('uid', $user->id);
            Cookie::set('token', $auth->getToken());
        });
        Hook::add('user_delete_successed', function ($user) use ($auth) {
            Cookie::delete('uid');
            Cookie::delete('token');
        });
        Hook::add('user_logout_successed', function ($user) use ($auth) {
            Cookie::delete('uid');
            Cookie::delete('token');
        });
    }

    /**
     * 会员中心
     */
    public function index()
    {
        $category = db('category')->whereIn('type', 'szb,occupation')->order('weigh desc')->select();
        $szb = $occupation = [];
        foreach ($category as $key => $val) {
            if($val['type'] == 'szb'){
                $szb[] = $val;
            }
            if($val['type'] == 'occupation'){
                $occupation[] = $val;
            }
        }
        $year = $month = $days = '';
        if($this->auth->birthday){
            list($year, $month, $days) = explode('-', $this->auth->birthday);
        }
        $szb_image = $this->auth->szb_image ? explode(',', $this->auth->szb_image) : [];
        $this->view->assign('title', __('会員登録情報'));
        $this->view->assign('szb', $szb);
        $this->view->assign('szb_image', $szb_image);
        $this->view->assign('year', $year);
        $this->view->assign('month', $month);
        $this->view->assign('days', $days);
        $this->view->assign('occupation', $occupation);
        return $this->view->fetch();
    }

    /**
     * 订单 - 予約履歷
     */
    public function order()
    {   
        $where = [];
        $where['user_id'] = $this->auth->id;
        $list = Order::with('details')
        ->where($where)->order('id desc')->paginate(10)->each(function($vs){
            $vs['show_cancel'] = $vs['status'] == CS::ORDER_STATUS_5 ? 0 : 1;
            return $vs;
        });
        $page = $list->render();
        $this->view->assign('title', __('予約履歷'));
        $this->view->assign('list', $list);
        $this->view->assign('page', $page);
        return $this->view->fetch();
    }

    /**
     * 订单 - 予約履歷 - 详情
     */
    public function order_details()
    {   
        $order_id = $this->request->param('id');
        $where = [];
        $where['user_id'] = $this->auth->id;
        $where['id'] = $order_id;
        $info = Order::with('user,store,details')
        ->where($where)->order('id desc')->find();
        if(!$info){
            $this->error(__('数据不存在'));
        }
        $this->view->assign('title', __('予約履歷'));
        $this->view->assign('info', $info);
        return $this->view->fetch();
    }

    /**
     * 申请完成页面
     */
    public function applyfor_complete()
    {   
        $this->view->assign('title', __('申し込み完了'));
        return $this->view->fetch();
    }
    

    /**
     * 购物车 - カート
     */
    public function shopping()
    {   
        $where = [];
        $where['s.user_id'] = $this->auth->id;
        $list = db('shopping')->alias('s')->field('s.*, g.jan')
          ->join('goods g','g.id =s.goods_id')
          ->where($where)->order('s.id desc')->select();
        $totalMoney = 0;
        foreach ($list as $key => $val) {
            //$totalMoney += $val['num'] * ($val['type'] == 1 ? $val['price'] : $val['price_zg']);
            $totalMoney += $val['num'] * $val['price'];
            if($val['type'] == 2){
                //$val['price'] = $val['price_zg'];
            }
            $list[$key]['price'] = number_format($val['price']);
        }
        $totalMoney = number_format($totalMoney);
        $this->view->assign('title', __('カート'));
        $this->view->assign('list', $list);
        $this->view->assign('totalMoney', $totalMoney);
        return $this->view->fetch();
    }

    /**
     * 店铺买取/邮件申请
     */
    public function applyfor()
    {   
        $type = $this->request->param('type') ?: 1;
        if($type == 1){
            $title = __('店頭買取のお申し込み');
        }else{
            $title = __('郵送買取のお申し込み');
        }
        $where = [];
        $where['s.user_id'] = $this->auth->id;
        $list = db('shopping')->alias('s')->field('s.*, g.jan')
          ->join('goods g','g.id =s.goods_id')
          ->where($where)->order('s.id desc')->select();
        $totalMoney = 0;
        foreach ($list as $key => $val) {
            //$totalMoney += $val['num'] * ($val['type'] == 1 ? $val['price'] : $val['price_zg']);
            $totalMoney += $val['num'] * $val['price'];
            if($val['type'] == 2){
                //$val['price'] = $val['price_zg'];
            }
            $list[$key]['price'] = number_format($val['price']);
        }
        $totalMoney = number_format($totalMoney);

        $shopList = db('store')->order('weigh desc')->select();

        //来店時間
        $goShopTime = [];
        for ($i=11; $i < 18; $i++) { 
            $starttime = strtotime(date('Y-m-d 00:00') . ' +'.$i.' hours');
            
            $starttime = date('H:00', $starttime);
            
            $endtime = strtotime(date('Y-m-d 00:00') . ' +'.($i + 1).' hours');
            if($endtime < time()){
                continue;
            }
            $endtime = date('H:00', $endtime);
            $goShopTime[] = $starttime.'-'.$endtime;
        }

        if(!$goShopTime){
            $goShopTime[] = '【日時をご相談】';
        }

        $this->view->assign('title', $title);
        $this->view->assign('type', $type);
        $this->view->assign('list', $list);
        $this->view->assign('shopList', $shopList);
        $this->view->assign('goShopTime', $goShopTime);
        $this->view->assign('totalMoney', $totalMoney);
        return $this->view->fetch();
    }

    /**
     * 注册会员
     */
    public function register()
    {
        $url = $this->request->request('url', '', 'url_clean');
        if ($this->auth->id) {
            $this->success(__('You\'ve logged in, do not login again'), $url ? $url : url('user/index'));
        }
        if ($this->request->isPost()) {
            $username = $this->request->post('username');
            $password = $this->request->post('password', '', null);
            $email = $this->request->post('email');
            $mobile = $this->request->post('mobile', '');
            $captcha = $this->request->post('captcha');
            $token = $this->request->post('__token__');
            $rule = [
                'username'  => 'require|length:3,30',
                'password'  => 'require|length:6,30',
                'email'     => 'require|email',
                'mobile'    => 'regex:/^1\d{10}$/',
                '__token__' => 'require|token',
            ];

            $msg = [
                'username.require' => 'Username can not be empty',
                'username.length'  => 'Username must be 3 to 30 characters',
                'password.require' => 'Password can not be empty',
                'password.length'  => 'Password must be 6 to 30 characters',
                'email'            => 'Email is incorrect',
                'mobile'           => 'Mobile is incorrect',
            ];
            $data = [
                'username'  => $username,
                'password'  => $password,
                'email'     => $email,
                'mobile'    => $mobile,
                '__token__' => $token,
            ];
            //验证码
            $captchaResult = true;
            $captchaType = config("fastadmin.user_register_captcha");
            if ($captchaType) {
                if ($captchaType == 'mobile') {
                    $captchaResult = Sms::check($mobile, $captcha, 'register');
                } elseif ($captchaType == 'email') {
                    $captchaResult = Ems::check($email, $captcha, 'register');
                } elseif ($captchaType == 'wechat') {
                    $captchaResult = WechatCaptcha::check($captcha, 'register');
                } elseif ($captchaType == 'text') {
                    $captchaResult = \think\Validate::is($captcha, 'captcha');
                }
            }
            if (!$captchaResult) {
                $this->error(__('Captcha is incorrect'));
            }
            $validate = new Validate($rule, $msg);
            $result = $validate->check($data);
            if (!$result) {
                $this->error(__($validate->getError()), null, ['token' => $this->request->token()]);
            }
            if ($this->auth->register($username, $password, $email, $mobile)) {
                $this->success(__('Sign up successful'), $url ? $url : url('user/index'));
            } else {
                $this->error($this->auth->getError(), null, ['token' => $this->request->token()]);
            }
        }
        //判断来源
        $referer = $this->request->server('HTTP_REFERER', '', 'url_clean');
        if (!$url && $referer && !preg_match("/(user\/login|user\/register|user\/logout)/i", $referer)) {
            $url = $referer;
        }
        $this->view->assign('captchaType', config('fastadmin.user_register_captcha'));
        $this->view->assign('url', $url);
        $this->view->assign('title', __('Register'));
        return $this->view->fetch();
    }

    /**
     * 会员登录
     */
    public function login()
    {
        $url = $this->request->request('url', '', 'url_clean');
        if ($this->auth->id) {
            $this->success(__('You\'ve logged in, do not login again'), $url ?: url('user/index'));
        }
        if ($this->request->isPost()) {
            $account = $this->request->post('account');
            $password = $this->request->post('password', '', null);
            $keeplogin = (int)$this->request->post('keeplogin');
            $token = $this->request->post('__token__');
            $rule = [
                'account'   => 'require|length:3,50',
                'password'  => 'require|length:6,30',
                '__token__' => 'require|token',
            ];

            $msg = [
                'account.require'  => 'Account can not be empty',
                'account.length'   => 'Account must be 3 to 50 characters',
                'password.require' => 'Password can not be empty',
                'password.length'  => 'Password must be 6 to 30 characters',
            ];
            $data = [
                'account'   => $account,
                'password'  => $password,
                '__token__' => $token,
            ];
            $validate = new Validate($rule, $msg);
            $result = $validate->check($data);
            if (!$result) {
                $this->error(__($validate->getError()), null, ['token' => $this->request->token()]);
            }
            if ($this->auth->login($account, $password)) {
                $this->success(__('Logged in successful'), $url ? $url : url('user/index'));
            } else {
                $this->error($this->auth->getError(), null, ['token' => $this->request->token()]);
            }
        }
        //判断来源
        $referer = $this->request->server('HTTP_REFERER', '', 'url_clean');
        if (!$url && $referer && !preg_match("/(user\/login|user\/register|user\/logout)/i", $referer)) {
            $url = $referer;
        }
        $this->view->assign('url', $url);
        $this->view->assign('title', __('Login'));
        return $this->view->fetch();
    }

    /**
     * 退出登录
     */
    public function logout()
    {
        if ($this->request->isPost()) {
            $this->token();
            //退出本站
            $this->auth->logout();
            $this->redirect('/');
            //$this->success(__('Logout successful'), url('/'));
        }
        $html = "<form id='logout_submit' name='logout_submit' action='' method='post'>" . token() . "<input type='submit' value='ok' style='display:none;'></form>";
        $html .= "<script>document.forms['logout_submit'].submit();</script>";

        return $html;
    }

    /**
     * 个人信息
     */
    public function profile()
    {
        $this->view->assign('title', __('Profile'));
        return $this->view->fetch();
    }

    /**
     * 修改密码
     */
    public function changepwd()
    {
        if ($this->request->isPost()) {
            $oldpassword = $this->request->post("oldpassword", '', null);
            $newpassword = $this->request->post("newpassword", '', null);
            $renewpassword = $this->request->post("renewpassword", '', null);
            $token = $this->request->post('__token__');
            $rule = [
                'oldpassword'   => 'require|regex:\S{6,30}',
                'newpassword'   => 'require|regex:\S{6,30}',
                'renewpassword' => 'require|regex:\S{6,30}|confirm:newpassword',
                '__token__'     => 'token',
            ];

            $msg = [
                'renewpassword.confirm' => __('Password and confirm password don\'t match')
            ];
            $data = [
                'oldpassword'   => $oldpassword,
                'newpassword'   => $newpassword,
                'renewpassword' => $renewpassword,
                '__token__'     => $token,
            ];
            $field = [
                'oldpassword'   => __('Old password'),
                'newpassword'   => __('New password'),
                'renewpassword' => __('Renew password')
            ];
            $validate = new Validate($rule, $msg, $field);
            $result = $validate->check($data);
            if (!$result) {
                $this->error(__($validate->getError()), null, ['token' => $this->request->token()]);
            }

            $ret = $this->auth->changepwd($newpassword, $oldpassword);
            if ($ret) {
                $this->success(__('Reset password successful'), url('user/login'));
            } else {
                $this->error($this->auth->getError(), null, ['token' => $this->request->token()]);
            }
        }
        $this->view->assign('title', __('Change password'));
        return $this->view->fetch();
    }

    public function attachment()
    {
        //设置过滤方法
        $this->request->filter(['strip_tags']);
        if ($this->request->isAjax()) {
            $mimetypeQuery = [];
            $where = [];
            $filter = $this->request->request('filter');
            $filterArr = (array)json_decode($filter, true);
            if (isset($filterArr['mimetype']) && preg_match("/(\/|\,|\*)/", $filterArr['mimetype'])) {
                $this->request->get(['filter' => json_encode(array_diff_key($filterArr, ['mimetype' => '']))]);
                $mimetypeQuery = function ($query) use ($filterArr) {
                    $mimetypeArr = array_filter(explode(',', $filterArr['mimetype']));
                    foreach ($mimetypeArr as $index => $item) {
                        $query->whereOr('mimetype', 'like', '%' . str_replace("/*", "/", $item) . '%');
                    }
                };
            } elseif (isset($filterArr['mimetype'])) {
                $where['mimetype'] = ['like', '%' . $filterArr['mimetype'] . '%'];
            }

            if (isset($filterArr['filename'])) {
                $where['filename'] = ['like', '%' . $filterArr['filename'] . '%'];
            }

            if (isset($filterArr['createtime'])) {
                $timeArr = explode(' - ', $filterArr['createtime']);
                $where['createtime'] = ['between', [strtotime($timeArr[0]), strtotime($timeArr[1])]];
            }
            $search = $this->request->get('search');
            if ($search) {
                $where['filename'] = ['like', '%' . $search . '%'];
            }

            $model = new Attachment();
            $offset = $this->request->get("offset", 0);
            $limit = $this->request->get("limit", 0);
            $total = $model
                ->where($where)
                ->where($mimetypeQuery)
                ->where('user_id', $this->auth->id)
                ->order("id", "DESC")
                ->count();

            $list = $model
                ->where($where)
                ->where($mimetypeQuery)
                ->where('user_id', $this->auth->id)
                ->order("id", "DESC")
                ->limit($offset, $limit)
                ->select();
            $cdnurl = preg_replace("/\/(\w+)\.php$/i", '', $this->request->root());
            foreach ($list as $k => &$v) {
                $v['fullurl'] = ($v['storage'] == 'local' ? $cdnurl : $this->view->config['upload']['cdnurl']) . $v['url'];
            }
            unset($v);
            $result = array("total" => $total, "rows" => $list);

            return json($result);
        }
        $mimetype = $this->request->get('mimetype', '');
        $mimetype = substr($mimetype, -1) === '/' ? $mimetype . '*' : $mimetype;
        $this->view->assign('mimetype', $mimetype);
        $this->view->assign("mimetypeList", \app\common\model\Attachment::getMimetypeList());
        return $this->view->fetch();
    }
}

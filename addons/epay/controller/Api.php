<?php

namespace addons\epay\controller;

use addons\epay\library\Service;
use addons\epay\library\Wechat;
use addons\third\model\Third;
use app\common\library\Auth;
use Exception;
use think\addons\Controller;
use think\Response;
use think\Session;
use Yansongda\Pay\Exceptions\GatewayException;
use Yansongda\Pay\Pay;

/**
 * APIAPIコントローラー
 *
 * @package addons\epay\controller
 */
class Api extends Controller
{

    protected $layout = 'default';
    protected $config = [];

    /**
     * デフォルトメソッド
     */
    public function index()
    {
        return;
    }

    /**
     * 外部送信
     */
    public function submit()
    {
        $this->request->filter('trim');
        $out_trade_no = $this->request->request("out_trade_no");
        $title = $this->request->request("title");
        $amount = $this->request->request('amount');
        $type = $this->request->request('type', $this->request->request('paytype'));
        $method = $this->request->request('method', 'web');
        $openid = $this->request->request('openid', '');
        $auth_code = $this->request->request('auth_code', '');
        $notifyurl = $this->request->request('notifyurl', '');
        $returnurl = $this->request->request('returnurl', '');

        if (!$amount || $amount < 0) {
            $this->error("支払金額は次の値より大きくなければなりません0");
        }

        if (!$type || !in_array($type, ['alipay', 'wechat'])) {
            $this->error("支払種別エラー");
        }

        $params = [
            'type'         => $type,
            'out_trade_no' => $out_trade_no,
            'title'        => $title,
            'amount'       => $amount,
            'method'       => $method,
            'openid'       => $openid,
            'auth_code'    => $auth_code,
            'notifyurl'    => $notifyurl,
            'returnurl'    => $returnurl,
        ];
        return Service::submitOrder($params);
    }

    /**
     * WeChat決済(公式アカウント決済&PCスキャン決済)
     */
    public function wechat()
    {
        $config = Service::getConfig('wechat');

        $isWechat = stripos($this->request->server('HTTP_USER_AGENT'), 'MicroMessenger') !== false;
        $isMobile = $this->request->isMobile();
        $this->view->assign("isWechat", $isWechat);
        $this->view->assign("isMobile", $isMobile);

        //開始PC支払い(Scan支払い)(PCスキャンモード)
        if ($this->request->isAjax()) {
            $pay = Pay::wechat($config);
            $orderid = $this->request->post("orderid");
            try {
                $result = Service::isVersionV3() ? $pay->find(['out_trade_no' => $orderid]) : $pay->find($orderid, 'scan');
                $this->success("", "", ['status' => $result['trade_state'] ?? 'NOTPAY']);
            } catch (GatewayException $e) {
                $this->error("照会に失敗しました(1001)");
            }
        }

        $orderData = Session::get("wechatorderdata");
        if (!$orderData) {
            $this->error("リクエストパラメーターエラー");
        }
        if ($isWechat && $isMobile) {
            //公式アカウント支払いを開始(jsapi支払い),openid必須

            //もし存在しない場合openid，自動的に取得しますopenid
            if (!isset($orderData['openid']) || !$orderData['openid']) {
                $orderData['openid'] = Service::getOpenid();
            }

            $orderData['method'] = 'mp';
            $type = 'jsapi';
            $payData = Service::submitOrder($orderData);
            if (!isset($payData['paySign'])) {
                $this->error("注文の作成に失敗しました，戻って再試行してください", "");
            }
        } else {
            $orderData['method'] = 'scan';
            $type = 'pc';
            $payData = Service::submitOrder($orderData);
            if (!isset($payData['code_url'])) {
                $this->error("注文の作成に失敗しました，戻って再試行してください", "");
            }
        }
        $this->view->assign("orderData", $orderData);
        $this->view->assign("payData", $payData);
        $this->view->assign("type", $type);

        $this->view->assign("title", "WeChat決済");
        return $this->view->fetch();
    }

    /**
     * Alipay支払い(PCスキャン決済)
     */
    public function alipay()
    {
        $config = Service::getConfig('alipay');

        $isWechat = stripos($this->request->server('HTTP_USER_AGENT'), 'MicroMessenger') !== false;
        $isMobile = $this->request->isMobile();
        $this->view->assign("isWechat", $isWechat);
        $this->view->assign("isMobile", $isMobile);

        if ($this->request->isAjax()) {
            $orderid = $this->request->post("orderid");
            $pay = Pay::alipay($config);
            try {
                $result = $pay->find(['out_trade_no' => $orderid]);
                if ($result['code'] == '10000' && $result['trade_status'] == 'TRADE_SUCCESS') {
                    $this->success("", "", ['status' => $result['trade_status']]);
                } else {
                    $this->error("照会に失敗しました");
                }
            } catch (GatewayException $e) {
                $this->error("照会に失敗しました(1001)");
            }
        }

        //開始PC支払い(Scan支払い)(PCスキャンモード)
        $orderData = Session::get("alipayorderdata");
        if (!$orderData) {
            $this->error("リクエストパラメーターエラー");
        }

        $orderData['method'] = 'scan';
        $payData = Service::submitOrder($orderData);
        if (!isset($payData['qr_code'])) {
            $this->error("注文の作成に失敗しました，戻って再試行してください");
        }

        $type = 'pc';
        $this->view->assign("orderData", $orderData);
        $this->view->assign("payData", $payData);
        $this->view->assign("type", $type);
        $this->view->assign("title", "Alipay支払い");
        return $this->view->fetch();
    }

    /**
     * 支払い成功コールバック
     */
    public function notifyx()
    {
        $paytype = $this->request->param('paytype');
        $pay = Service::checkNotify($paytype);
        if (!$pay) {
            return json(['code' => 'FAIL', 'message' => '失敗'], 500, ['Content-Type' => 'application/json']);
        }

        // コールバックデータを取得，V3とV2のコールバック受信が異なります
        $data = Service::isVersionV3() ? $pay->callback() : $pay->verify();

        try {
            //WeChat決済V3戻り値とV2異なります
            if (Service::isVersionV3() && $paytype === 'wechat') {
                $data = $data['resource']['ciphertext'];
                $data['total_fee'] = $data['amount']['total'];
            }

            \think\Log::record($data);
            //支払金額を取得、注文番号
            $payamount = $paytype == 'alipay' ? $data['total_amount'] : $data['total_fee'] / 100;
            $out_trade_no = $data['out_trade_no'];

            \think\Log::record("コールバック成功，注文番号：{$out_trade_no}，金額：{$payamount}");

            //ここで注文処理ロジックを記述できます
        } catch (Exception $e) {
            \think\Log::record("コールバックロジック処理エラー:" . $e->getMessage(), "error");
        }

        //以下の一文は必ず実行してください,かつその前に何も出力してはいけません
        if (Service::isVersionV3()) {
            return $pay->success()->getBody()->getContents();
        } else {
            return $pay->success()->send();
        }
    }

    /**
     * 支払い成功レスポンス
     */
    public function returnx()
    {
        $paytype = $this->request->param('paytype');
        if (Service::checkReturn($paytype)) {
            echo '署名が誤っている';
            return;
        }

        //ここでメッセージ内容を定義できます,ただしここでロジックを記述しないでください
        $this->success("おめでとうございます！支払い成功!", addon_url("epay/index/index"));
    }

}

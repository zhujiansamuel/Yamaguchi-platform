<?php

namespace addons\epay\controller;

use addons\epay\library\Service;
use fast\Random;
use think\addons\Controller;
use Exception;

/**
 * WeChat・Alipay統合プラグイン ホーム
 *
 * このコントローラーは開発時の表示説明およびテスト専用です，戻り値およびコールバック処理用の新しいコントローラーを追加してください，あわせてこのコントローラーファイルを削除してください
 *
 * Class Index
 * @package addons\epay\controller
 */
class Index extends Controller
{
    protected $layout = 'default';

    protected $config = [];

    public function _initialize()
    {
        parent::_initialize();
        if (!config("app_debug")) {
            $this->error("開発環境でのみ閲覧可能");
        }
    }

    public function index()
    {
        $this->view->assign("title", "WeChat・Alipay統合");
        return $this->view->fetch();
    }

    /**
     * 体験，開発テスト専用
     */
    public function experience()
    {
        $amount = $this->request->post('amount');
        $type = $this->request->post('type');
        $method = $this->request->post('method');
        $openid = $this->request->post('openid', "");

        if (!$amount || $amount < 0) {
            $this->error("支払金額は次の値より大きくなければなりません0");
        }

        if (!$type || !in_array($type, ['alipay', 'wechat'])) {
            $this->error("支払種別は空にできません");
        }

        if (in_array($method, ['miniapp', 'mp']) && !$openid) {
            $this->error("openid空にできません");
        }

        //注文番号
        $out_trade_no = date("YmdHis") . mt_rand(100000, 999999);

        //注文タイトル
        $title = 'テスト注文';

        //コールバックURL
        $notifyurl = $this->request->root(true) . '/addons/epay/index/notifyx/paytype/' . $type;
        $returnurl = $this->request->root(true) . '/addons/epay/index/returnx/paytype/' . $type . '/out_trade_no/' . $out_trade_no;

        $response = Service::submitOrder($amount, $out_trade_no, $type, $title, $notifyurl, $returnurl, $method, $openid);

        return $response;
    }

    /**
     * 支払い成功，開発テスト専用
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
     * 支払い戻り，開発テスト専用
     */
    public function returnx()
    {
        $paytype = $this->request->param('paytype');
        $out_trade_no = $this->request->param('out_trade_no');
        $pay = Service::checkReturn($paytype);
        if (!$pay) {
            $this->error('署名が誤っている', '');
        }

        //ここでメッセージ内容を定義できます,ただしここでロジックを記述しないでください
        $this->success("サイトに戻って支払い結果を確認してください", addon_url("epay/index/index"));
    }
}

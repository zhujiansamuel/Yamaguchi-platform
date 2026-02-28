<?php

namespace app\api\controller;

use app\common\controller\Api;
use think\Exception;
use custom\Data;
use custom\ConfigStatus as CS;
use think\Db;
use addons\epay\library\Service;
use app\common\model\User;
/**
 * 支払い
 */
class Pay extends Api
{
    //use \traits\Shares, \traits\Redis;

    protected $noNeedLogin = ['notify','ys_notify','ys_df_notify','cardnotify'];
    protected $noNeedRight = ['*'];


    /**
     * 支払い
     *
     */
    public function index()
    {
        try {
            $request = $this->request->post();
            $type = $this->request->post('type');
            $no = $request['no'] ?? '';
            
            if(!$no){
                throw new Exception('注文番号が不足しています');
            }

            if(!$this->auth->openid){
                throw new Exception('支払いに失敗しました,認可してください');
            }

            $response = [];
            if(strpos($no, 'R') !== false){
                $OrderMsg = 'チャージ';
                $info = db('user_recharge')->where('no', $no)->find();
                $type = 'recharge';
            }else{
                $info = db('order')->where('no', $no)->find();
                $OrderMsg = '注文';
                $type = 'order';
                $info['money'] = $info['total_money'];
            }

            $no = $info['no'] . '-' . rand(100,999);
            
            if($info['money'] > 0){
                $notifyurl = getProtocol().'/notify/'.$type;
                $returnurl = getProtocol().'/returnx/'.$type;
                $response = Service::submitOrder(
                    $info['money'], $no, 'wechat', $OrderMsg, $notifyurl, $returnurl, 'miniapp', $this->auth->openid
                );
            }else{
                $data = [
                    'out_trade_no' =>   $no,
                    'total_fee' => $info['money'] * 100
                ];
                switch ($type) {
                    case 'recharge':
                        $this->updateRecharge($data);
                        break;
                    default:
                        $this->updateOrder($data);
                        break;
                }
            }
            
            
            $this->success('成功！', $response);

        }catch (Exception $e){
            //例外をキャッチ
            $this->error($e->getMessage());
        }
    }


    /**
     * 支払い成功，開発テスト専用
     */
    public function notify()
    {
        $type = $this->request->param('type');

        $pay = Service::checkNotify('wechat');
        $xinpaopaoPayNotify = json_decode(cache('xinpaopaoPayNotify'), true) ?? [];
        if (!$pay) {
            array_push($xinpaopaoPayNotify, '署名が誤っている');
            cache('xinpaopaoPayNotify', json_encode($xinpaopaoPayNotify, JSON_UNESCAPED_UNICODE), 3600);
            return;
        }
        $data = $pay->verify();
        try {
            array_push($xinpaopaoPayNotify, json_encode($data, JSON_UNESCAPED_UNICODE));
            
            // キャッシュデータを設定
            cache('xinpaopaoPayNotify', json_encode($xinpaopaoPayNotify, JSON_UNESCAPED_UNICODE), 3600);

            switch ($type) {
                case 'recharge':
                    $this->updateRecharge($data);
                    break;
                default:
                    $this->updateOrder($data);
                    break;
            }
            

        } catch (Exception $e) {
        }

        //以下の一文は必ず実行してください,かつその前に何も出力してはいけません
        return $pay->success()->send();
    }

    private function updateOrder($data)
    {
        list($no, $rand) = explode('-', $data['out_trade_no']);
        $payamount = $data['total_fee'] / 100;
        $transaction_id = $data['transaction_id'] ?? '';
        
        $order = db('order')->where('no', $no)->find();
        //注文ユーザー情報を取得
        $orderUser = db('user')->where('id', $order['user_id'])->find();

        // トランザクションを開始
        Db::startTrans();
        try {
            db('order')->where('no', $no)->update([
                'status' => CS::ORDER_STATUS_YES_PAY,
                'is_pay' => 1,
                'transaction_id' => $transaction_id,
                'pay_time' => time(),
            ]);

            if($orderUser && $orderUser['pid']){
                $income = round((config('site.distributionLevel1') / 100) * $order['total_money'], 2);
                User::income($income, $orderUser['pid'], '収益', CS::MONEY_LOG_TYPE_PROFIT, $order['id']);
                //上位ユーザー情報を取得
                $subUserPid = db('user')->where('id', $orderUser['pid'])->value('pid');
                if($subUserPid){
                    $income2 = round((config('site.distributionLevel2') / 100) * $order['total_money'], 2);
                    User::income($income2, $subUserPid, '収益', CS::MONEY_LOG_TYPE_PROFIT, $order['id']);
                }
            }

            // トランザクションをコミットする
            Db::commit();
        } catch (\Exception $e) {
            // トランザクションをロールバック
            Db::rollback();
            $this->error($e->getMessage());
        }
    }

    private function updateRecharge($data)
    {
        list($no, $rand) = explode('-', $data['out_trade_no']);
        $payamount = $data['total_fee'] / 100;
        $transaction_id = $data['transaction_id'] ?? '';
        $user_recharge = db('user_recharge')->where('no', $no)->find();
        
        // トランザクションを開始
        Db::startTrans();
        try {
            db('user_recharge')->where('no', $no)->update([
                'is_pay' => 1,
                'pay_time' => time(),
                'transaction_id' => $transaction_id
            ]);

            User::money($user_recharge['money'] + $user_recharge['deliver'], $user_recharge['user_id'], 'チャージ', CS::MONEY_LOG_TYPE_RECHARGE, $user_recharge['id']);

            // トランザクションをコミットする
            Db::commit();
        } catch (\Exception $e) {
            // トランザクションをロールバック
            Db::rollback();
            //$this->error($e->getMessage());
        }
    }
    
    
    /**
     * 支払い戻り，開発テスト専用
     */
    public function returnx()
    {
        $paytype = $this->request->param('paytype');
        $out_trade_no = $this->request->param('out_trade_no');
        // $pay = Service::checkReturn($paytype);
        // if (!$pay) {
        //     $this->error('署名が誤っている', '');
        // }

        //ここでout_trade_noを通じて注文ステータスを検証できます
        //ただしここで注文ロジックを記述してはいけません！！！

        $this->success("サイトに戻って支払い結果を確認してください", 'https://szhswy.cn/#/pages/tabbar/home/pay/paySuccess/paySuccess');
    }
    
    
    public function ceshi()
    {
        $no = $this->request->post('no');
        $order_info['total_fee'] = 50;
        $order_info['out_trade_no'] = $no.'-556';
        if(strpos($no, 'R') !== false){
            $this->updateRecharge($order_info);
        }else{
            $this->updateOrder($order_info);
        }
        
        // $xinpaopaoPayNotify = json_decode(cache('xinpaopaoPayNotify'), true) ?? [];
        // dump($xinpaopaoPayNotify);
        // die;
       //Data::name('order', $order_info)->order_info(true,true)->verifi('payStatus')->getProject()->updateOrder();
        die;
    }
    
    /*
     * WeChat に注文金額と署名が正しいことを通知し、SUCCESS 情報を返す，SUCCESS情報 -xzz0521
     */
    private function return_success(){
        $return['return_code'] = 'SUCCESS';
        $return['return_msg'] = 'OK';
        $xml_post = '<xml>
                    <return_code>'.$return['return_code'].'</return_code>
                    <return_msg>'.$return['return_msg'].'</return_msg>
                    </xml>';
        echo $xml_post;exit;
    }
    
    
    /**
     * をxmlに変換array
     * @param string $xml
     * return array
     */
    public function xml_to_array($xml){
        if(!$xml){
            return false;
        }
        //をXMLに変換array
        //外部参照を禁止xmlエンティティ
        libxml_disable_entity_loader(true);
        $data = json_decode(json_encode(simplexml_load_string($xml, 'SimpleXMLElement', LIBXML_NOCDATA)), true);
        return $data;
    }
    


}

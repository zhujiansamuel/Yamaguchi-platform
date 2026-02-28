<?php

namespace addons\epay\library;

use addons\third\model\Third;
use app\common\library\Auth;
use Exception;
use think\Hook;
use think\Session;
use Yansongda\Pay\Pay;
use Yansongda\Supports\Str;

/**
 * 注文サービスクラス
 *
 * @package addons\epay\library
 */
class Service
{

    public const SDK_VERSION_V2 = 'v2';

    public const SDK_VERSION_V3 = 'v3';

    /**
     * 注文を送信
     * @param array|float $amount    注文金額
     * @param string      $orderid   注文番号
     * @param string      $type      支払いタイプ,選択可能alipayまたはwechat
     * @param string      $title     注文タイトル
     * @param string      $notifyurl 通知コールバックURL
     * @param string      $returnurl リダイレクト戻りURL
     * @param string      $method    支払方法
     * @param string      $openid    Openid
     * @param array       $custom    カスタムのWeChat・Alipay関連設定
     * @return Response|RedirectResponse|Collection
     * @throws Exception
     */
    public static function submitOrder($amount, $orderid = null, $type = null, $title = null, $notifyurl = null, $returnurl = null, $method = null, $openid = '', $custom = [])
    {
        $version = self::getSdkVersion();
        $request = request();
        $addonConfig = get_addon_config('epay');

        if (!is_array($amount)) {
            $params = [
                'amount'    => $amount,
                'orderid'   => $orderid,
                'type'      => $type,
                'title'     => $title,
                'notifyurl' => $notifyurl,
                'returnurl' => $returnurl,
                'method'    => $method,
                'openid'    => $openid,
                'custom'    => $custom,
            ];
        } else {
            $params = $amount;
        }
        $type = isset($params['type']) && in_array($params['type'], ['alipay', 'wechat']) ? $params['type'] : 'wechat';
        $method = $params['method'] ?? 'web';
        $orderid = $params['orderid'] ?? date("YmdHis") . mt_rand(100000, 999999);
        $amount = $params['amount'] ?? 1;
        $title = $params['title'] ?? "支払い";
        $auth_code = $params['auth_code'] ?? '';
        $openid = $params['openid'] ?? '';

        //カスタムのWeChat・Alipay関連設定
        $custom = $params['custom'] ?? [];

        //未定義の場合はデフォルトのコールバックとリダイレクトを使用
        $notifyurl = !empty($params['notifyurl']) ? $params['notifyurl'] : $request->root(true) . '/addons/epay/index/notifyx/paytype/' . $type;
        $returnurl = !empty($params['returnurl']) ? $params['returnurl'] : $request->root(true) . '/addons/epay/index/returnx/paytype/' . $type . '/out_trade_no/' . $orderid;

        $html = '';
        $config = Service::getConfig($type, array_merge($custom, ['notify_url' => $notifyurl, 'return_url' => $returnurl]));

        //モバイル端末またはWeChat内ブラウザかどうかを判断
        $isMobile = $request->isMobile();
        $isWechat = strpos($request->server('HTTP_USER_AGENT'), 'MicroMessenger') !== false;

        $result = null;
        if ($type == 'alipay') {
            //もし〜ならPC支払い,現在の環境を判断,リダイレクトを行う
            if ($method == 'web') {
                //WeChat環境またはバックエンド設定の場合PCスキャン決済を使用
                if ($isWechat || $addonConfig['alipay']['scanpay']) {
                    Session::set("alipayorderdata", $params);
                    $url = addon_url('epay/api/alipay', [], true, true);
                    return new RedirectResponse($url);
                } elseif ($isMobile) {
                    $method = 'wap';
                }
            }

            //決済オブジェクトを作成
            $pay = Pay::alipay($config);
            $params = [
                'out_trade_no' => $orderid,//あなたの注文番号
                'total_amount' => $amount,//単位：元
                'subject'      => $title,
            ];

            switch ($method) {
                case 'web':
                    //PC決済
                    $result = $pay->web($params);
                    break;
                case 'wap':
                    //モバイルWeb決済
                    $result = $pay->wap($params);
                    break;
                case 'app':
                    //APP支払い
                    $result = $pay->app($params);
                    break;
                case 'scan':
                    //スキャン決済
                    $result = $pay->scan($params);
                    break;
                case 'pos':
                    //カード決済には必須auth_code
                    $params['auth_code'] = $auth_code;
                    $result = $pay->pos($params);
                    break;
                case 'mini':
                case 'miniapp':
                    //ミニプログラム決済,文字列を直接返す
                    //ミニプログラム決済には必須buyer_idまたはbuyer_open_id
                    if (is_numeric($openid) && strlen($openid) === 16) {
                        $params['buyer_id'] = $openid;
                    } else {
                        $params['buyer_open_id'] = $openid;
                    }
                    $result = $pay->mini($params);
                    break;
                default:
            }
        } else {
            //もし〜ならPC支払い,現在の環境を判断,リダイレクトを行う
            if ($method == 'web') {
                //モバイル端末の場合，ただしWeChat環境ではない
                if ($isMobile && !$isWechat) {
                    $method = 'wap';
                } else {
                    Session::set("wechatorderdata", $params);
                    $url = addon_url('epay/api/wechat', [], true, true);
                    return new RedirectResponse($url);
                }
            }

            //単位：分
            $total_fee = function_exists('bcmul') ? bcmul($amount, 100) : $amount * 100;
            $total_fee = (int)$total_fee;
            $ip = $request->ip();
            //WeChatサービスプロバイダーモード時に渡す必要ありsub_openidパラメーター
            $openidName = $addonConfig['wechat']['mode'] == 'service' ? 'sub_openid' : 'openid';

            //決済オブジェクトを作成
            $pay = Pay::wechat($config);

            if (self::isVersionV3()) {
                //V3支払い
                $params = [
                    'out_trade_no' => $orderid,
                    'description'  => $title,
                    'amount'       => [
                        'total' => $total_fee,
                    ]
                ];
                switch ($method) {
                    case 'mp':
                        //公式アカウント決済
                        //公式アカウント決済には必須openid
                        $params['payer'] = [$openidName => $openid];
                        $result = $pay->mp($params);
                        break;
                    case 'wap':
                        //モバイルWeb決済,リダイレクト
                        $params['scene_info'] = [
                            'payer_client_ip' => $ip,
                            'h5_info'         => [
                                'type' => 'Wap',
                            ]
                        ];
                        $result = $pay->wap($params);
                        break;
                    case 'app':
                        //APP支払い,文字列を直接返す
                        $result = $pay->app($params);
                        break;
                    case 'scan':
                        //スキャン決済,文字列を直接返す
                        $result = $pay->scan($params);
                        break;
                    case 'pos':
                        //カード決済,文字列を直接返す
                        //カード決済には必須auth_code
                        $params['auth_code'] = $auth_code;
                        $result = $pay->pos($params);
                        break;
                    case 'mini':
                    case 'miniapp':
                        //ミニプログラム決済,文字列を直接返す
                        //ミニプログラム決済には必須openid
                        $params['payer'] = [$openidName => $openid];
                        $result = $pay->mini($params);
                        break;
                    default:
                }
            } else {
                //V2支払い
                $params = [
                    'out_trade_no' => $orderid,
                    'body'         => $title,
                    'total_fee'    => $total_fee,
                ];
                switch ($method) {
                    case 'mp':
                        //公式アカウント決済
                        //公式アカウント決済には必須openid
                        $params[$openidName] = $openid;
                        $result = $pay->mp($params);
                        break;
                    case 'wap':
                        //モバイルWeb決済,リダイレクト
                        $params['spbill_create_ip'] = $ip;
                        $result = $pay->wap($params);
                        break;
                    case 'app':
                        //APP支払い,文字列を直接返す
                        $result = $pay->app($params);
                        break;
                    case 'scan':
                        //スキャン決済,文字列を直接返す
                        $result = $pay->scan($params);
                        break;
                    case 'pos':
                        //カード決済,文字列を直接返す
                        //カード決済には必須auth_code
                        $params['auth_code'] = $auth_code;
                        $result = $pay->pos($params);
                        break;
                    case 'mini':
                    case 'miniapp':
                        //ミニプログラム決済,文字列を直接返す
                        //ミニプログラム決済には必須openid
                        $params[$openidName] = $openid;
                        $result = $pay->miniapp($params);
                        break;
                    default:
                }
            }
        }

        //オーバーライドされたResponseクラス、RedirectResponse、Collectionクラス
        if ($result instanceof \Symfony\Component\HttpFoundation\RedirectResponse) {
            $result = new RedirectResponse($result->getTargetUrl());
        } elseif ($result instanceof \Symfony\Component\HttpFoundation\Response) {
            $result = new Response($result->getContent());
        } elseif ($result instanceof \Yansongda\Supports\Collection) {
            $result = Collection::make($result->all());
        } elseif ($result instanceof \GuzzleHttp\Psr7\Response) {
            $result = new Response($result->getBody());
        }

        return $result;
    }

    /**
     * コールバックが成功かどうかを検証
     * @param string $type   支払いタイプ
     * @param array  $custom カスタム設定情報
     * @return bool|\Yansongda\Pay\Gateways\Alipay|\Yansongda\Pay\Gateways\Wechat|\Yansongda\Pay\Provider\Wechat|\Yansongda\Pay\Provider\Alipay
     */
    public static function checkNotify($type, $custom = [])
    {
        $type = strtolower($type);
        if (!in_array($type, ['wechat', 'alipay'])) {
            return false;
        }

        $version = self::getSdkVersion();

        try {
            $config = self::getConfig($type, $custom);
            $pay = $type == 'wechat' ? Pay::wechat($config) : Pay::alipay($config);

            $data = Service::isVersionV3() ? $pay->callback() : $pay->verify();
            if ($type == 'alipay') {
                if (in_array($data['trade_status'], ['TRADE_SUCCESS', 'TRADE_FINISHED'])) {
                    return $pay;
                }
            } else {
                return $pay;
            }
        } catch (Exception $e) {
            \think\Log::record("コールバックリクエストパラメータの解析エラー", "error");
            return false;
        }

        return false;
    }

    /**
     * 戻り値が成功かどうかを検証，支払い成功かどうかのロジック検証には使用しないでください
     * 非推奨
     *
     * @param string $type   支払いタイプ
     * @param array  $custom カスタム設定情報
     * @return bool
     * @deprecated  非推奨，ロジック検証には使用しないでください
     */
    public static function checkReturn($type, $custom = [])
    {
        //〜のためPCおよびモバイル端末ではリクエストパラメータ情報を取得できない，取り消しreturn検証，すべて返すtrue
        return true;
    }

    /**
     * 設定を取得
     * @param string $type   支払いタイプ
     * @param array  $custom カスタム設定，プラグインのデフォルト設定を上書きするために使用
     * @return array
     */
    public static function getConfig($type = 'wechat', $custom = [])
    {
        $addonConfig = get_addon_config('epay');
        $config = $addonConfig[$type] ?? $addonConfig['wechat'];

        // SDKバージョン
        $version = self::getSdkVersion();

        if (isset($config['cert_client']) && substr($config['cert_client'], 0, 8) == '/addons/') {
            $config['cert_client'] = ROOT_PATH . str_replace('/', DS, substr($config['cert_client'], 1));
        }
        if (isset($config['cert_key']) && substr($config['cert_key'], 0, 8) == '/addons/') {
            $config['cert_key'] = ROOT_PATH . str_replace('/', DS, substr($config['cert_key'], 1));
        }
        if (isset($config['app_cert_public_key']) && substr($config['app_cert_public_key'], 0, 8) == '/addons/') {
            $config['app_cert_public_key'] = ROOT_PATH . str_replace('/', DS, substr($config['app_cert_public_key'], 1));
        }
        if (isset($config['alipay_root_cert']) && substr($config['alipay_root_cert'], 0, 8) == '/addons/') {
            $config['alipay_root_cert'] = ROOT_PATH . str_replace('/', DS, substr($config['alipay_root_cert'], 1));
        }
        if (isset($config['ali_public_key']) && (Str::endsWith($config['ali_public_key'], '.crt') || Str::endsWith($config['ali_public_key'], '.pem'))) {
            $config['ali_public_key'] = ROOT_PATH . str_replace('/', DS, substr($config['ali_public_key'], 1));
        }

        // V3支払い
        if (self::isVersionV3()) {
            if ($type == 'wechat') {
                $config['mp_app_id'] = $config['app_id'] ?? '';
                $config['app_id'] = $config['appid'] ?? '';
                $config['mini_app_id'] = $config['miniapp_id'] ?? '';
                $config['combine_mch_id'] = $config['combine_mch_id'] ?? '';
                $config['mch_secret_key'] = $config['key_v3'] ?? '';
                $config['mch_secret_cert'] = $config['cert_key'];
                $config['mch_public_cert_path'] = $config['cert_client'];

                $config['sub_mp_app_id'] = $config['sub_appid'] ?? '';
                $config['sub_app_id'] = $config['sub_app_id'] ?? '';
                $config['sub_mini_app_id'] = $config['sub_miniapp_id'] ?? '';
                $config['sub_mch_id'] = $config['sub_mch_id'] ?? '';
            } elseif ($type == 'alipay') {
                $config['app_secret_cert'] = $config['private_key'] ?? '';
                $config['app_public_cert_path'] = $config['app_cert_public_key'] ?? '';
                $config['alipay_public_cert_path'] = $config['ali_public_key'] ?? '';
                $config['alipay_root_cert_path'] = $config['alipay_root_cert'] ?? '';
                $config['service_provider_id'] = $config['pid'] ?? '';
            }
            $modeArr = ['normal' => 0, 'dev' => 1, 'service' => 2];
            $config['mode'] = $modeArr[$config['mode']] ?? 0;
        }

        // ログ
        if ($config['log']) {
            $config['log'] = [
                'enable' => true,
                'file'   => LOG_PATH . 'epaylogs' . DS . $type . '-' . date("Y-m-d") . '.log',
                'level'  => 'debug'
            ];
        } else {
            $config['log'] = [
                'enable' => false,
            ];
        }

        // GuzzleHttp設定，選択可能
        $config['http'] = [
            'timeout'         => 10,
            'connect_timeout' => 10,
            // 詳細な設定項目は次を参照してください [Guzzle](https://guzzle-cn.readthedocs.io/zh_CN/latest/request-options.html)
        ];

        $config['notify_url'] = empty($config['notify_url']) ? addon_url('epay/api/notifyx', [], false) . '/type/' . $type : $config['notify_url'];
        $config['notify_url'] = !preg_match("/^(http:\/\/|https:\/\/)/i", $config['notify_url']) ? request()->root(true) . $config['notify_url'] : $config['notify_url'];
        $config['return_url'] = empty($config['return_url']) ? addon_url('epay/api/returnx', [], false) . '/type/' . $type : $config['return_url'];
        $config['return_url'] = !preg_match("/^(http:\/\/|https:\/\/)/i", $config['return_url']) ? request()->root(true) . $config['return_url'] : $config['return_url'];

        //カスタム設定をマージ
        $config = array_merge($config, $custom);

        //v3バージョンv3では返却される構造が異なる
        if (self::isVersionV3()) {
            $config = [$type => ['default' => $config], 'logger' => $config['log'], 'http' => $config['http'], '_force' => true];

        }
        return $config;
    }

    /**
     * WeChat を取得Openid
     *
     * @param array $custom カスタム設定情報
     * @return mixed|string
     */
    public static function getOpenid($custom = [])
    {
        $openid = '';
        $auth = Auth::instance();
        if ($auth->isLogin()) {
            $third = get_addon_info('third');
            if ($third && $third['state']) {
                $thirdInfo = Third::where('user_id', $auth->id)->where('platform', 'wechat')->where('apptype', 'mp')->find();
                $openid = $thirdInfo ? $thirdInfo['openid'] : '';
            }
        }
        if (!$openid) {
            $openid = Session::get("openid");

            //渡されていない場合openid，読み取りに行くopenid
            if (!$openid) {
                $addonConfig = get_addon_config('epay');
                $wechat = new Wechat($custom['app_id'] ?? $addonConfig['wechat']['app_id'], $custom['app_secret'] ?? $addonConfig['wechat']['app_secret']);
                $openid = $wechat->getOpenid();
            }
        }
        return $openid;
    }

    /**
     * 取得SDKバージョン
     * @return mixed|string
     */
    public static function getSdkVersion()
    {
        $addonConfig = get_addon_config('epay');
        return $addonConfig['version'] ?? self::SDK_VERSION_V2;
    }

    /**
     * かどうかを判定V2支払い
     * @return bool
     */
    public static function isVersionV2()
    {
        return self::getSdkVersion() === self::SDK_VERSION_V2;
    }

    /**
     * かどうかを判定V3支払い
     * @return bool
     */
    public static function isVersionV3()
    {
        return self::getSdkVersion() === self::SDK_VERSION_V3;
    }
}

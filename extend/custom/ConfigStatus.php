<?php
namespace custom;

class  ConfigStatus  {

    //入金
    const ENTRY = 0;
    //支出
    const CONSUME = 1;
    
    const DISABLED_YES = 1;

    const MONEY_DYNAMIC = [
        self::ENTRY => '入金',
        self::CONSUME => '支出',
    ];
    
    //支払方法:0=WeChat決済,1=サービス回数
    const PAY_MOD_WX = 0;
    //サービス回数
    const PAY_MOD_SERVICE = 1;
    //ポイント
    const PAY_MOD_SCORE = 2;

    const PAY_MOD_LIST = [
        self::PAY_MOD_WX => 'WeChat決済',
        self::PAY_MOD_SERVICE => 'サービス回数',
        self::PAY_MOD_SCORE => 'ポイント交換',
    ];

    //サービス種別  カテゴリ:1=団体購入注文,2=ゴミ代理廃棄,3=荷物代理受取,4=ポイント交換
    const SERVICE_TYPE_GROUP_BUY = 1;

    const SERVICE_TYPE_WASTE = 2;

    const SERVICE_TYPE_FASTMAIL = 3;

    const SERVICE_TYPE_EXCHANGE = 4;

    const SERVICE_TYPE_LIST = [
        self::SERVICE_TYPE_GROUP_BUY => '団体購入',
        self::SERVICE_TYPE_WASTE => 'ゴミ代理廃棄',
        self::SERVICE_TYPE_FASTMAIL => '荷物代理受取',
        self::SERVICE_TYPE_EXCHANGE => 'ポイント交換',
    ];

    const SERVICE_TYPE_WASTE_TEXT = 'waste';

    const SERVICE_TYPE_FASTMAIL_TEXT = 'fastmail';

    const SERVICE_TYPE_TEXT_VALUE = [
        self::SERVICE_TYPE_WASTE_TEXT => self::SERVICE_TYPE_WASTE,
        self::SERVICE_TYPE_FASTMAIL_TEXT => self::SERVICE_TYPE_FASTMAIL,
    ];

    //性別
    const GENDER_UNKNOWN = 0;

    const GENDER_MALE = 1;

    const GENDER_FEMALE = 2;

    const GENDER_LIST = [
        self::GENDER_MALE => '男性',
        self::GENDER_FEMALE => '女性',
    ];
    
 
    const ORDER_STATUS_1 = 1;

    const ORDER_STATUS_2 = 2;
  
    const ORDER_STATUS_3 = 3;
    const ORDER_STATUS_4 = 4;
    const ORDER_STATUS_5 = 5;
    const ORDER_STATUS_6 = 6;
    

    const ORDER_STATUS_LIST = [
        self::ORDER_STATUS_1 => '申し込み承認中',
        self::ORDER_STATUS_2 => '申し込み承認',
        self::ORDER_STATUS_3 => '査定進行中',
        self::ORDER_STATUS_4 => '取引完了',
        self::ORDER_STATUS_5 => '取引キャンセル申請',
        self::ORDER_STATUS_6 => '取引キャンセル',
        
    ];

    const ORDER_STATUS_ADMIN_1 = 1;
    const ORDER_STATUS_ADMIN_2 = 2;
    const ORDER_STATUS_ADMIN_3 = 3;
    const ORDER_STATUS_ADMIN_4 = 4;
    const ORDER_STATUS_ADMIN_5 = 5;
    const ORDER_STATUS_ADMIN_6 = 6;
    const ORDER_STATUS_ADMIN_7 = 7;
    const ORDER_STATUS_ADMIN_8 = 8;
    const ORDER_STATUS_ADMIN_9 = 9;
    const ORDER_STATUS_ADMIN_10 = 10;
    const ORDER_STATUS_ADMIN_11 = 11;
    const ORDER_STATUS_ADMIN_12 = 12;
    const ORDER_STATUS_ADMIN_13 = 13;
    const ORDER_STATUS_ADMIN_14 = 14;
    
    const ORDER_STATUS_ADMIN_LIST = [
        self::ORDER_STATUS_ADMIN_1 => '新規申込',
        self::ORDER_STATUS_ADMIN_2 => '申込交渉中',
        self::ORDER_STATUS_ADMIN_3 => '申込承認済および到着待ち中',
        self::ORDER_STATUS_ADMIN_4 => '商品を受け取った',
        self::ORDER_STATUS_ADMIN_5 => '査定交渉中',
        self::ORDER_STATUS_ADMIN_6 => '査定確認',
        self::ORDER_STATUS_ADMIN_7 => '入庫完了',
        self::ORDER_STATUS_ADMIN_8 => '入金完了',
        self::ORDER_STATUS_ADMIN_9 => '取引キャンセル交渉中',
        self::ORDER_STATUS_ADMIN_10 => '取引キャンセル返品中',
        self::ORDER_STATUS_ADMIN_11 => '取引キャンセル返金返品中',
        self::ORDER_STATUS_ADMIN_12 => '取引キャンセル返品完了返金中',
        self::ORDER_STATUS_ADMIN_13 => '取引キャンセル返金完了返品中',
        self::ORDER_STATUS_ADMIN_14 => '取引キャンセルプロセス完了',
    ];

    const ORDER_STATUS_DY_ADMIN_LIST = [
        self::ORDER_STATUS_ADMIN_1 => self::ORDER_STATUS_1,
        self::ORDER_STATUS_ADMIN_2 => self::ORDER_STATUS_1,
        self::ORDER_STATUS_ADMIN_3 => self::ORDER_STATUS_2,
        self::ORDER_STATUS_ADMIN_4 => self::ORDER_STATUS_3,
        self::ORDER_STATUS_ADMIN_5 => self::ORDER_STATUS_3,
        self::ORDER_STATUS_ADMIN_6 => self::ORDER_STATUS_3,
        self::ORDER_STATUS_ADMIN_7 => self::ORDER_STATUS_3,
        self::ORDER_STATUS_ADMIN_8 => self::ORDER_STATUS_4,
        self::ORDER_STATUS_ADMIN_9 => self::ORDER_STATUS_5,
        self::ORDER_STATUS_ADMIN_10 => self::ORDER_STATUS_6,
        self::ORDER_STATUS_ADMIN_11 => self::ORDER_STATUS_6,
        self::ORDER_STATUS_ADMIN_12 => self::ORDER_STATUS_6,
        self::ORDER_STATUS_ADMIN_13 => self::ORDER_STATUS_6,
        self::ORDER_STATUS_ADMIN_14 => self::ORDER_STATUS_6,
    ];

    const ORDER_STATUS_SCORE_LIST = [
        self::ORDER_STATUS_NO_PAY => '交換待ち',
        self::ORDER_STATUS_YES_PAY => '発送待ち',
        self::ORDER_STATUS_COMPLETE => '完了',
    ];

    //ユーザー充值/出金履歴
    //ステータス 0処理待ち1成功 2失敗
    const RECHARGE_STATUS_PENDING = 0;
    //成功
    const RECHARGE_STATUS_SUCCESS = 1;
    //失敗
    const RECHARGE_STATUS_FAIL = 2;
    //処理中
    const RECHARGE_STATUS_HANDLE = 3;

    const RECHARGE_STATUS_LIST = [
        self::RECHARGE_STATUS_PENDING => '処理待ち',
        self::RECHARGE_STATUS_SUCCESS => '成功',
        self::RECHARGE_STATUS_FAIL => '失敗',
        self::RECHARGE_STATUS_HANDLE => '処理中',
    ];


    /*支払方法*/
    //残高支払い
    const BALANCE_PAYMENT = 0;
    //凍結残高支払い
    const FROZEN_BALANCE_PAYMENT = 1;
    //その他の支払い
    const OTHER_PAYMENT = 2;
    //WeChat決済
    const WX_PAYMENT = 3;
    //クイック決済
    const QUICK_PAYMENT = 4;

    const PAYMENT_LIST = [
        self::BALANCE_PAYMENT => '残高支払い',
        self::FROZEN_BALANCE_PAYMENT => '凍結残高支払い',
        self::OTHER_PAYMENT => 'Alipay支払い',
        self::WX_PAYMENT => 'WeChat決済',
        self::QUICK_PAYMENT => 'クイック決済',
    ];

    /*残高タイプ*/
    const MONEY_TYPE_BALANCE = 0;

    const MONEY_TYPE_FROZEN_BALANCE = 1;


    /* 支払い状況*/
    const YES_PAY = 1;

    const NOT_PAY = 0;

    const MONEY_LOG_TYPE_PROFIT = 0;

    const MONEY_LOG_TYPE_WITHDRAWAL =1;

    const MONEY_LOG_TYPE_EXPEND =2;

    const MONEY_LOG_TYPE_LIST = [
        self::MONEY_LOG_TYPE_PROFIT => '収益',
        self::MONEY_LOG_TYPE_WITHDRAWAL => '出金',
        self::MONEY_LOG_TYPE_EXPEND => '支出',
    ];

    const SCORE_LOG_TYPE_PROFIT = 0;

    const SCORE_LOG_TYPE_EXCHANGE =1;

    const SCORE_LOG_TYPE_EXPEND =2;

    const SCORE_LOG_TYPE_LIST = [
        self::MONEY_LOG_TYPE_PROFIT => '収益',
        self::SCORE_LOG_TYPE_EXCHANGE => '交換',
        self::MONEY_LOG_TYPE_EXPEND => '支出',
    ];

   
    const IS_INCOME = 0;

    const IS_INCOME_YES = 1;

    //支払い状況
    const IS_PAY_NO = 0;

    const IS_PAY_YES = 1;

    const IS_PAY_LIST = [
        self::IS_PAY_NO => '未払い',
        self::IS_PAY_YES => '支払い済み',
    ];

    

    const USER_AUTH_SUCCESS_MSG = '認証申請が承認されました,ライダー画面にてご確認ください';

    const USER_AUTH_FAIL_MSG = '認証申請は承認されませんでした,理由:$text';

    const WITHDRAWAL_MSG_SUCCESS = '出金申請が承認されました,振込が完了しました';

    const WITHDRAWAL_MSG_FAIL = '出金申請は承認されませんでした,金額は返金されました';

    const POINTSMALL_REFUND_MSG_REFUND = 'お客様の返品・交換-返品申請が承認されました,ライダーが集荷に伺います';

    const POINTSMALL_REFUND_MSG_CHANGE = 'お客様の返品・交換-交換申請が承認されました,ライダーが集荷に伺います';

    const POINTSMALL_REFUND_MSG_FAIL = '返品・交換申請は承認されませんでした';

    const POINTSMALL_REFUND_MSG_REFUND_RECEIVE = 'お客様の返品・交換-返品完了,ポイントは返還されました';

    const RIDER_APPLYFOR_MSG_SUCCESS = 'ライダー申請が承認されました';

    const RIDER_APPLYFOR_MSG_FAIL = 'ライダー申請は承認されませんでした,理由:$text';

    const FEEDBACK_REPLY = 'お客様からのフィードバック【$title】,管理者から返信がありました:$content';
    
 
}
<?php
return [
  # サイトドメイン名
  'WEB_DOMAIN_NAME' => 'http://192.168.1.22:8082',
  # h5ドメイン名
  'WEB_H5_DOMAIN_NAME' => 'http://192.168.1.22:8081/h5',
  'share' => '/share/',
  # 画像のURL
  'WEB_UPLOAD_URL' => '/uploads/',
   'source' => 'コミュニティサービスプラットフォーム',
   'appid' => '',
   'secret' => '',
   'goods_type' => [1 => '新品', 2 => '中古'],
   'persion_type_list' => [1 => '個人', 2 => '法人'],
   'pay_mode_list' => [1 => '現金払い ', 2=>'銀行振込 '],
   'bank_account_type' => [1=>'普通預金',2=>'当座預金 '],
    'order_status_list' => [
        1 => '申し込み承認中',
        2 => '申し込み承認',
        3 => '査定進行中',
        4 => '取引完了',
        5 => '取引キャンセル申請',
        6 => '取引キャンセル',
    ],
];
<?php

// +----------------------------------------------------------------------
// | ThinkPHP [ WE CAN DO IT JUST THINK ]
// +----------------------------------------------------------------------
// | Copyright (c) 2006~2016 http://thinkphp.cn All rights reserved.
// +----------------------------------------------------------------------
// | Licensed ( http://www.apache.org/licenses/LICENSE-2.0 )
// +----------------------------------------------------------------------
// | Author: liu21st <liu21st@gmail.com>
// +----------------------------------------------------------------------
use think\Route;
Route::any('ylindex/:id','index/index/ylindex');
Route::any('ylindex_empty','index/index/ylindex_empty');
Route::rule('notify/:type','api/pay/notify');
Route::rule('returnx/:type','api/pay/returnx');
Route::rule('goods/[:category_id]/[:category_second]/[:category_three]','index/index/goods');
Route::rule('news','index/index/news');
Route::rule('shop','index/index/shop');
Route::rule('buy_way','index/index/buy_way');
Route::rule('guide','index/index/guide');
Route::rule('contactus','index/index/contactus');
Route::rule('user','index/user/index');
Route::rule('user/shopping','index/user/shopping');
Route::rule('user/order','index/user/order');
Route::rule('applyfor/[:type]','index/user/applyfor');
Route::rule('user/mail','index/user/mail_applyfor');
Route::rule('logout','index/user/logout');
Route::rule('applyfor_complete','index/user/applyfor_complete');
Route::rule('faq','index/index/faq');
Route::rule('trading_law','index/index/trading_law');
Route::rule('use_terms','index/index/use_terms');
Route::rule('privacy_policy','index/index/privacy_policy');
Route::rule('gdetails/:id','index/index/goods_details');
Route::rule('ndetails/:id','index/index/news_details');
Route::rule('odetails/:id','index/user/order_details');

// SEO - Sitemap
Route::rule('sitemap.xml','index/sitemap/index');

// GoodsPrice API 路由 - 使用 rule 格式
Route::rule('api/goodsprice/test', 'api/goods_price/test');
Route::rule('api/goodsprice/list', 'api/goods_price/list');
Route::rule('api/goodsprice/detail', 'api/goods_price/detail');
Route::rule('api/goodsprice/update', 'api/goods_price/update');
Route::rule('api/goodsprice/setprices', 'api/goods_price/setprices');
Route::rule('api/goodsprice/gettoken', 'api/goods_price/gettoken');
Route::rule('api/goodsprice/listusers', 'api/goods_price/listusers');
Route::rule('api/goodsprice/createtestuser', 'api/goods_price/createtestuser');

return [
    //エイリアス設定,エイリアスはコントローラーへのマッピングのみ可能で、アクセス時には必ずリクエストメソッドを付加する必要があります
    '__alias__'   => [
    ],
    //変数ルール
    '__pattern__' => [
    ],
//        ドメインをモジュールにバインド
//        '__domain__'  => [
//            'admin' => 'admin',
//            'api'   => 'api',
//        ],
];

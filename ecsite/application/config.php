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
use think\Env;

return [
    // +----------------------------------------------------------------------
    // | アプリケーション設定
    // +----------------------------------------------------------------------
    // アプリケーションの名前空間
    'app_namespace'          => 'app',
    // アプリケーションデバッグモード
    'app_debug'              => Env::get('app.debug', false),
    // アプリケーションTrace
    'app_trace'              => Env::get('app.trace', false),
    // アプリケーションモードステータス
    'app_status'             => '',
    // マルチモジュール対応かどうか
    'app_multi_module'       => true,
    // エントリでモジュールを自動バインド
    'auto_bind_module'       => false,
    // 登録されたルート名前空間
    'root_namespace'         => [],
    // 拡張関数ファイル
    'extra_file_list'        => [THINK_PATH . 'helper' . EXT],
    // デフォルト出力タイプ
    'default_return_type'    => 'html',
    // デフォルトAJAX データ返却フォーマット,選択可能json xml ...
    'default_ajax_return'    => 'json',
    // デフォルトJSONPフォーマット返却時の処理メソッド
    'default_jsonp_handler'  => 'jsonpReturn',
    // デフォルトJSONP処理メソッド
    'var_jsonp_handler'      => 'callback',
    // デフォルトタイムゾーン
    'default_timezone'       => 'Asia/Tokyo',
    // 多言語を有効にするかどうか
    'lang_switch_on'         => false,
    // デフォルトのグローバルフィルターメソッド 複数指定する場合はカンマ区切り
    'default_filter'         => '',
    // デフォルト言語
    'default_lang'           => 'zh-cn',
    // 許可される言語リスト
    'allow_lang_list'        => ['zh-cn', 'en'],
    // アプリケーションクラスライブラリのサフィックス
    'class_suffix'           => false,
    // コントローラークラスのサフィックス
    'controller_suffix'      => false,
    // 取得IPの変数
    'http_agent_ip'          => 'REMOTE_ADDR',
    // +----------------------------------------------------------------------
    // | モジュール設定
    // +----------------------------------------------------------------------
    // デフォルトモジュール名
    'default_module'         => 'index',
    // アクセス禁止モジュール
    'deny_module_list'       => ['common'],
    // デフォルトコントローラー名
    'default_controller'     => 'Index',
    // デフォルトアクション名
    'default_action'         => 'index',
    // デフォルトバリデーター
    'default_validate'       => '',
    // デフォルトの空コントローラー名
    'empty_controller'       => 'Error',
    // アクションメソッドのサフィックス
    'action_suffix'          => '',
    // コントローラーを自動検索
    'controller_auto_search' => true,
    // +----------------------------------------------------------------------
    // | URL設定を行う
    // +----------------------------------------------------------------------
    // PATHINFO変数名 互換モード用
    'var_pathinfo'           => 's',
    // 互換PATH_INFO取得
    'pathinfo_fetch'         => ['ORIG_PATH_INFO', 'REDIRECT_PATH_INFO', 'REDIRECT_URL'],
    // pathinfo区切り文字
    'pathinfo_depr'          => '/',
    // URL擬似静的サフィックス
    'url_html_suffix'        => 'html',
    // URL通常方式パラメーター 自動生成用
    'url_common_param'       => false,
    // URLパラメーター方式 0 名前ごとのペアで解析 1 順番どおりに解析
    'url_param_type'         => 0,
    // ルーティングを有効にするかどうか
    'url_route_on'           => true,
    // ルーティングで完全一致を使用
    'route_complete_match'   => false,
    // ルーティング設定ファイル（複数設定をサポート）
    'route_config_file'      => ['route'],
    // ルーティングの強制使用の有無
    'url_route_must'         => false,
    // ドメインデプロイ
    'url_domain_deploy'      => false,
    // ドメインルート，例thinkphp.cn
    'url_domain_root'        => '',
    // 自動変換するかどうかURL内のコントローラー名とアクション名
    'url_convert'            => true,
    // デフォルトのアクセスコントローラー層
    'url_controller_layer'   => 'controller',
    // フォームリクエストタイプ偽装変数
    'var_method'             => '_method',
    // フォームajax偽装変数
    'var_ajax'               => '_ajax',
    // フォームpjax偽装変数
    'var_pjax'               => '_pjax',
    // リクエストキャッシュを有効にするかどうか true自動キャッシュ リクエストキャッシュ規則の設定をサポート
    'request_cache'          => false,
    // リクエストキャッシュ有効期間
    'request_cache_expire'   => null,
    // +----------------------------------------------------------------------
    // | テンプレート設定
    // +----------------------------------------------------------------------
    'template'               => [
        // テンプレートエンジンタイプ サポート php think サポート扩展
        'type'         => 'Think',
        // テンプレートパス
        'view_path'    => '',
        // テンプレート拡張子
        'view_suffix'  => 'html',
        // テンプレートファイル名区切り文字
        'view_depr'    => DS,
        // テンプレートエンジン通常タグの開始マーカー
        'tpl_begin'    => '{',
        // テンプレートエンジン通常タグの終了マーカー
        'tpl_end'      => '}',
        // タグライブラリタグの開始マーカー
        'taglib_begin' => '{',
        // タグライブラリタグの終了マーカー
        'taglib_end'   => '}',
        'tpl_cache'    => true,
    ],
    // ビュー出力文字列の内容置換,空欄の場合は自動計算されます
    'view_replace_str'       => [
        '__PUBLIC__' => '',
        '__ROOT__'   => '',
        '__CDN__'    => '',
    ],
    // デフォルトジャンプページに対応するテンプレートファイル
    'dispatch_success_tmpl'  => APP_PATH . 'common' . DS . 'view' . DS . 'tpl' . DS . 'dispatch_jump.tpl',
    'dispatch_error_tmpl'    => APP_PATH . 'common' . DS . 'view' . DS . 'tpl' . DS . 'dispatch_jump.tpl',
    // +----------------------------------------------------------------------
    // | 例外およびエラー設定
    // +----------------------------------------------------------------------
    // 例外ページのテンプレートファイル
    'exception_tmpl'         => APP_PATH . 'common' . DS . 'view' . DS . 'tpl' . DS . 'think_exception.tpl',
    // カスタムエラーコードテンプレート
    'http_exception_template'    =>  [
        // 定義する404エラー時のテンプレートレンダリング
        // 404 =>  APP_PATH . 'common/view/tpl/404.tpl',
    ],
    // エラー表示メッセージ,デバッグモード以外で有効
    'error_message'          => '現在、このページには一時的にアクセスできません',
    // エラー情報を表示
    'show_error_msg'         => false,
    // 例外処理handleクラス 空の場合は使用 \think\exception\Handle
    'exception_handle'       => '',
    // +----------------------------------------------------------------------
    // | ログ設定
    // +----------------------------------------------------------------------
    'log'                    => [
        // ログ記録方式，内蔵 file socket 拡張をサポート
        'type'  => 'File',
        // ログ保存ディレクトリ
        'path'  => LOG_PATH,
        // ログ記録レベル
        'level' => [],
    ],
    // +----------------------------------------------------------------------
    // | Trace設定を行う 有効 app_trace 後 有効
    // +----------------------------------------------------------------------
    'trace'                  => [
        // 内蔵Html Console 拡張をサポート
        'type' => 'Html',
    ],
    // +----------------------------------------------------------------------
    // | キャッシュ設定
    // +----------------------------------------------------------------------
    'cache'                  => [
        // ドライバー方式
        'type'   => 'File',
        // キャッシュ保存ディレクトリ
        'path'   => CACHE_PATH,
        // キャッシュプレフィックス
        'prefix' => '',
        // キャッシュ有効期限 0は永久キャッシュを表します
        'expire' => 0,
    ],
    // +----------------------------------------------------------------------
    // | セッション設定
    // +----------------------------------------------------------------------
    'session'                => [
        'id'             => '',
        // SESSION_IDの送信変数,解決flashアップロードのクロスドメイン
        'var_session_id' => '',
        // SESSION プレフィックス
        'prefix'         => 'think',
        // ドライバー方式 サポートredis memcache memcached
        'type'           => '',
        // 自動的に開始するかどうか SESSION
        'auto_start'     => true,
        //'cache_limiter'=>''
    ],
    // +----------------------------------------------------------------------
    // | Cookie設定を行う
    // +----------------------------------------------------------------------
    'cookie'                 => [
        // cookie 名前プレフィックス
        'prefix'    => '',
        // cookie 保存時間
        'expire'    => 0,
        // cookie 保存パス
        'path'      => '/',
        // cookie 有効ドメイン
        'domain'    => '',
        //  cookie セキュア転送を有効にする
        'secure'    => false,
        // httponly設定を行う
        'httponly'  => '',
        // 使用するかどうか setcookie
        'setcookie' => true,
    ],
    //ページネーション設定
    'paginate'               => [
        'type'      => 'bootstrap',
        'var_page'  => 'page',
        'list_rows' => 15,
    ],
    //認証コード設定
    'captcha'                => [
        // 認証コードの文字集合
        'codeSet'  => '2345678abcdefhijkmnpqrstuvwxyzABCDEFGHJKLMNPQRTUVWXY',
        // 認証コードの文字サイズ(px)
        'fontSize' => 18,
        // ノイズ用の曲線を描画するかどうか
        'useCurve' => false,
        //中国語の認証コードを使用する
        'useZh'    => false,
        // 認証コード画像の高さ
        'imageH'   => 40,
        // 認証コード画像の幅
        'imageW'   => 130,
        // 認証コードの桁数
        'length'   => 4,
        // 認証成功後にリセットするかどうか
        'reset'    => true
    ],
    // +----------------------------------------------------------------------
    // | Token設定を行う
    // +----------------------------------------------------------------------
    'token'                  => [
        // ドライバー方式
        'type'     => 'Mysql',
        // キャッシュプレフィックス
        'key'      => 'xMBRkdt0SN7bzPjsArTUZ2LvlDFEKf81',
        // 暗号化方式
        'hashalgo' => 'ripemd160',
        // キャッシュ有効期限 0は永久キャッシュを表します
        'expire'   => 0,
    ],
    //FastAdmin設定
    'fastadmin'              => [
        //フロント会員センターを有効にするかどうか
        'usercenter'            => true,
        //会員登録時の認証コード種別email/mobile/wechat/text/false
        'user_register_captcha' => 'text',
        //ログイン認証コード
        'login_captcha'         => false,
        //ログイン失敗が10回を超えた場合1日後に再試行
        'login_failure_retry'   => true,
        //同一アカウントは同時に一か所でしかログインできないようにするかどうか
        'login_unique'          => false,
        //有効かどうかIPIP変動検知
        'loginip_check'         => true,
        //ログインページのデフォルト背景画像
        'login_background'      => "",
        //多階層メニュー ナビゲーションを有効にするかどうか
        'multiplenav'           => false,
        //マルチタブを有効にするかどうか(多階層メニュー有効時のみ有効)
        'multipletab'           => true,
        //子メニューをデフォルト表示するかどうか
        'show_submenu'          => false,
        //管理画面のスキン,空欄の場合は使用しますskin-black-blue
        'adminskin'             => '',
        //管理画面でパンくずリストを有効にするかどうか
        'breadcrumb'            => false,
        //不明な提供元のプラグイン圧縮ファイルを許可するかどうか
        'unknownsources'        => false,
        //プラグインの有効化・無効化時に対応するグローバルファイルをバックアップするかどうか
        'backup_global_files'   => true,
        //バックエンドの自動ログ記録を有効にするかどうか
        'auto_record_log'       => true,
        //プラグインクリーンモード，プラグイン有効化後、プラグインディレクトリ内のapplication、publicとassetsフォルダーを削除するかどうか
        'addon_pure_mode'       => true,
        //クロスドメインを許可するドメイン名,複数指定する場合は,で区切る,*で全許可（一時的なテスト用）
        'cors_request_domain'   => '*',
        //バージョン番号
        'version'               => '1.5.3.20250217',
        //APIAPIエンドポイントURL
        'api_url'               => 'https://api.fastadmin.net',
    ],
];

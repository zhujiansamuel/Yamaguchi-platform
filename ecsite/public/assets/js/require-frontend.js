require.config({
    urlArgs: "v=" + requirejs.s.contexts._.config.config.site.version,
    packages: [{
        name: 'moment',
        location: '../libs/moment',
        main: 'moment'
    }],
    //パッケージ圧縮時にinclude内のモジュールをメインファイルに結合します
    include: ['css', 'layer', 'toastr', 'fast', 'frontend', 'frontend-init', 'table', 'form', 'dragsort', 'selectpage'],
    paths: {
        'lang': "empty:",
        'form': 'require-form',
        'table': 'require-table',
        'upload': 'require-upload',
        'dropzone': 'dropzone.min',
        'echarts': 'echarts.min',
        'echarts-theme': 'echarts-theme',
        'adminlte': 'adminlte',
        'bootstrap-table-commonsearch': 'bootstrap-table-commonsearch',
        'bootstrap-table-template': 'bootstrap-table-template',
        //
        // 以下の包从bowerのlibsディレクトリから読み込みます
        'jquery': '../libs/jquery/dist/jquery.min',
        'bootstrap': '../libs/bootstrap/dist/js/bootstrap.min',
        'bootstrap-datetimepicker': '../libs/eonasdan-bootstrap-datetimepicker/build/js/bootstrap-datetimepicker.min',
        'bootstrap-daterangepicker': '../libs/bootstrap-daterangepicker/daterangepicker',
        'bootstrap-select': '../libs/bootstrap-select/dist/js/bootstrap-select.min',
        'bootstrap-select-lang': '../libs/bootstrap-select/dist/js/i18n/defaults-zh_CN',
        'bootstrap-table': '../libs/bootstrap-table/dist/bootstrap-table.min',
        'bootstrap-table-export': '../libs/bootstrap-table/dist/extensions/export/bootstrap-table-export.min',
        'bootstrap-table-fixed-columns': '../libs/bootstrap-table/dist/extensions/fixed-columns/bootstrap-table-fixed-columns',
        'bootstrap-table-mobile': '../libs/bootstrap-table/dist/extensions/mobile/bootstrap-table-mobile',
        'bootstrap-table-lang': '../libs/bootstrap-table/dist/locale/bootstrap-table-zh-CN',
        'bootstrap-table-jumpto': '../libs/bootstrap-table/dist/extensions/page-jumpto/bootstrap-table-jumpto',
        'tableexport': '../libs/tableExport.jquery.plugin/tableExport.min',
        'dragsort': '../libs/fastadmin-dragsort/jquery.dragsort',
        'sortable': '../libs/Sortable/Sortable.min',
        'addtabs': '../libs/fastadmin-addtabs/jquery.addtabs',
        'slimscroll': '../libs/jquery-slimscroll/jquery.slimscroll',
        'validator': '../libs/nice-validator/dist/jquery.validator',
        'validator-lang': '../libs/nice-validator/dist/local/zh-CN',
        'toastr': '../libs/toastr/toastr',
        'jstree': '../libs/jstree/dist/jstree.min',
        'layer': '../libs/fastadmin-layer/dist/layer',
        'cookie': '../libs/jquery.cookie/jquery.cookie',
        'cxselect': '../libs/fastadmin-cxselect/js/jquery.cxselect',
        'template': '../libs/art-template/dist/template-native',
        'selectpage': '../libs/fastadmin-selectpage/selectpage',
        'citypicker': '../libs/fastadmin-citypicker/dist/js/city-picker.min',
        'citypicker-data': '../libs/fastadmin-citypicker/dist/js/city-picker.data'
    },
    // shim依存関係の設定
    shim: {
        'addons': ['frontend'],
        'bootstrap': ['jquery'],
        'bootstrap-table': {
            deps: ['bootstrap'],
            exports: '$.fn.bootstrapTable'
        },
        'bootstrap-table-lang': {
            deps: ['bootstrap-table'],
            exports: '$.fn.bootstrapTable.defaults'
        },
        'bootstrap-table-export': {
            deps: ['bootstrap-table'],
            exports: '$.fn.bootstrapTable.defaults'
        },
        'bootstrap-table-fixed-columns': {
            deps: ['bootstrap-table'],
            exports: '$.fn.bootstrapTable.defaults'
        },
        'bootstrap-table-mobile': {
            deps: ['bootstrap-table'],
            exports: '$.fn.bootstrapTable.defaults'
        },
        'bootstrap-table-advancedsearch': {
            deps: ['bootstrap-table'],
            exports: '$.fn.bootstrapTable.defaults'
        },
        'bootstrap-table-commonsearch': {
            deps: ['bootstrap-table'],
            exports: '$.fn.bootstrapTable.defaults'
        },
        'bootstrap-table-template': {
            deps: ['bootstrap-table', 'template'],
            exports: '$.fn.bootstrapTable.defaults'
        },
        'bootstrap-table-jumpto': {
            deps: ['bootstrap-table'],
            exports: '$.fn.bootstrapTable.defaults'
        },
        'tableexport': {
            deps: ['jquery'],
            exports: '$.fn.extend'
        },
        'slimscroll': {
            deps: ['jquery'],
            exports: '$.fn.extend'
        },
        'adminlte': {
            deps: ['bootstrap', 'slimscroll'],
            exports: '$.AdminLTE'
        },
        'bootstrap-daterangepicker': [
            'moment/locale/zh-cn'
        ],
        'bootstrap-datetimepicker': [
            'moment/locale/zh-cn',
        ],
        'bootstrap-select-lang': ['bootstrap-select'],
        'jstree': ['css!../libs/jstree/dist/themes/default/style.css'],
        'validator-lang': ['validator'],
        'citypicker': ['citypicker-data', 'css!../libs/fastadmin-citypicker/dist/css/city-picker.css']
    },
    baseUrl: requirejs.s.contexts._.config.config.site.cdnurl + '/assets/js/', //アセットのベースパス
    map: {
        '*': {
            'css': '../libs/require-css/css.min'
        }
    },
    waitSeconds: 60,
    charset: 'utf-8' // ファイルエンコード
});

require(['jquery', 'bootstrap'], function ($, undefined) {
    //初期設定
    var Config = requirejs.s.contexts._.config.config;
    //をConfigグローバルへレンダリング
    window.Config = Config;
    // 言語パックのパスを設定
    var paths = {};
    paths['lang'] = Config.moduleurl + '/ajax/lang?callback=define&controllername=' + Config.controllername + '&lang=' + Config.language;
    // ディレクトリ競合を回避
    paths['frontend/'] = 'frontend/';
    require.config({paths: paths});

    // 初期化
    $(function () {
        require(['fast'], function (Fast) {
            require(['frontend', 'frontend-init', 'addons'], function (Frontend, Addons) {
                //該当モジュールを読み込み
                if (Config.jsname) {
                    require([Config.jsname], function (Controller) {
                        Controller[Config.actionname] != undefined && Controller[Config.actionname]();
                    }, function (e) {
                        console.error(e);
                        // ここでモジュール読み込みエラーを捕捉可能
                    });
                }
            });
        });
    });
});

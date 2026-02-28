/**
 * Bootstrap Table Chinese translation
 * Author: Zhixin Wen<wenzhixin2010@gmail.com>
 */
(function ($) {
    'use strict';

    $.fn.bootstrapTable.locales['zh-CN'] = {
        formatLoadingMessage: function () {
            return 'データを読み込んでいます，しばらくお待ちください……';
        },
        formatRecordsPerPage: function (pageNumber) {
            return '1ページあたり ' + pageNumber + ' 件のレコード';
        },
        formatShowingRows: function (pageFrom, pageTo, totalRows) {
            return '表示中:  ' + pageFrom + '  から  ' + pageTo + ' 件のレコード，合計 ' + totalRows + ' 件のレコード';
        },
        formatDetailPagination: function (totalRows) {
            return '合計 ' + totalRows + ' 件のレコード';
        },
        formatSearch: function () {
            return '検索';
        },
        formatNoMatches: function () {
            return '一致するレコードが見つかりません';
        },
        formatPaginationSwitch: function () {
            return '非表示/ページネーションを表示';
        },
        formatRefresh: function () {
            return '更新';
        },
        formatToggle: function () {
            return '切り替え';
        },
        formatColumns: function () {
            return '列';
        },
        formatExport: function () {
            return 'データをエクスポート';
        },
        formatClearFilters: function () {
            return 'フィルターをクリア';
        }
    };

    $.extend($.fn.bootstrapTable.defaults, $.fn.bootstrapTable.locales['zh-CN']);

})(jQuery);

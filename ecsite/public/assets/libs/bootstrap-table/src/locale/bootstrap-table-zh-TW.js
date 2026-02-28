/**
 * Bootstrap Table Chinese translation
 * Author: Zhixin Wen<wenzhixin2010@gmail.com>
 */
(function ($) {
    'use strict';

    $.fn.bootstrapTable.locales['zh-TW'] = {
        formatLoadingMessage: function () {
            return 'データを読み込んでいます，しばらくお待ちください……';
        },
        formatRecordsPerPage: function (pageNumber) {
            return 'ページあたり ' + pageNumber + ' 件を表示';
        },
        formatShowingRows: function (pageFrom, pageTo, totalRows) {
            return '表示中 ' + pageFrom + '  から  ' + pageTo + ' 件を表示，合計 ' + totalRows + ' 件を表示';
        },
        formatDetailPagination: function (pageFrom, pageTo, totalRows) {
            return '合計 ' + totalRows + ' 件を表示';
        },
        formatSearch: function () {
            return '検索';
        },
        formatNoMatches: function () {
            return '一致する結果が見つかりません';
        },
        formatPaginationSwitch: function () {
            return '非表示/ページを表示';
        },
        formatRefresh: function () {
            return '再読み込み';
        },
        formatToggle: function () {
            return '切り替え';
        },
        formatColumns: function () {
            return '列';
        }
    };

    $.extend($.fn.bootstrapTable.defaults, $.fn.bootstrapTable.locales['zh-TW']);

})(jQuery);

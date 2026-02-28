/**
 * をBootstrapTableの行をカスタムテンプレートでレンダリング
 * 
 * @author: karson
 * @version: v0.0.1
 *
 * @update 2017-06-24 <http://github.com/karsonzhang/fastadmin>
 */

!function ($) {
    'use strict';

    $.extend($.fn.bootstrapTable.defaults, {
        //テンプレートレンダリングを有効にするかどうか
        templateView: false,
        //データフォーマット用テンプレートIDIDまたはフォーマット関数
        templateFormatter: "itemtpl",
        //に追加する親要素のclass
        templateParentClass: "row row-flex",
        //に対してtableに追加するclass
        templateTableClass: "table-template",

    });

    var BootstrapTable = $.fn.bootstrapTable.Constructor,
            _initContainer = BootstrapTable.prototype.initContainer,
            _initBody = BootstrapTable.prototype.initBody,
            _initRow = BootstrapTable.prototype.initRow;

    BootstrapTable.prototype.initContainer = function () {
        _initContainer.apply(this, Array.prototype.slice.apply(arguments));
        var that = this;
        if (!that.options.templateView) {
            return;
        }
        that.options.cardView = true;

    };

    BootstrapTable.prototype.initBody = function () {
        var that = this;
        $.extend(that.options, {
            showHeader: !that.options.templateView ? $.fn.bootstrapTable.defaults.showHeader : false,
            showFooter: !that.options.templateView ? $.fn.bootstrapTable.defaults.showFooter : false,
        });
        $(that.$el).toggleClass(that.options.templateTableClass, that.options.templateView);

        _initBody.apply(this, Array.prototype.slice.apply(arguments));

        if (!that.options.templateView) {
            return;
        } else {
            //〜のためBootstrapはテーブルをベースとしているためTableの，親コンテナを1つ追加
            $("> *:not(.no-records-found)", that.$body).wrapAll($("<div />").addClass(that.options.templateParentClass));
        }
    };

    BootstrapTable.prototype.initRow = function (item, i, data, parentDom) {
        var that = this;
        //有効でない場合はネイティブのinitRowメソッド
        if (!that.options.templateView) {
            return _initRow.apply(that, Array.prototype.slice.apply(arguments));
        }
        var $content = '';
        if (typeof that.options.templateFormatter === 'function') {
            $content = that.options.templateFormatter.call(that, item, i, data);
        } else {
            var Template = require('template');
            $content = Template(that.options.templateFormatter, {item: item, i: i, data: data});
        }
        return $content;
    };

}(jQuery);

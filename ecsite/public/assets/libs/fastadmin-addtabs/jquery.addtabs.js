/**
 * http://git.oschina.net/hbbcs/bootStrap-addTabs
 * Created by joe on 2015-12-19.
 * Modified by FastAdmin
 */

(function ($) {

    $.fn.addtabs = function (options) {
        var obj = $(this);
        options = $.extend({
            content: '', //すべてのページを直接指定TABS内容
            close: true, //閉じることができるかどうか
            monitor: 'body', //監視する領域
            nav: '.nav-addtabs',
            tab: '.tab-addtabs',
            iframeUse: true, //使用iframeかどうかajax
            simple: false, //シンプルモードを有効にするかどうか，シンプルモードでは有効にしないnavとtab
            iframeHeight: $(window).height() - 50, //固定TAB中IFRAME高さ,必要に応じて自分で変更
            iframeForceRefresh: false, //クリック後に対応するを強制的に読み込むiframe
            iframeForceRefreshTable: false, //クリック後に対応するを強制的にリフレッシュiframeの中table
            callback: function () {
                //閉じた後のコールバック関数
            }
        }, options || {});
        var navobj = $(options.nav);
        var tabobj = $(options.tab);
        if (history.pushState) {
            //ブラウザの進む・戻るイベント
            $(window).on("popstate", function (e) {
                var state = e.originalEvent.state;
                if (state) {
                    $("a[addtabs=" + state.id + "]", options.monitor).data("pushstate", true).trigger("click");
                }
            });
        }
        $(options.monitor).on('click', '[addtabs]', function (e) {
            if ($(this).attr('url').indexOf("javascript:") !== 0) {
                if ($(this).is("a")) {
                    e.preventDefault();
                }
                var id = $(this).attr('addtabs');
                var title = $(this).attr('title') ? $(this).attr('title') : $.trim($(this).text());
                var url = $(this).attr('url');
                var content = options.content ? options.content : $(this).attr('content');
                var ajax = $(this).attr('ajax') === '1' || $(this).attr('ajax') === 'true';
                var state = ({
                    url: url, title: title, id: id, content: content, ajax: ajax
                });

                document.title = title;
                if (history.pushState && !$(this).data("pushstate")) {
                    var pushurl = url.indexOf("ref=addtabs") === -1 ? (url + (url.indexOf("?") > -1 ? "&" : "?") + "ref=addtabs") : url;
                    try {
                        window.history.pushState(state, title, pushurl);
                    } catch (e) {

                    }
                }
                $(this).data("pushstate", null);
                _add.call(this, {
                    id: id,
                    title: $(this).attr('title') ? $(this).attr('title') : $(this).html(),
                    content: content,
                    url: url,
                    ajax: ajax
                });
            }
        });

        navobj.on('click', '.close-tab', function () {
            var id = $(this).prev("a").attr("aria-controls");
            _close(id);
            return false;
        });
        navobj.on('dblclick', 'li[role=presentation]', function () {
            $(this).find(".close-tab").trigger("click");
        });
        navobj.on('click', 'li[role=presentation]', function () {
            $("a[addtabs=" + $("a", this).attr("node-id") + "]").trigger("click");
        });

        $(window).resize(function () {
            if (typeof options.nav === 'object') {
                var siblingsWidth = 0;
                navobj.siblings().each(function () {
                    siblingsWidth += $(this).outerWidth();
                });
                navobj.width(navobj.parent().width() - siblingsWidth);
            } else {
                $("#nav").width($("#header").find("> .navbar").width() - $(".sidebar-toggle").outerWidth() - $(".navbar-custom-menu").outerWidth() - 20);
            }
            _drop();
        });

        var _add = function (opts) {
            var id, tabid, conid, url;
            id = opts.id;
            tabid = 'tab_' + opts.id;
            conid = 'con_' + opts.id;
            url = opts.url;
            url += (opts.url.indexOf("?") > -1 ? "&addtabs=1" : "?addtabs=1");

            if (options.simple) {
                navobj.find("[role='presentation']").remove();
                tabobj.find("[role='tabpanel']").remove();
            }

            var tabitem = $('#' + tabid, navobj);
            var conitem = $('#' + conid, tabobj);

            navobj.find("[role='presentation']").removeClass('active');
            tabobj.find("[role='tabpanel']").removeClass('active');

            //もしTAB存在しない，新しいを作成TAB
            if (tabitem.length === 0) {
                //新規を作成TABのtitle
                tabitem = $('<li role="presentation" id="' + tabid + '"><a href="#' + conid + '" node-id="' + opts.id + '" aria-controls="' + id + '" role="tab" data-toggle="tab">' + opts.title + '</a></li>');
                //閉じることを許可するかどうか
                if (options.close && $("li", navobj).length > 0) {
                    tabitem.append(' <i class="close-tab fa fa-remove"></i>');
                }
                if (conitem.length === 0) {
                    //新規を作成TABの内容
                    conitem = $('<div role="tabpanel" class="tab-pane" id="' + conid + '"></div>');
                    //を指定するかどうかTAB内容
                    if (opts.content) {
                        conitem.append(opts.content);
                    } else if (options.iframeUse && !opts.ajax) {//コンテンツがない場合，使用IFRAMEリンクを開く
                        var height = options.iframeHeight;
                        conitem.append('<iframe src="' + url + '" width="100%" height="' + height + '" frameborder="no" border="0" marginwidth="0" marginheight="0" scrolling-x="no" scrolling-y="auto" allowtransparency="yes"></iframe></div>');
                    } else {
                        $.get(url, function (data) {
                            conitem.append(data);
                        });
                    }
                    tabobj.append(conitem);
                }
                if (!options.simple) {
                    //追加TABS
                    if ($('.tabdrop li', navobj).length > 0) {
                        $('.tabdrop ul', navobj).append(tabitem);
                    } else {
                        navobj.append(tabitem);
                    }
                }
            } else {
                //強制的にリフレッシュiframe
                if (options.iframeForceRefresh) {
                    $("#" + conid + " iframe").attr('src', function (i, val) {
                        return val;
                    });
                } else if (options.iframeForceRefreshTable) {
                    try {
                        //チェックiframe中にリフレッシュボタンが存在するかどうか
                        if ($("#" + conid + " iframe").contents().find(".btn-refresh:not([data-force-refresh=false])").length > 0) {
                            $("#" + conid + " iframe")[0].contentWindow.$(".btn-refresh:not([data-force-refresh=false])").trigger("click");
                        }
                    } catch (e) {

                    }
                }
            }
            sessionStorage.setItem("addtabs", $(this).prop('outerHTML'));
            //有効化TAB
            tabitem.addClass('active');
            conitem.addClass("active");
            _drop();
        };

        var _close = function (id) {
            var tabid = 'tab_' + id;
            var conid = 'con_' + id;
            var tabitem = $('#' + tabid, navobj);
            var conitem = $('#' + conid, tabobj);
            //もし閉じるのが現在アクティブな場合TAB，その一つ前のをアクティブにするTAB
            if (obj.find("li.active").not('.tabdrop').attr('id') === tabid) {
                var prev = tabitem.prev().not(".tabdrop");
                var next = tabitem.next().not(".tabdrop");
                if (prev.length > 0) {
                    prev.find('a').trigger("click");
                } else if (next.length > 0) {
                    next.find('a').trigger("click");
                } else {
                    $(">li:not(.tabdrop):last > a", navobj).trigger('click');
                }
            }
            //無効TAB
            tabitem.remove();
            conitem.remove();
            _drop();
            options.callback();
        };

        var _drop = function () {
            navobj.refreshAddtabs();
        };
    };
    //更新Addtabs
    $.fn.refreshAddtabs = function () {
        var navobj = $(this);
        var dropdown = $(".tabdrop", navobj);
        if (dropdown.length === 0) {
            dropdown = $('<li class="dropdown pull-right hide tabdrop"><a class="dropdown-toggle" data-toggle="dropdown" href="javascript:;">' +
                '<i class="glyphicon glyphicon-align-justify"></i>' +
                ' <b class="caret"></b></a><ul class="dropdown-menu"></ul></li>');
            dropdown.prependTo(navobj);
        }

        //ドロップダウンスタイルがあるかどうかを検出
        if (navobj.parent().is('.tabs-below')) {
            dropdown.addClass('dropup');
        }

        var collection = 0;
        var maxwidth = navobj.width() - 65;

        var liwidth = 0;
        //複数行にわたるタブをチェック
        var litabs = navobj.append(dropdown.find('li')).find('>li').not('.tabdrop');
        var totalwidth = 0;
        litabs.each(function () {
            totalwidth += $(this).outerWidth(true);
        });
        if (navobj.width() < totalwidth) {
            litabs.each(function () {
                liwidth += $(this).outerWidth(true);
                if (liwidth > maxwidth) {
                    dropdown.find('ul').append($(this));
                    collection++;
                }
            });
            if (collection > 0) {
                dropdown.removeClass('hide');
                if (dropdown.find('.active').length === 1) {
                    dropdown.addClass('active');
                } else {
                    dropdown.removeClass('active');
                }
            }
        } else {
            dropdown.addClass('hide');
        }

    };
})(jQuery);

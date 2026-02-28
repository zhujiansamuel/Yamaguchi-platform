define(['jquery', 'bootstrap', 'toastr', 'layer', 'lang'], function ($, undefined, Toastr, Layer, Lang) {
    var Fast = {
        config: {
            //toastrデフォルト設定
            toastr: {
                "closeButton": true,
                "debug": false,
                "newestOnTop": false,
                "progressBar": false,
                "positionClass": "toast-top-center",
                "preventDuplicates": false,
                "onclick": null,
                "showDuration": "300",
                "hideDuration": "1000",
                "timeOut": "5000",
                "extendedTimeOut": "1000",
                "showEasing": "swing",
                "hideEasing": "linear",
                "showMethod": "fadeIn",
                "hideMethod": "fadeOut"
            }
        },
        events: {
            //リクエスト成功時のコールバック
            onAjaxSuccess: function (ret, onAjaxSuccess) {
                var data = typeof ret.data !== 'undefined' ? ret.data : null;
                var msg = typeof ret.msg !== 'undefined' && ret.msg ? ret.msg : __('Operation completed');

                if (typeof onAjaxSuccess === 'function') {
                    var result = onAjaxSuccess.call(this, data, ret);
                    if (result === false)
                        return;
                }
                Toastr.success(msg);
            },
            //リクエストエラー時のコールバック
            onAjaxError: function (ret, onAjaxError) {
                var data = typeof ret.data !== 'undefined' ? ret.data : null;
                if (typeof onAjaxError === 'function') {
                    var result = onAjaxError.call(this, data, ret);
                    if (result === false) {
                        return;
                    }
                }
                Toastr.error(ret.msg);
            },
            //サーバーがデータを返した後
            onAjaxResponse: function (response) {
                try {
                    var ret = typeof response === 'object' ? response : JSON.parse(response);
                    if (!ret.hasOwnProperty('code')) {
                        $.extend(ret, {code: -2, msg: response, data: null});
                    }
                } catch (e) {
                    var ret = {code: -1, msg: e.message, data: null};
                }
                return ret;
            }
        },
        api: {
            //送信Ajaxリクエスト
            ajax: function (options, success, error) {
                options = typeof options === 'string' ? {url: options} : options;
                var index;
                if (typeof options.loading === 'undefined' || options.loading) {
                    index = Layer.load(options.loading || 0);
                }
                options = $.extend({
                    type: "POST",
                    dataType: "json",
                    xhrFields: {
                        withCredentials: true
                    },
                    success: function (ret) {
                        index && Layer.close(index);
                        ret = Fast.events.onAjaxResponse(ret);
                        if (ret.code === 1) {
                            Fast.events.onAjaxSuccess(ret, success);
                        } else {
                            Fast.events.onAjaxError(ret, error);
                        }
                    },
                    error: function (xhr) {
                        index && Layer.close(index);
                        var ret = {code: xhr.status, msg: xhr.statusText, data: null};
                        Fast.events.onAjaxError(ret, error);
                    }
                }, options);
                return $.ajax(options);
            },
            //修復URL
            fixurl: function (url) {
                if (url.substr(0, 1) !== "/") {
                    var r = new RegExp('^(?:[a-z]+:)?//', 'i');
                    if (!r.test(url)) {
                        url = Config.moduleurl + "/" + url;
                    }
                } else if (url.substr(0, 8) === "/addons/") {
                    url = Config.__PUBLIC__.replace(/(\/*$)/g, "") + url;
                }
                return url;
            },
            //修復後にアクセス可能なcdnリンク
            cdnurl: function (url, domain) {
                var rule = new RegExp("^((?:[a-z]+:)?\\/\\/|data:image\\/)", "i");
                var cdnurl = Config.upload.cdnurl;
                if (typeof domain === 'undefined' || domain === true || cdnurl.indexOf("/") === 0) {
                    url = rule.test(url) || (cdnurl && url.indexOf(cdnurl) === 0) ? url : cdnurl + url;
                }
                if (domain && !rule.test(url)) {
                    domain = typeof domain === 'string' ? domain : location.origin;
                    url = domain + url;
                }
                return url;
            },
            //クエリUrlパラメーター
            query: function (name, url) {
                if (!url) {
                    url = window.location.href;
                }
                if (!name)
                    return '';
                name = name.replace(/[\[\]]/g, "\\$&");
                var regex = new RegExp("[?&/]" + name + "([=/]([^&#/?]*)|&|#|$)"),
                    results = regex.exec(url);
                if (!results)
                    return null;
                if (!results[2])
                    return '';
                return decodeURIComponent(results[2].replace(/\+/g, " "));
            },
            //ポップアップウィンドウを開く
            open: function (url, title, options) {
                title = options && options.title ? options.title : (title ? title : "");
                url = Fast.api.fixurl(url);
                url = url + (url.indexOf("?") > -1 ? "&" : "?") + "dialog=1";
                var area = Fast.config.openArea != undefined ? Fast.config.openArea : [$(window).width() > 800 ? '800px' : '95%', $(window).height() > 600 ? '600px' : '95%'];
                var success = options && typeof options.success === 'function' ? options.success : $.noop;
                if (options && typeof options.success === 'function') {
                    delete options.success;
                }
                options = $.extend({
                    type: 2,
                    title: title,
                    shadeClose: true,
                    shade: false,
                    maxmin: true,
                    moveOut: true,
                    area: area,
                    content: url,
                    zIndex: Layer.zIndex,
                    success: function (layero, index) {
                        var that = this;
                        //保存callbackイベント
                        $(layero).data("callback", that.callback);
                        //$(layero).removeClass("layui-layer-border");
                        Layer.setTop(layero);
                        try {
                            var frame = Layer.getChildFrame('html', index);
                            var layerfooter = frame.find(".layer-footer");
                            Fast.api.layerfooter(layero, index, that);

                            //イベントをバインド
                            if (layerfooter.length > 0) {
                                // ウィンドウ内の要素および属性の変化を監視
                                // FirefoxとChrome初期バージョンではプレフィックス付き
                                var MutationObserver = window.MutationObserver || window.WebKitMutationObserver || window.MozMutationObserver;
                                if (MutationObserver) {
                                    // 対象ノードを選択
                                    var target = layerfooter[0];
                                    // オブザーバーオブジェクトを作成
                                    var observer = new MutationObserver(function (mutations) {
                                        Fast.api.layerfooter(layero, index, that);
                                        mutations.forEach(function (mutation) {
                                        });
                                    });
                                    // 監視オプションを設定:
                                    var config = {attributes: true, childList: true, characterData: true, subtree: true}
                                    // 対象ノードと監視オプションを渡す
                                    observer.observe(target, config);
                                    // その後,監視を停止することもできます
                                    // observer.disconnect();
                                }
                            }
                        } catch (e) {

                        }
                        if ($(layero).height() > $(window).height()) {
                            //ポップアップウィンドウがブラウザの表示高さより大きい場合,位置を再調整
                            Layer.style(index, {
                                top: 0,
                                height: $(window).height()
                            });
                        }
                        success.call(this, layero, index);
                    }
                }, options ? options : {});
                if ($(window).width() < 480 || (/iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream && top.$(".tab-pane.active").length > 0)) {
                    if (top.$(".tab-pane.active").length > 0) {
                        options.area = [top.$(".tab-pane.active").width() + "px", top.$(".tab-pane.active").height() + "px"];
                        options.offset = [top.$(".tab-pane.active").scrollTop() + "px", "0px"];
                    } else {
                        options.area = [$(window).width() + "px", $(window).height() + "px"];
                        options.offset = ["0px", "0px"];
                    }
                }
                return Layer.open(options);
            },
            //ウィンドウを閉じてデータを返す
            close: function (data) {
                var index = parent.Layer.getFrameIndex(window.name);
                var callback = parent.$("#layui-layer" + index).data("callback");
                //続いて閉じる処理を実行
                parent.Layer.close(index);
                //続いてコールバック関数を呼び出す
                if (typeof callback === 'function') {
                    callback.call(undefined, data);
                }
            },
            layerfooter: function (layero, index, that) {
                var frame = Layer.getChildFrame('html', index);
                var layerfooter = frame.find(".layer-footer");
                if (layerfooter.length > 0) {
                    $(".layui-layer-footer", layero).remove();
                    var footer = $("<div />").addClass('layui-layer-btn layui-layer-footer');
                    footer.html(layerfooter.html());
                    if ($(".row", footer).length === 0) {
                        $(">", footer).wrapAll("<div class='row'></div>");
                    }
                    footer.insertAfter(layero.find('.layui-layer-content'));
                    //イベントをバインド
                    footer.on("click", ".btn", function () {
                        if ($(this).hasClass("disabled") || $(this).parent().hasClass("disabled")) {
                            return;
                        }
                        var index = footer.find('.btn').index(this);
                        $(".btn:eq(" + index + ")", layerfooter).trigger("click");
                    });

                    var titHeight = layero.find('.layui-layer-title').outerHeight() || 0;
                    var btnHeight = layero.find('.layui-layer-btn').outerHeight() || 0;
                    //再設定iframe高さ
                    $("iframe", layero).height(layero.height() - titHeight - btnHeight);
                }
                //修復iOS下ポップアップウィンドウの高さとiOS下iframeスクロール不可のBUG
                if (/iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream) {
                    var titHeight = layero.find('.layui-layer-title').outerHeight() || 0;
                    var btnHeight = layero.find('.layui-layer-btn').outerHeight() || 0;
                    $("iframe", layero).parent().css("height", layero.height() - titHeight - btnHeight);
                    $("iframe", layero).css("height", "100%");
                }
            },
            success: function (options, callback) {
                var type = typeof options === 'function';
                if (type) {
                    callback = options;
                }
                return Layer.msg(__('Operation completed'), $.extend({
                    offset: 0, icon: 1
                }, type ? {} : options), callback);
            },
            error: function (options, callback) {
                var type = typeof options === 'function';
                if (type) {
                    callback = options;
                }
                return Layer.msg(__('Operation failed'), $.extend({
                    offset: 0, icon: 2
                }, type ? {} : options), callback);
            },
            msg: function (message, url) {
                var callback = typeof url === 'function' ? url : function () {
                    if (typeof url !== 'undefined' && url) {
                        location.href = url;
                    }
                };
                Layer.msg(message, {
                    time: 2000
                }, callback);
            },
            escape: function (text) {
                if (typeof text === 'string') {
                    return text
                        .replace(/&/g, '&amp;')
                        .replace(/</g, '&lt;')
                        .replace(/>/g, '&gt;')
                        .replace(/"/g, '&quot;')
                        .replace(/'/g, '&#039;')
                        .replace(/`/g, '&#x60;');
                }
                return text;
            },
            toastr: Toastr,
            layer: Layer
        },
        lang: function () {
            var args = arguments,
                string = args[0],
                i = 1;
            string = string.toLowerCase();
            //string = typeof Lang[string] != 'undefined' ? Lang[string] : string;
            if (typeof Lang !== 'undefined' && typeof Lang[string] !== 'undefined') {
                if (typeof Lang[string] == 'object')
                    return Lang[string];
                string = Lang[string];
            } else if (string.indexOf('.') !== -1 && false) {
                var arr = string.split('.');
                var current = Lang[arr[0]];
                for (var i = 1; i < arr.length; i++) {
                    current = typeof current[arr[i]] != 'undefined' ? current[arr[i]] : '';
                    if (typeof current != 'object')
                        break;
                }
                if (typeof current == 'object')
                    return current;
                string = current;
            } else {
                string = args[0];
            }
            return string.replace(/%((%)|s|d)/g, function (m) {
                // m is the matched format, e.g. %s, %d
                var val = null;
                if (m[2]) {
                    val = m[2];
                } else {
                    val = args[i];
                    // A switch statement so that the formatter can be extended. Default is %s
                    switch (m) {
                        case '%d':
                            val = parseFloat(val);
                            if (isNaN(val)) {
                                val = 0;
                            }
                            break;
                    }
                    i++;
                }
                return val;
            });
        },
        init: function () {
            // jQuery互換処理
            $.fn.extend({
                size: function () {
                    return $(this).length;
                }
            });
            // 相対パスを処理
            $.ajaxSetup({
                beforeSend: function (xhr, setting) {
                    setting.url = Fast.api.fixurl(setting.url);
                }
            });
            Layer.config({
                skin: 'layui-layer-fast'
            });
            // バインドESCウィンドウを閉じるイベント
            $(window).keyup(function (e) {
                if (e.keyCode == 27) {
                    if ($(".layui-layer").length > 0) {
                        var index = 0;
                        $(".layui-layer").each(function () {
                            index = Math.max(index, parseInt($(this).attr("times")));
                        });
                        if (index) {
                            Layer.close(index);
                        }
                    }
                }
            });

            //共通コード
            //設定Toastrのパラメータ
            Toastr.options = Fast.config.toastr;
        }
    };
    //をLayerグローバルに公開する
    window.Layer = Layer;
    //をToastrグローバルに公開する
    window.Toastr = Toastr;
    //言語メソッドをグローバルに公開する
    window.__ = Fast.lang;
    //をFastグローバルへレンダリング
    window.Fast = Fast;

    //デフォルト初期化時に実行するコード
    Fast.init();
    return Fast;
});

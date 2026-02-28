define(['fast', 'template', 'moment'], function (Fast, Template, Moment) {
    var Frontend = {
        api: Fast.api,
        init: function () {
            var si = {};
            //認証コードを送信
            $(document).on("click", ".btn-captcha", function (e) {
                var type = $(this).data("type") ? $(this).data("type") : 'mobile';
                var btn = this;
                Frontend.api.sendcaptcha = function (btn, type, data, callback) {
                    $(btn).addClass("disabled", true).text("送信中...");

                    Frontend.api.ajax({url: $(btn).data("url"), data: data}, function (data, ret) {
                        clearInterval(si[type]);
                        var seconds = 60;
                        si[type] = setInterval(function () {
                            seconds--;
                            if (seconds <= 0) {
                                clearInterval(si);
                                $(btn).removeClass("disabled").text("認証コードを送信");
                            } else {
                                $(btn).addClass("disabled").text(seconds + "秒後に再送信可能");
                            }
                        }, 1000);
                        if (typeof callback == 'function') {
                            callback.call(this, data, ret);
                        }
                    }, function () {
                        $(btn).removeClass("disabled").text('認証コードを送信');
                    });
                };
                if (['mobile', 'email'].indexOf(type) > -1) {
                    var element = $(this).data("input-id") ? $("#" + $(this).data("input-id")) : $("input[name='" + type + "']", $(this).closest("form"));
                    var text = type === 'email' ? 'メールアドレス' : '携帯番号';
                    if (element.val() === "") {
                        Layer.msg(text + "空にできません！");
                        element.focus();
                        return false;
                    } else if (type === 'mobile' && !element.val().match(/^1[3-9]\d{9}$/)) {
                        Layer.msg("正しい" + text + "！");
                        element.focus();
                        return false;
                    } else if (type === 'email' && !element.val().match(/^[\w\+\-]+(\.[\w\+\-]+)*@[a-z\d\-]+(\.[a-z\d\-]+)*\.([a-z]{2,4})$/)) {
                        Layer.msg("正しい" + text + "！");
                        element.focus();
                        return false;
                    }
                    element.isValid(function (v) {
                        if (v) {
                            var data = {event: $(btn).data("event")};
                            data[type] = element.val();
                            Frontend.api.sendcaptcha(btn, type, data);
                        } else {
                            Layer.msg("正しい" + text + "！");
                        }
                    });
                } else {
                    var data = {event: $(btn).data("event")};
                    Frontend.api.sendcaptcha(btn, type, data, function (data, ret) {
                        Layer.open({title: false, area: ["400px", "430px"], content: "<img src='" + data.image + "' width='400' height='400' /><div class='text-center panel-title'>QRコードをスキャンして公式アカウントをフォローし、認証コードを取得してください</div>", type: 1});
                    });
                }
                return false;
            });
            //tooltipとpopover
            if (!('ontouchstart' in document.documentElement)) {
                $('body').tooltip({selector: '[data-toggle="tooltip"]'});
            }
            $('body').popover({selector: '[data-toggle="popover"]'});

            // モバイル端末で左右スワイプしてメニューを切り替え
            if ('ontouchstart' in document.documentElement) {
                var startX, startY, moveEndX, moveEndY, relativeX, relativeY, element;
                element = $('body', document);
                element.on("touchstart", function (e) {
                    startX = e.originalEvent.changedTouches[0].pageX;
                    startY = e.originalEvent.changedTouches[0].pageY;
                });
                element.on("touchend", function (e) {
                    moveEndX = e.originalEvent.changedTouches[0].pageX;
                    moveEndY = e.originalEvent.changedTouches[0].pageY;
                    relativeX = moveEndX - startX;
                    relativeY = moveEndY - startY;

                    // 判定基準
                    //右スワイプ
                    if (relativeX > 45) {
                        if ((Math.abs(relativeX) - Math.abs(relativeY)) > 50) {
                            element.addClass("sidebar-open");
                        }
                    }
                    //左スワイプ
                    else if (relativeX < -45) {
                        if ((Math.abs(relativeX) - Math.abs(relativeY)) > 50) {
                            element.removeClass("sidebar-open");
                        }
                    }
                });
            }
            $(document).on("click", ".sidebar-toggle", function () {
                $("body").toggleClass("sidebar-open");
            });
        }
    };
    Frontend.api = $.extend(Fast.api, Frontend.api);
    //をTemplateグローバルへレンダリング,サブフレームから呼び出せるようにする
    window.Template = Template;
    //をMomentグローバルへレンダリング,サブフレームから呼び出せるようにする
    window.Moment = Moment;
    //をFrontendグローバルへレンダリング,サブフレームから呼び出せるようにする
    window.Frontend = Frontend;

    Frontend.init();
    return Frontend;
});

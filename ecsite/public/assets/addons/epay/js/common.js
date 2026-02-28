$(function () {

    if ($('.carousel').length > 0) {
        $('.carousel').carousel({
            interval: 5000
        });
    }

    if ($(".qrcode").length > 0) {
        $(".qrcode").qrcode({width: 250, height: 250, text: $(".qrcode").data("text")});
    }

    var si, xhr;
    if (typeof queryParams != 'undefined') {
        var queryResult = function () {
            xhr && xhr.abort();
            xhr = $.ajax({
                url: "",
                type: "post",
                data: queryParams,
                dataType: 'json',
                success: function (ret) {
                    if (ret.code == 1) {
                        var data = ret.data;
                        if (typeof data.status != 'undefined') {
                            var status = data.status;
                            if (status == 'SUCCESS' || status == 'TRADE_SUCCESS') {
                                $(".scanpay-qrcode .paid").removeClass("hidden");
                                $(".scanpay-tips p").html("支払い成功！<br><span>3</span>秒後に自動的に遷移します...");

                                var sin = setInterval(function () {
                                    $(".scanpay-tips p span").text(parseInt($(".scanpay-tips p span").text()) - 1);
                                }, 1000);

                                setTimeout(function () {
                                    clearInterval(sin);
                                    location.href = queryParams.returnurl;
                                }, 3000);

                                clearInterval(si);
                            } else if (status == 'REFUND' || status == 'TRADE_CLOSED') {
                                $(".scanpay-tips p").html("リクエストに失敗しました！<br>戻って支払いをやり直してください");
                                clearInterval(si);
                            } else if (status == 'NOTPAY' || status == 'TRADE_NOT_EXIST') {
                            } else if (status == 'CLOSED' || status == 'TRADE_CLOSED') {
                                $(".scanpay-tips p").html("注文はすでにクローズされています！<br>戻って支払いをやり直してください");
                                clearInterval(si);
                            } else if (status == 'USERPAYING' || status == 'WAIT_BUYER_PAY') {
                            } else if (status == 'PAYERROR') {
                                clearInterval(si);
                            }
                        }
                    }
                }
            });
        };
        si = setInterval(function () {
            queryResult();
        }, 3000);
        queryResult();
    }

});

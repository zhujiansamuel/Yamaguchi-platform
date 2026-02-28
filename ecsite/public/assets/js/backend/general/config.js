define(['jquery', 'bootstrap', 'backend', 'table', 'form'], function ($, undefined, Backend, Table, Form) {

    var Controller = {
        index: function () {
            $("form.edit-form").data("validator-options", {
                display: function (elem) {
                    return $(elem).closest('tr').find("td:first").text();
                }
            });
            Form.api.bindevent($("form.edit-form"));

            //非表示要素は検証しない
            $("form#add-form").data("validator-options", {
                ignore: ':hidden',
                rules: {
                    content: function () {
                        return ['radio', 'checkbox', 'select', 'selects'].indexOf($("#add-form select[name='row[type]']").val()) > -1;
                    },
                    extend: function () {
                        return $("#add-form select[name='row[type]']").val() == 'custom';
                    }
                }
            });
            Form.api.bindevent($("form#add-form"), function (ret) {
                setTimeout(function () {
                    location.reload();
                }, 1500);
            });

            //関連する表示フィールドと保存フィールドをレンダリング
            var renderselect = function (id, data, defaultvalue) {
                var html = [];
                for (var i = 0; i < data.length; i++) {
                    html.push("<option value='" + data[i].name + "' " + (defaultvalue == data[i].name ? "selected" : "") + " data-subtext='" + data[i].title + "'>" + data[i].name + "</option>");
                }
                var select = $(id);
                $(select).html(html.join(""));
                select.trigger("change");
                if (select.data("selectpicker")) {
                    select.selectpicker('refresh');
                }
            };
            //関連テーブルの切り替え
            $(document).on('change', "#c-selectpage-table", function (e, first) {
                var that = this;
                Fast.api.ajax({
                    url: "general/config/get_fields_list",
                    data: {table: $(that).val()},
                }, function (data, ret) {
                    renderselect("#c-selectpage-primarykey", data.fieldList, first ? $("#c-selectpage-primarykey").data("value") : '');
                    renderselect("#c-selectpage-field", data.fieldList, first ? $("#c-selectpage-field").data("value") : '');
                    return false;
                });
                return false;
            });
            //編集モードの場合は既知のデータをレンダリング
            if (['selectpage', 'selectpages'].indexOf($("#c-type").val()) > -1) {
                $("#c-selectpage-table").trigger("change", true);
            }

            //タイプ切り替え時
            $(document).on("change", "#c-type", function () {
                var value = $(this).val();
                $(".tf").addClass("hidden");
                $(".tf.tf-" + value).removeClass("hidden");
                if (["selectpage", "selectpages"].indexOf(value) > -1 && $("#c-selectpage-table option").length == 1) {
                    //テーブル一覧を非同期で読み込み
                    Fast.api.ajax({
                        url: "general/config/get_table_list",
                    }, function (data, ret) {
                        renderselect("#c-selectpage-table", data.tableList);
                        return false;
                    });
                }
            });

            //変数辞書リストの表示／非表示を切り替え
            $(document).on("change", "form#add-form select[name='row[type]']", function (e) {
                $("#add-content-container").toggleClass("hide", ['select', 'selects', 'checkbox', 'radio'].indexOf($(this).val()) > -1 ? false : true);
            });

            //ルールを選択
            $(document).on("click", ".rulelist > li > a", function () {
                var ruleArr = $("#rule").val() == '' ? [] : $("#rule").val().split(";");
                var rule = $(this).data("value");
                var index = ruleArr.indexOf(rule);
                if (index > -1) {
                    ruleArr.splice(index, 1);
                } else {
                    ruleArr.push(rule);
                }
                $("#rule").val(ruleArr.join(";"));
                $(this).parent().toggleClass("active");
            });

            //送信者にテストメールを送信するボタンとメソッドを追加
            $('input[name="row[mail_from]"]').parent().next().append('<a class="btn btn-info testmail">' + __('Send a test message') + '</a>');
            $(document).on("click", ".testmail", function () {
                var that = this;
                Layer.prompt({title: __('Please input your email'), formType: 0}, function (value, index) {
                    Backend.api.ajax({
                        url: "general/config/emailtest",
                        data: $(that).closest("form").serialize() + "&receiver=" + value
                    });
                });

            });

            //設定を削除
            $(document).on("click", ".btn-delcfg", function () {
                var that = this;
                Layer.confirm(__('Are you sure you want to delete this item?'), {
                    icon: 3,
                    title: 'ヒント'
                }, function (index) {
                    Backend.api.ajax({
                        url: "general/config/del",
                        data: {name: $(that).data("name")}
                    }, function () {
                        $(that).closest("tr").remove();
                        Layer.close(index);
                    });
                });

            });
        },
        add: function () {
            Controller.api.bindevent();
        },
        edit: function () {
            Controller.api.bindevent();
        },
        api: {
            bindevent: function () {
                Form.api.bindevent($("form[role=form]"));
            }
        }
    };
    return Controller;
});

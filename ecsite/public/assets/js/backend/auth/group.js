define(['jquery', 'bootstrap', 'backend', 'table', 'form', 'jstree'], function ($, undefined, Backend, Table, Form, undefined) {
    //選択した項目を読み取る
    $.jstree.core.prototype.get_all_checked = function (full) {
        var obj = this.get_selected(), i, j;
        for (i = 0, j = obj.length; i < j; i++) {
            obj = obj.concat(this.get_node(obj[i]).parents);
        }
        obj = $.grep(obj, function (v, i, a) {
            return v != '#';
        });
        obj = obj.filter(function (itm, i, a) {
            return i == a.indexOf(itm);
        });
        return full ? $.map(obj, $.proxy(function (i) {
            return this.get_node(i);
        }, this)) : obj;
    };
    var Controller = {
        index: function () {
            // テーブルパラメーター設定の初期化
            Table.api.init({
                extend: {
                    "index_url": "auth/group/index",
                    "add_url": "auth/group/add",
                    "edit_url": "auth/group/edit",
                    "del_url": "auth/group/del",
                    "multi_url": "auth/group/multi",
                }
            });

            var table = $("#table");

            //テーブル内容のレンダリング完了後に呼び出されるイベント
            table.on('post-body.bs.table', function (e, json) {
                $("tbody tr[data-index]", this).each(function () {
                    if (Config.admin.group_ids.indexOf(parseInt(parseInt($("td:eq(1)", this).text()))) > -1) {
                        $("input[type=checkbox]", this).prop("disabled", true);
                    }
                });
            });

            // テーブルの初期化
            table.bootstrapTable({
                url: $.fn.bootstrapTable.defaults.extend.index_url,
                columns: [
                    [
                        {field: 'state', checkbox: true,},
                        {field: 'id', title: 'ID'},
                        {field: 'pid', title: __('Parent')},
                        {field: 'name', title: __('Name'), align: 'left', formatter:function (value, row, index) {
                                return value.toString().replace(/(&|&amp;)nbsp;/g, '&nbsp;');
                            }
                        },
                        {field: 'status', title: __('Status'), formatter: Table.api.formatter.status},
                        {
                            field: 'operate', title: __('Operate'), table: table, events: Table.api.events.operate, formatter: function (value, row, index) {
                                if (Config.admin.group_ids.indexOf(parseInt(row.id)) > -1) {
                                    return '';
                                }
                                return Table.api.formatter.operate.call(this, value, row, index);
                            }
                        }
                    ]
                ],
                pagination: false,
                search: false,
                commonSearch: false,
            });

            // テーブルにイベントをバインド
            Table.api.bindevent(table);//内容のレンダリング完了後

        },
        add: function () {
            Controller.api.bindevent();
        },
        edit: function () {
            Controller.api.bindevent();
        },
        api: {
            bindevent: function () {
                Form.api.bindevent($("form[role=form]"), null, null, function () {
                    if ($("#treeview").length > 0) {
                        var r = $("#treeview").jstree("get_all_checked");
                        $("input[name='row[rules]']").val(r.join(','));
                    }
                    return true;
                });
                //権限ノードツリーをレンダリング
                //レベル変更後はノードツリーを再構築する必要があります
                $(document).on("change", "select[name='row[pid]']", function () {
                    var pid = $(this).data("pid");
                    var id = $(this).data("id");
                    if ($(this).val() == id) {
                        $("option[value='" + pid + "']", this).prop("selected", true).change();
                        Backend.api.toastr.error(__('Can not change the parent to self'));
                        return false;
                    }
                    $.ajax({
                        url: "auth/group/roletree",
                        type: 'post',
                        dataType: 'json',
                        data: {id: id, pid: $(this).val()},
                        success: function (ret) {
                            if (ret.hasOwnProperty("code")) {
                                var data = ret.hasOwnProperty("data") && ret.data != "" ? ret.data : "";
                                if (ret.code === 1) {
                                    //既存のノードツリーを破棄
                                    $("#treeview").jstree("destroy");
                                    Controller.api.rendertree(data);
                                } else {
                                    Backend.api.toastr.error(ret.msg);
                                }
                            }
                        }, error: function (e) {
                            Backend.api.toastr.error(e.message);
                        }
                    });
                });
                //すべて選択して展開
                $(document).on("click", "#checkall", function () {
                    $("#treeview").jstree($(this).prop("checked") ? "check_all" : "uncheck_all");
                });
                $(document).on("click", "#expandall", function () {
                    $("#treeview").jstree($(this).prop("checked") ? "open_all" : "close_all");
                });
                $("select[name='row[pid]']").trigger("change");
            },
            rendertree: function (content) {
                $("#treeview")
                    .on('redraw.jstree', function (e) {
                        $(".layer-footer").attr("domrefresh", Math.random());
                    })
                    .jstree({
                        "themes": {"stripes": true},
                        "checkbox": {
                            "keep_selected_style": false,
                        },
                        "types": {
                            "root": {
                                "icon": "fa fa-folder-open",
                            },
                            "menu": {
                                "icon": "fa fa-folder-open",
                            },
                            "file": {
                                "icon": "fa fa-file-o",
                            }
                        },
                        "plugins": ["checkbox", "types"],
                        "core": {
                            'check_callback': true,
                            "data": content
                        }
                    });
            }
        }
    };
    return Controller;
});

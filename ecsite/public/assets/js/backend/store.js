define(['jquery', 'bootstrap', 'backend', 'table', 'form'], function ($, undefined, Backend, Table, Form) {

    var Controller = {
        index: function () {
            // テーブルパラメーター設定の初期化
            Table.api.init({
                extend: {
                    index_url: 'store/index' + location.search,
                    add_url: 'store/add',
                    edit_url: 'store/edit',
                    del_url: 'store/del',
                    multi_url: 'store/multi',
                    import_url: 'store/import',
                    table: 'store',
                }
            });

            var table = $("#table");

            // テーブルの初期化
            table.bootstrapTable({
                url: $.fn.bootstrapTable.defaults.extend.index_url,
                pk: 'id',
                sortName: 'weigh',
                fixedColumns: true,
                fixedRightNumber: 1,
                columns: [
                    [
                        {checkbox: true},
                        {field: 'id', title: __('Id')},
                        {field: 'name', title: __('Name'), operate: 'LIKE'},
                        {field: 'image', title: __('Image'), operate: false, events: Table.api.events.image, formatter: Table.api.formatter.image},
                        {field: 'intro', title: __('Intro'), operate: 'LIKE', table: table, class: 'autocontent', formatter: Table.api.formatter.content},
                        {field: 'establish', title: __('Establish'), operate: 'LIKE'},
                        {field: 'represent', title: __('Represent'), operate: 'LIKE'},
                        {field: 'funds', title: __('Funds'), operate: 'LIKE'},
                        {field: 'address', title: __('Address'), operate: 'LIKE'},
                        //{field: 'business', title: __('Business'), operate: 'LIKE', table: table, class: 'autocontent', formatter: Table.api.formatter.content},
                        //{field: 'trade_bank', title: __('Trade_bank'), operate: 'LIKE', table: table, class: 'autocontent', formatter: Table.api.formatter.content},
                        //{field: 'map_url', title: __('Map_url'), operate: 'LIKE', formatter: Table.api.formatter.url},
                        {field: 'weigh', title: __('Weigh'), operate: false},
                        {field: 'createtime', title: __('Createtime'), operate:'RANGE', addclass:'datetimerange', autocomplete:false, formatter: Table.api.formatter.datetime},
                        {field: 'operate', title: __('Operate'), table: table, events: Table.api.events.operate, formatter: Table.api.formatter.operate}
                    ]
                ]
            });

            // テーブルにイベントをバインド
            Table.api.bindevent(table);
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

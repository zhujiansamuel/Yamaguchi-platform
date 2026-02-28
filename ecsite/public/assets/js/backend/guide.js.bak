define(['jquery', 'bootstrap', 'backend', 'table', 'form'], function ($, undefined, Backend, Table, Form) {

    var Controller = {
        index: function () {
            // 初始化表格参数配置
            Table.api.init({
                extend: {
                    index_url: 'guide/index' + location.search,
                    add_url: 'guide/add',
                    edit_url: 'guide/edit',
                    del_url: 'guide/del',
                    multi_url: 'guide/multi',
                    import_url: 'guide/import',
                    table: 'guide',
                }
            });

            var table = $("#table");

            // 初始化表格
            table.bootstrapTable({
                url: $.fn.bootstrapTable.defaults.extend.index_url,
                pk: 'id',
                sortName: 'weigh',
                showToggle:false,
                showExport: false,
                showColumns: false,
                search: false,
                queryParams : function(params)
                {
                    params.with = 'category';
                    return params;
                },
                columns: [
                    [
                        {checkbox: true},
                        {field: 'id', title: __('Id')},
                        {field: 'category.name', title: __('Category_id')},
                        {field: 'title', title: __('Title'), operate: 'LIKE'},
                        {field: 'weigh', title: __('Weigh'), operate: false},
                        //{field: 'content', title: __('Content')},
                        {
                            field: 'is_pdf',
                            title: __('显示pdf文件'),
                            align: 'center',
                            table: table,
                            formatter: Table.api.formatter.toggle
                        },
                        {field: 'createtime', title: __('Createtime'), operate:'RANGE', addclass:'datetimerange', autocomplete:false, formatter: Table.api.formatter.datetime},
                        {field: 'operate', title: __('Operate'), table: table, events: Table.api.events.operate, formatter: Table.api.formatter.operate}
                    ]
                ]
            });

            // 为表格绑定事件
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

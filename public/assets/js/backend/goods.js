define(['jquery', 'bootstrap', 'backend', 'table', 'form'], function ($, undefined, Backend, Table, Form) {

    var Controller = {
        index: function () {
            // テーブルパラメーター設定の初期化
            Table.api.init({
                extend: {
                    index_url: 'goods/index' + location.search,
                    add_url: 'goods/add',
                    edit_url: 'goods/edit',
                    del_url: 'goods/del',
                    multi_url: 'goods/multi',
                    import_url: 'goods/import',
                    table: 'goods',
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
                showToggle:false,
                showExport: false,
                showColumns: false,
                search: false,
                queryParams : function(params)
                {
                    params.with = 'category,second,three';
                    return params;
                },
                columns: [
                    [
                        {checkbox: true},
                        {field: 'id', title: __('Id')},
                        {
                            field: 'recomm',
                            title: __('トップページ固定表示'),
                            align: 'center',
                            table: table,
                            formatter: Table.api.formatter.toggle
                        },
                        {field: 'status', title: __('Status'), searchList: {"1":__('Status 1'),"0":__('Status 0')}, formatter: Table.api.formatter.status},
                        {field: 'category.name', title: __('Category_id')},
                        {field: 'second.name', title: __('Category_second')},
                        {field: 'three.name', title: __('Category_three')},
                        {field: 'image', title: __('Image'), operate: false, events: Table.api.events.image, formatter: Table.api.formatter.image},
                        {field: 'title', title: __('Title'), operate: 'LIKE'},
                        {field: 'price', title: __('Price'), operate:'BETWEEN'},
                        {field: 'weigh', title: __('優先度ソート'), operate: false},
                        //{field: 'memo', title: __('memo'), operate: 'LIKE'},
                        {field: 'memo', title: __('備考'), operate: 'LIKE'},
                        {field: 'imei', title: __('IMEI'), operate: 'LIKE'},
                        
                        //{field: 'color_id', title: __('Color_id'), operate: 'LIKE', table: table, class: 'autocontent', formatter: Table.api.formatter.content},
                        //{field: 'spec_info', title: __('Spec_info'), operate: 'LIKE', table: table, class: 'autocontent', formatter: Table.api.formatter.content},
                        
                        //{field: 'price_zg', title: __('Price_zg'), operate:'BETWEEN'},
                        //{field: 'type', title: __('type'), searchList: {"1":__('新品'),"2":__('中古')}, formatter: Table.api.formatter.status},
                        
                        
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

    $("#c-category_second").data("params", function (obj) {
        var v = $("#c-category_id").val();
        v = v > 0 ? v : -1;
        //objためのSelectPageオブジェクト
        return {custom: {pid: v}};
    });

    $("#c-category_three").data("params", function (obj) {
        var v = $("#c-category_second").val();
        v = v > 0 ? v : -1;
        //objためのSelectPageオブジェクト
        return {custom: {pid: v}};
    });

    // 批量价格管理
    Controller.bulkprice = function() {
        console.log('bulkprice function called');
        // 存储修改的价格
        var modifiedPrices = {};
        // 存储筛选条件
        var filterParams = {};

        // 初始化表格
        var table = $("#bulkprice-table");
        console.log('Table element found:', table.length);
        table.bootstrapTable({
            url: 'goods/bulkprice',
            pk: 'id',
            sortName: 'goods_id',
            pagination: true,
            pageSize: 50,
            pageList: [20, 50, 100, 200],
            search: false,
            showToggle: false,
            showExport: false,
            showColumns: false,
            sidePagination: 'server',
            queryParams: function(params) {
                console.log('Query params:', params);
                // 添加筛选参数
                $.extend(params, filterParams);
                console.log('Final params with filters:', params);
                return params;
            },
            responseHandler: function(res) {
                console.log('Response handler called, data:', res);
                return res;
            },
            columns: [
                {field: 'goods_id', title: '商品ID', width: 60, sortable: true},
                {field: 'image', title: '图片', width: 80, formatter: function(value, row) {
                    if (value) {
                        var img = value.indexOf('http') === 0 ? value : 'https://www.mobile-zone.jp' + value;
                        return '<img class="img-sm img-center" src="' + img + '">';
                    }
                    return '';
                }},
                {field: 'title', title: '商品标题', width: 250},
                {field: 'category.name', title: '分类', width: 100},
                {field: 'spec_name', title: '規格/色など', width: 150, formatter: function(value, row) {
                    return '<span class="spec-name-highlight">' + (value || '') + '</span>';
                }},
                {field: 'status', title: '状态', width: 70, formatter: function(value) {
                    return value == 1 ? '<span class="label label-success">上架</span>' : '<span class="label label-default">下架</span>';
                }},
                {field: 'price', title: '价格', width: 120, formatter: function(value, row) {
                    var val = value || 0;
                    return '<input type="text" class="editable-price" data-id="' + row.id + '" data-field="price" value="' + val + '">';
                }}
            ],
            onLoadSuccess: function(data) {
                console.log('Table loaded successfully, rows:', data.rows ? data.rows.length : 0);
                console.log('Total:', data.total);
                // 绑定价格输入框事件
                $('.editable-price').off('input').on('input', function() {
                    var $input = $(this);
                    var id = $input.data('id');
                    var field = $input.data('field');
                    var value = $input.val();

                    // 标记为已修改
                    if (!modifiedPrices[id]) {
                        modifiedPrices[id] = {};
                    }
                    modifiedPrices[id][field] = value;

                    // 添加视觉反馈
                    $input.addClass('price-modified');
                });
            }
        });

        // 刷新按钮
        $('.btn-refresh').on('click', function() {
            table.bootstrapTable('refresh');
            modifiedPrices = {};
        });

        // 批量保存按钮
        $('.btn-save-all').on('click', function() {
            if (Object.keys(modifiedPrices).length === 0) {
                Toastr.warning('没有需要保存的修改');
                return;
            }

            Layer.confirm('确定要保存 ' + Object.keys(modifiedPrices).length + ' 个商品的价格修改吗？', function(index) {
                Fast.api.ajax({
                    url: 'goods/bulkupdate',
                    data: {
                        prices: modifiedPrices
                    }
                }, function(data, ret) {
                    // 成功回调
                    console.log('=== 成功回调被调用 ===');
                    console.log('data:', data);
                    console.log('ret:', ret);
                    console.log('ret.msg:', ret.msg);
                    console.log('ret.code:', ret.code);

                    Layer.close(index);
                    // 显示成功消息
                    Toastr.success(ret.msg || '保存成功');
                    modifiedPrices = {};
                    // 清除所有价格输入框的修改标记
                    $('.editable-price').removeClass('price-modified');
                    table.bootstrapTable('refresh');
                }, function(data, ret) {
                    // 失败回调
                    console.log('=== 失败回调被调用 ===');
                    console.log('data:', data);
                    console.log('ret:', ret);
                    console.log('ret.msg:', ret.msg);

                    Layer.close(index);
                    // 显示错误消息
                    // Toastr.error(ret.msg || '保存失败');
                    return false;  // ← 添加这一行，阻止框架再次显示错误
                });
            });
        });

        // 筛选功能
        $('.btn-filter').on('click', function() {
            // 更新筛选参数
            filterParams = {};

            var title = $('#filter-title').val();
            var categoryId = $('#filter-category').val();
            var status = $('#filter-status').val();

            // 构建filter对象
            var filterObj = {};
            var opObj = {};

            if (title) {
                filterObj['title'] = title;
                opObj['title'] = 'LIKE';
            }
            if (categoryId) {
                filterObj['category_id'] = categoryId;
            }
            if (status) {
                filterObj['status'] = status;
            }

            // 将filter和op转换为JSON字符串
            if (Object.keys(filterObj).length > 0) {
                filterParams['filter'] = JSON.stringify(filterObj);
            }
            if (Object.keys(opObj).length > 0) {
                filterParams['op'] = JSON.stringify(opObj);
            }

            console.log('Filter params:', filterParams);
            // 刷新表格
            table.bootstrapTable('refresh');
        });

        // 重置筛选
        $('.btn-reset').on('click', function() {
            $('#filter-title').val('');
            $('#filter-category').val('');
            $('#filter-status').val('');
            // 清空筛选参数
            filterParams = {};
            // 刷新表格
            table.bootstrapTable('refresh');
        });

        // 加载分类列表（树形结构，仅商品分类）
        $.ajax({
            url: 'ajax/category',
            data: {
                type: 'goods',  // 仅加载商品分类
                tree: '1'       // 返回树形结构
            },
            dataType: 'json',
            success: function(res) {
                console.log('Category response:', res);
                if (res && res.code == 1 && res.data) {
                    var options = '<option value="">全部分类</option>';
                    $.each(res.data, function(i, item) {
                        // Ajax返回的字段名是value和name
                        options += '<option value="' + item.value + '">' + item.name + '</option>';
                    });
                    $('#filter-category').html(options);
                } else {
                    console.error('Failed to load categories:', res);
                }
            },
            error: function(xhr, status, error) {
                console.error('Ajax error loading categories:', error);
            }
        });
    };

    return Controller;
});

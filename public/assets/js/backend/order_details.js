define(['jquery', 'bootstrap', 'backend', 'table', 'form'], function ($, undefined, Backend, Table, Form) {

    var Controller = {
        index: function () {
            // テーブルパラメーター設定の初期化
            Table.api.init({
                extend: {
                    index_url: 'order_details/index' + location.search,
                    add_url: 'order_details/add?order_id='+Config.order_id,
                    edit_url: 'order_details/edit',
                    del_url: 'order_details/del',
                    multi_url: 'order_details/multi',
                    import_url: 'order_details/import',
                    table: 'order_details',
                }
            });

            var table = $("#table");

            // テーブルの初期化
            table.bootstrapTable({
                url: $.fn.bootstrapTable.defaults.extend.index_url,
                pk: 'id',
                sortName: 'id',
                fixedColumns: true,
                fixedRightNumber: 1,
                showToggle:false,
                showExport: false,
                showColumns: false,
                search: false,
                queryParams : function(params)
                {
                    params.where = {"order_id": Config.order_id}
                    return params;
                },
                columns: [
                    [
                        {checkbox: true},
                        {field: 'id', title: __('Id')},
                        //{field: 'order_id', title: __('Order_id')},
                        //{field: 'goods_id', title: __('Goods_id')},
                        {field: 'title', title: __('Title'), operate: 'LIKE'},
                        {field: 'jan', title: __('Jan'), operate: 'LIKE'},
                        {field: 'image', title: __('Image'), operate: false, events: Table.api.events.image, formatter: Table.api.formatter.image},
                        {field: 'specs_name', title: __('Specs_name'), operate: 'LIKE'},
                        {field: 'color', title: __('Color'), operate: 'LIKE'},
                        {field: 'num', title: __('Num')},
                        {field: 'price', title: __('Price')},
                        //{field: 'type', title: __('Type'), searchList: {"1":__('Type 1'),"2":__('Type 2')}, formatter: Table.api.formatter.normal},
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
    // $("#c-color").data("params", function (obj) {
    //     var color_id = $("#c-color").parents('.form-group').attr('data-color_id');
    //     color_id = color_id ? color_id : -1;
    //     //objためのSelectPageオブジェクト
    //     return {custom: {id: ["in", color_id]}};
    // });

    $(document).on('change' ,'#c-specs_name', function(){
        var v = $(this).val();
        var arrs = [];
        $('#c-specs_name option').each(function(i,n ){

            arrs[$(n).attr('value')] = $(n).attr('data-price');
            
        })
        $('#c-price').val( arrs[v] );
    })

    $("#c-goods_id").data("eSelect", function(data){
        var spec_info = decodeBasicHtmlEntities(data.spec_info);
        if(spec_info != ''){
            spec_info = JSON.parse(spec_info);
        }else{
            spec_info = [];
        }

        var color = decodeBasicHtmlEntities(data.color);
        if(color != ''){
            color = JSON.parse(color);
        }else{
            color = [];
        }
        
        //後続処理
        console.log( data , spec_info);
        $('#c-title').val(data.title);
        $('#c-jan').val(data.jan);
        $('#c-image').val(data.image);
        $('#c-price').val(data.price);
        //$('#c-price').val(data.price);
        //$("#c-color").parents('.form-group').attr('data-color_id', data.color_id);
        var option = '<option value="">選択</option>';
        for (var i = 0; i < spec_info.length; i++) {
            option += '<option data-price="'+spec_info[i]['price']+'" value="'+spec_info[i]['name']+'">'+spec_info[i]['name']+'</option>';
        }
        $("#c-specs_name").html(option);

        var color_option = '<option value="">選択</option>';
        for (var i = 0; i < color.length; i++) {
            color_option += '<option value="'+color[i]+'">'+color[i]+'</option>';
        }
        $("#c-color").html(color_option);

        Form.api.bindevent($("form[role=form]"));
        Form.events.cxselect($("form[role=form]"));
        Form.events.faupload($("form[role=form]"))  
    });

    function decodeBasicHtmlEntities(str) {
        return str.replace(/&quot;/g, '"')
                 .replace(/&amp;/g, '&')
                 .replace(/&#039;/g, "'")
                 .replace(/&lt;/g, '<')
                 .replace(/&gt;/g, '>');
    }
    return Controller;
});

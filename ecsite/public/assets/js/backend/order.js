define(['jquery', 'bootstrap', 'backend', 'table', 'form'], function ($, undefined, Backend, Table, Form) {

    var Controller = {
        index: function () {
            // テーブルパラメーター設定の初期化
            Table.api.init({
                extend: {
                    index_url: 'order/index' + location.search,
                    //add_url: 'order/add',
                    //edit_url: 'order/edit',
                    del_url: 'order/del',
                    multi_url: 'order/multi',
                    import_url: 'order/import',
                    table: 'order',
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
                //showExport: false,
                showColumns: false,
                search: false,
                exportTypes:['excel'],
                queryParams : function(params)
                {
                    params.with = 'user';
                    params.extendFunction = 'handleList';
                    params.extendReturn = 'handleReturn';
                    return params;
                },
                columns: [
                    [
                        {checkbox: true},
                        {field: 'id', title: __('Id')},
                        {field: 'user.email', title: __('E-mail')},
                        {field: 'user.name', title: __('お名前(カナ)')},
                        //{field: 'store_id', title: __('Store_id')},
                        {field: 'no', title: __('No'), operate: 'LIKE'},
                        //{field: 'bank_account_type', title: __('Bank_account_type'), searchList: {"1":__('Bank_account_type 1'),"2":__('Bank_account_type 2')}, formatter: Table.api.formatter.normal},
                        //{field: 'bank_account_name', title: __('Bank_account_name'), operate: 'LIKE'},
                        //{field: 'bank_account', title: __('Bank_account'), operate: 'LIKE'},
                        //{field: 'bank', title: __('Bank'), operate: 'LIKE'},
                        //{field: 'bank_branch', title: __('Bank_branch'), operate: 'LIKE'},
                        //{field: 'store_name', title: __('Store_name'), operate: 'LIKE'},
                        //{field: 'go_store_date', title: __('Go_store_date'), operate:'RANGE', addclass:'datetimerange', autocomplete:false},
                        //{field: 'go_store_time', title: __('Go_store_time'), operate: 'LIKE'},
                        {field: 'price', title: __('Price')},
                        //{field: 'procedures', title: __('Procedures')},
                        {field: 'total_price', title: __('Total_price')},
                        {field: 'status', title: __('Status'), searchList: Config.statusList, formatter: Table.api.formatter.normal},
                        {field: 'admin_status', title: __('Admin_status'), searchList: Config.adminStatusList, formatter: Table.api.formatter.normal},
                        {field: 'pay_mode', title: __('Pay_mode'), searchList: {"1":__('Pay_mode 1'),"2":__('Pay_mode 2')}, formatter: Table.api.formatter.normal},
                        //{field: 'type', title: __('Type'), searchList: {"1":__('Type 1'),"2":__('Type 2')}, formatter: Table.api.formatter.normal,operate:false},
                        {field: 'type', title: __('Type'), formatter: function(value, row){
                            var html = '';
                            if(value == 1){
                                html = '店頭買取<br>('+row['store_name']+')';
                            }else{
                                html = '郵送買取';
                            }
                            return html;
                        },operate:false},
                        {field: 'createtime', title: __('Createtime'), operate:'RANGE', addclass:'datetimerange', autocomplete:false, formatter: Table.api.formatter.datetime},
                        {field: 'operate', title: __('Operate'), table: table, events: Table.api.events.operate, 
                            buttons:[
                                {
                                    name: 'details',
                                    text:'注文詳細',
                                    title:'注文詳細',
                                    //classname: 'btn btn-xs btn-warning btn-view btn-ajax ',
                                    classname: 'btn btn-xs btn-warning  btn-dialog',
                                    icon: 'fa fa-shopping-cart',
                                    url: 'order/details',
                                    extend: 'data-area=\'["100%", "100%"]\'',
                                    
                                },
                                {
                                    name: 'details',
                                    text:'買取申込書',
                                    title:'買取申込書',
                                    //classname: 'btn btn-xs btn-warning btn-view btn-ajax ',
                                    classname: 'btn btn-xs btn-danger',
                                    icon: 'fa fa-shopping-cart',
                                    url: '/ylindex/{id}',
                                    extend:' target="_blank"',
                                    
                                },
                                {
                                    text:'予約メール',
                                    classname: 'btn btn-xs btn-info btn-view btn-ajax ',
                                    icon: 'fa fa-envelope-o',
                                    url: 'order/sendEms?type=1',
                                    confirm: function (row, column) { //確認ダイアログ
                                        return "送信してよろしいですか？?"
                                    },
                                    success:function(data,ret) {
                                        $(".btn-refresh").trigger("click")
                                    },
                                    error:function(data,ret) {
                                        console.log(data,ret)
                                        alert("ret.msg")
                                    },
                                    // visible:function(row){
                                    //     if((row.type==1  && row.pay_mode == 1) || row.type==2  && row.pay_mode == 2){
                                    //         return true;
                                    //     }else{
                                    //         return false;
                                    //     }
                                    // },
                                },
                                {
                                    text:'査定メール',
                                    classname: 'btn btn-xs btn-primary btn-view btn-ajax ',
                                    icon: 'fa fa-envelope-o',
                                    url: 'order/sendEms?type=2',
                                    confirm: function (row, column) { //確認ダイアログ
                                        return "送信してよろしいですか？?"
                                    },
                                    success:function(data,ret) {
                                        $(".btn-refresh").trigger("click")
                                    },
                                    error:function(data,ret) {
                                        console.log(data,ret)
                                        alert("ret.msg")
                                    },
                                    visible:function(row){
                                       
                                        //if( ((row.type==1  && row.pay_mode == 1) || row.type==2  && row.pay_mode == 2) && row.is_send_yuyue == 1 ){
                                        if( row.is_send_yuyue == 1 ){
                                            return true;
                                        }else{
                                            return false;
                                        }
                                    },
                                },
                                {
                                    text:'注文キャンセルメール',
                                    classname: 'btn btn-xs btn-danger btn-info btn-view btn-ajax ',
                                    icon: 'fa fa-envelope-o',
                                    url: 'order/sendEms?type=3',
                                    confirm: function (row, column) { //確認ダイアログ
                                        return "送信してよろしいですか？?"
                                    },
                                    success:function(data,ret) {
                                        $(".btn-refresh").trigger("click")
                                    },
                                    error:function(data,ret) {
                                        console.log(data,ret)
                                        alert("ret.msg")
                                    },
                                    // visible:function(row){
                                    //     if((row.type==1  && row.pay_mode == 1) || row.type==2  && row.pay_mode == 2){
                                    //         return true;
                                    //     }else{
                                    //         return false;
                                    //     }
                                    // },
                                },
                            ],
                        formatter: Table.api.formatter.operate}
                    ]
                ]
            });

            //テーブルデータの読み込み完了時
            table.on('load-success.bs.table', function (e, data) {
                //ここでサーバーから取得したJSONデータ
                console.log(data);
                $('.btn-export').attr('data-json', JSON.stringify(data.filter) );
                //$('.getOrderTotalMoney').html(data.orderTotalMoney);
                //ここでフッターの値を手動で設定します
                //$("#money").text(data.extend.money);
                //$("#price").text(data.extend.price);
            });

            // テーブルにイベントをバインド
            Table.api.bindevent(table);
        },
        recyclebin: function () {
            // テーブルパラメーター設定の初期化
            Table.api.init({
                extend: {
                    'dragsort_url': ''
                }
            });

            var table = $("#table");

            // テーブルの初期化
            table.bootstrapTable({
                url: 'order/recyclebin' + location.search,
                pk: 'id',
                sortName: 'id',
                columns: [
                    [
                        {checkbox: true},
                        {field: 'id', title: __('Id')},
                        {
                            field: 'deletetime',
                            title: __('Deletetime'),
                            operate: 'RANGE',
                            addclass: 'datetimerange',
                            formatter: Table.api.formatter.datetime
                        },
                        {
                            field: 'operate',
                            width: '140px',
                            title: __('Operate'),
                            table: table,
                            events: Table.api.events.operate,
                            buttons: [
                                {
                                    name: 'Restore',
                                    text: __('Restore'),
                                    classname: 'btn btn-xs btn-info btn-ajax btn-restoreit',
                                    icon: 'fa fa-rotate-left',
                                    url: 'order/restore',
                                    refresh: true
                                },
                                {
                                    name: 'Destroy',
                                    text: __('Destroy'),
                                    classname: 'btn btn-xs btn-danger btn-ajax btn-destroyit',
                                    icon: 'fa fa-times',
                                    url: 'order/destroy',
                                    refresh: true
                                }
                            ],
                            formatter: Table.api.formatter.operate
                        }
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
        edit_order_info: function () {
            Controller.api.bindevent();
        },
        details: function () {
            $(document).on("click", ".edit_order_details", function () {
                Fast.api.open('order_details/index?order_id='+$(this).attr('data-id'), __('商品明細'), {
                    area: ["100%", "100%"],
                });
                
            });
            $(document).on("click", ".edit_order_memo", function () {
                Fast.api.open('order/edit_order_info?order_id='+$(this).attr('data-id'), __('備考'), {
                    area: ["500px", "540px"],
                });
                
            });
            //注文ステータスを変更
            $('.edit_status').on('change', function(){
                var status = $(this).val();
                var order_id = $('.edit_status_box').attr('data-id');
                $.ajax({
                    url: "order/edit_status",
                    data: {'order_id': order_id, status:status},
                    type: "post",
                    success: function (res) {
                        if (res.code == 1) {
                            layer.msg(res.msg);
                            // $("#image").val(res.data.url);
                            //Fast.api.close(res.data);
                        } else {
                            layer.msg(res.msg);
                        }
                    }
                });
            })
            Controller.api.bindevent();
        },
        api: {
            bindevent: function () {
                Form.api.bindevent($("form[role=form]"));
            }
        }
    };
    $(document).on("click", ".btn-export", function () {
        var obj = $(this);
     
        $.ajax({
            url: obj.attr('data-href'),
            data: {'filter':obj.attr('data-json')},
            type: "post",
            success: function (res) {
                if (res.code == 1) {
                    var html = '';
                    var data = res.data;
                    for (var i = 0; i < data.length; i++) {
                        html += '<div><a href="'+data[i]['file']+'">'+data[i]['file']+'</a></div>';
                    };
                    Layer.confirm("出力するオプションを選択してください<br>"+html, {
                        title: 'データをエクスポート',
                        //btn: ["無効"],
                        success: function (layero, index) {
                            $(".layui-layer-btn a", layero).addClass("layui-layer-btn0");
                        }, 
                        // yes: function (index, layero) {
                        //     submitForm(ids.join(","), layero);
                        //     return false;
                        // },
                        // btn2: function (index, layero) {
                        //     var ids = [];
                        //     $.each(page, function (i, j) {
                        //         ids.push(j.id);
                        //     });
                        //     submitForm(ids.join(","), layero);
                        //     return false;
                        // },
                        // btn3: function (index, layero) {
                        //     submitForm("all", layero);
                        //     return false;
                        // }
                    })
                    //layer.msg(res.msg);
                    // $("#image").val(res.data.url);
                    //Fast.api.close(res.data);
                } else {
                    layer.msg(res.msg);
                }
            }
        });
 
    });
    return Controller;
});

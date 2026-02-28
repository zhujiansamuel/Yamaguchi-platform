$(function(){
	
	var mySwiper = new Swiper('.banner .swiper',{
		pagination: {
			el: '.swiper-pagination',
			clickable :true,
		},
		autoplay: true,
		loop: true,
	})
	$(".left").click(function(){
		mySwiper.slidePrev()
	})
	$(".right").click(function(){
		mySwiper.slideNext()
	})
	
	$(".icon_m a").click(function(e){
		$(".menu_m").toggle();
		e.stopPropagation();
	})
	$(".menu_m2>ul>li a").click(function(){
		$(this).siblings().toggle();
		$(this).children("img").toggleClass("tras");
		console.log(123)
	})
	$(document).click(function(e){
		var popup1 = $(".menu_m1");
		if (!popup1.is(e.target) && popup1.has(e.target).length == 0) {
			$(".menu_m").hide();
		}
	});
	
	$(".goTop").click(function(){
		$('html , body').animate({scrollTop: 0},'slow');
	})
	
	$(".login_tc7 img").click(function(){
		$(this).parent().children("img").toggle()
		var _type = $(this).siblings("input").attr("type")
		if(_type == "password"){
			$(this).siblings().attr("type","text")
		}else{
			$(this).siblings().attr("type","password")
		}
	})
	$(".login").click(function(){
		$(".login_tc").show()
	})
	$(".forget").click(function(){
		$(".forget_tc").show()
		$(".login_tc").hide()
	})
	$(".register").click(function(){
		$(".register_tc").show()
		$(".login_tc").hide()
	})
	$(".close").click(function(){
		$(".login_tc").hide()
		$(".forget_tc").hide()
		$(".forget1_tc").hide()
		$(".register_tc").hide()
		$(".register1_tc").hide()
		$(".qb_tc").hide()
	})
	
	
	$(".close1").click(function(){
		$(".gg").hide()
	})
	
// 	$('#imgs_file').change(function() {
// 		var file = this.files[0];
// 		var r = new FileReader();
// 		r.readAsDataURL(file);
// 		$(r).load(function() {
// 			//$(".orderLeft14").append('<span><img alt="" src="'+this.result+'"/><img class="newclose" alt="" src="/img/close.png"/><input type="hidden" name="pics[]" value="'+this.result+'"/></span>')
// 		})
// 	})
	$(".listLeft2").click(function(){
		$(this).parent().toggleClass("on")
		$(this).parent().siblings().removeClass("on")
	})
	$(".listLeft4").click(function(){
		$(this).toggleClass("on")
		$(this).siblings().toggleClass("show")
		$(this).parent().siblings().children().removeClass("show")
		$(this).parent().parent().siblings().find(".listLeft5").removeClass("show")
	})
	
	$(".listRight4").click(function(){
		$(this).find("img").toggle()
		$(".listRight5").toggle()
	})
	
	$(".proDeta7 span").click(function(){
		$(this).addClass("on")
		$(this).siblings().removeClass("on")
	})
	$(".proDeta8 span").click(function(){
		$(this).addClass("on")
		$(this).siblings().removeClass("on")
		$(".proDeta9a span").removeClass("on")
		var _index=$(this).index();
		$(".proDeta9 .proDeta9a").eq(_index).addClass('show').siblings().removeClass('show');
	})
	$(".proDeta9a span").click(function(){
		$(this).addClass("on")
		$(this).siblings().removeClass("on")
	})
	
	
	$(".reduce").click(function(){
		var _val = $(this).siblings(".proDeta10a").val()
		if(_val > 1){
			_val--;
			$(this).siblings(".proDeta10a").val(_val)
		}
	})
	$(".add").click(function(){
		var _val = $(this).siblings(".proDeta10a").val()
		_val++;
		$(this).siblings(".proDeta10a").val(_val)
	})
	
	$(".question2").click(function(){
		$(this).parent().toggleClass("on")
		$(this).children(".q_img1").toggleClass("rotate")
	})
	$('#imgs_file1').change(function() {
		var file = this.files[0];
		var r = new FileReader();
		r.readAsDataURL(file);
		$(r).load(function() {
			$("#img_src_show1").css("opacity","1")
			$('#img_src_show1').attr('src', this.result)
		})
	})
	//商品の価格変更
	$(document).on('change', '.select_spec', function(){
		var v = $(this).val();
		var arrs = [];
		$('.select_spec option').each(function(i,n ){

			arrs[$(n).attr('value')] = $(n).attr('data-price');
			
		})
		$('.proDeta5 span').html( arrs[v] );
		//console.log( arrs );
	})
	//カートに追加
	$('.addshopping').on('click', function(){
	    var obj = $("#addshopping-form");
	    var jsonData = obj.serializeArray();
	    $.ajax({
	       type: "POST",
	       url: "/api/user/addshopping",
	       data: jsonData,
	       success: function(res){
	       		$('.tips_tc .tips_tc3').html( res.msg );
	            $('.tips_tc').show();
	            setTimeout(function(){
	            	$('.tips_tc').hide();
	            },2000)
	          	if(res.code == 1){
		          	obj[0].reset();
		            //location.reload();
		        }
	       },
	       error: function(xhr, status, error) {
	            // エラー応答を処理
	            if(xhr.status == 401){
	            	tanchuang('ログイン後に操作してください');
	            }
	        }
	    });
	    return false;
	})
	//数値にカンマを付ける
	function formatNumber(num) {
	    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
	}
	//カート数量を変更
	$('.updateshopping').on('input', function(){
	    var obj = $(this);
	    var num = parseInt(obj.val());

	    // 1000を超える場合は1000に制限
	    if (num > 1000) {
	        num = 1000;
	        obj.val(1000);
	    }
	    // 無効な値の場合はAJAX送信しない
	    if (isNaN(num) || num < 1) {
	        return;
	    }

	    var shopping_id = obj.parents('.pr_info2').attr('data-id');
	    var price = parseInt(obj.attr('data-price')) || 0;

	    // 小計をリアルタイム更新
	    obj.parents('tr').find('.subtotal-value').html(formatNumber(price * num));

	    $.ajax({
	       type: "POST",
	       url: "/api/user/updateshopping",
	       data: {shopping_id: shopping_id, num: num},
	       success: function(res){
	          	if(res.code == 1){
		          	$('#ftotal span').html( res.data.totalMoney );
		        }else{
		        	tanchuang(res.msg);
		        }
	       },
	       error: function(xhr, status, error) {
	            if(xhr.status == 401){
	            	tanchuang('ログイン後に操作してください');
	            }
	        }
	    });
	    return false;
	})
	$('.apply').click(function(){
		var type = $(this).attr('data-type');
		var xyh1 = $('#xyh1:checked').val();
		var xyh2 = $('#xyh2:checked').val();
		if(xyh1 != 1){
			tanchuang('プライバシーポリシーを確認してください。');
			return false;
		}
		if(xyh2 != 1){
			tanchuang('買取利用規約を確認してください。');
			return false;
		}
		window.location.href="/applyfor/"+type;
	})
	//カートから削除
	$('.delshopping').on('click', function(){
	    var obj = $(this);
	    var shopping_id = obj.parents('tr').attr('data-id');

	    $.ajax({
	       type: "POST",
	       url: "/api/user/delshopping",
	       data: {shopping_id: shopping_id},
	       success: function(res){
	       		
	          	if(res.code == 1){
		          	location.reload();
		        }else{
		        	tanchuang(res.msg);
		        }
	       },
	       error: function(xhr, status, error) {
	            // エラー応答を処理
	            if(xhr.status == 401){
	            	tanchuang('ログイン後に操作してください');
	            }
	        }
	    });
	    return false;
	})
	//ログイン
	$('.submitlogin').on('click', function(){
	    var obj = $("#login-form");
	    var jsonData = obj.serializeArray();
	    $.ajax({
	       type: "POST",
	       url: "/api/user/login",
	       data: jsonData,
	       success: function(res){
	          if(res.code == 0){

	            tanchuang(res.msg);
	          }else{
	             //obj[0].reset();
	             location.reload();
	            //
	          }

	       },
	    });
	    return false;
	})
	
	//新規登録
	$('.submitregister').on('click', function(){
	    var obj = $("#register-form");
	    var jsonData = obj.serializeArray();
	    $.ajax({
	       type: "POST",
	       url: "/api/user/register",
	       data: jsonData,
	       success: function(res){
	       	tanchuang(res.msg, 3000, res.code == 1 ? 'reload' : '');
	          if(res.code == 1){
				obj[0].reset();
	          }

	       },
	    });
	    return false;
	})
	//ユーザー情報を変更
	$('#edituser-form').on('submit', function(e){
	    e.preventDefault();
	    var obj = $(this);
	    var persionType = obj.find('#persion_type').val();
	    obj.find('#formPersonal input, #formPersonal select').prop('disabled', persionType !== '1');
	    obj.find('#formCorporate input, #formCorporate select').prop('disabled', persionType !== '2');
	    var jsonData = obj.serializeArray();
	    obj.find('input, select').prop('disabled', false);
	    $.ajax({
	       type: "POST",
	       url: "/api/user/profile",
	       data: jsonData,
	       success: function(res){
	       		tanchuang(res.msg);	
	          if(res.code == 1){
	          	window.location.href = '/user/index';
	          }
	       },
	    });
	    return false;
	})

	$(document).on('change', '.img-upload', function() {
		var file = this.files[0];
		if (!file) return;
		var target = $(this).data('target');
		var containerId = $(this).data('container');
		var $container = $('#' + containerId);
		if (!$container.length) return;
		var allowedExtensions = /(\.png|\.jpg|\.jpeg|\.gif)$/i;
		var formData = new FormData();
		formData.append('file', file);
		var $input = $(this);

			if (!allowedExtensions.exec(file.name)) {
			    alert('アップロードしてくださいPNG、JPG、JPEGまたはGIF形式の画像！');
			    return false; // 形式が正しくない場合，後続の処理を中止する
			}
			// ... ファイルを処理 ...
			$.ajax({
			    url: '/api/common/upload', // サーバー側でファイルアップロードを処理するスクリプトのアドレス
			    type: 'POST',
			    data: formData,
			    processData: false, // 知らせる jQuery 送信データを処理しないようにする
			    contentType: false, // 知らせる jQuery Content-Typeヘッダー情報を設定しないようにする
			    success: function(data) {
			        // アップロード成功後のコールバック関数，data はサーバーが返すデータです
			        if(data.code == 1){
			   //      	var r = new FileReader();
						// r.readAsDataURL(file);
						// $(r).load(function() {
						// 	$("#img_src_show1").css("opacity","1")
						// 	$('#img_src_show1').attr('src', data.data.url)
						// })
						//$("#img_src_show1").css("opacity","1")
			        	//$('#img_src_show1').attr('src', data.data.url)
			        	var nameAttr = target.indexOf('[]')>=0 ? target : target+'[]';
			        	$container.append('<span><img alt="" src="'+data.data.url+'"/><img class="newclose" alt="" src="/img/close.png"/><input type="hidden" name="'+nameAttr+'" value="'+data.data.url+'"/></span>');
			        	$input.val('');
			        }
			        console.log('アップロード成功');
			        console.log(data);
			    },
			    error: function(jqXHR, textStatus, errorThrown) {
			        // アップロード失敗時のコールバック関数，jqXHR はい XMLHttpRequest オブジェクト，textStatus はい请求状态，errorThrown はい异常信息
			        console.log('アップロード失敗');
			        console.log(textStatus);
			        console.log(errorThrown);
			    }
			});
	})
	
	$(document).on('click','.newclose', function(){
	    var id = $(this).attr('data-id');
	    $(this).parent('span').remove();
	    
	})
	
	//来店時間を設定
	$('#go_store_time').on('click', function(){
	    var dateInput = $('#dateInput').val();
	    for (var i = 11; i < 18; i++) {
	        
	    }
	})

	//お問い合わせ
	$('.submitcontactus').on('click', function(){
	    var obj = $("#contactus-form");
	    var jsonData = obj.serializeArray();
	    var grqb = $('#grqb:checked').val();
	    console.log(grqb);
		if(grqb != 1){
			tanchuang('個人情報の取り扱いを確認してください。');
			return false;
		}
	    $.ajax({
	       type: "POST",
	       url: "/api/user/contactus",
	       data: jsonData,
	       success: function(res){
	       		tanchuang(res.msg, 3000, 'reload');
		        if(res.code == 1){
		          	obj[0].reset();
		             
		            
		        }

	       },
	    });
	    return false;
	})
	//注文を送信
	$('.submitorder').on('click', function(){
	    var obj = $("#order-form");
	    var jsonData = obj.serializeArray();
	    $.ajax({
	       type: "POST",
	       url: "/api/user/addOrder",
	       data: jsonData,
	       success: function(res){
	       		
		        if(res.code == 1){
		            window.location.href = '/applyfor_complete';
		        }else{
		        	tanchuang(res.msg);
		        }
	       },
	    });
	    return false;
	})
	//注文確定をキャンセル
	$('.cancle').on('click', function(){
	    var obj = $(this);
	    var order_id = obj.parents('.record1').attr('data-id');

	    $('.tips_tc .tips_tc3').html( 'この予約をキャンセルしてもよろしいですか？' );
        $('.tips_tc').show();
        $('.querenbox').show();
        $('.yesCancel').addClass('cancle_confirm');
        $('.yesCancel').attr('data-id', order_id);

	    return false;
	})

	$('.noCancel').on('click', function(){
		$('.tips_tc').hide();
		$('.yesCancel').removeClass('cancle_confirm');
        $('.querenbox').hide();
	})

	//注文をキャンセル
	$(document).on('click','.cancle_confirm', function(){
	    var obj = $(this);
	    var order_id = obj.attr('data-id');

	    $.ajax({
	       type: "POST",
	       url: "/api/user/cancleOrder",
	       data: {order_id: order_id},
	       success: function(res){
	          	if(res.code == 1){
		          	location.reload();
		        }else{
		        	tanchuang(res.msg);
		        }
	       },
	       error: function(xhr, status, error) {
	            // エラー応答を処理
	            if(xhr.status == 401){
	            	tanchuang('ログイン後に操作してください');
	            }
	        }
	    });
	    return false;
	})

	$('.searchbutton').on('click', function(){
		var keywords = $('.keywords').val();
		window.location.href="/goods?kwd="+keywords;
	})

	//パスワードをリセット
	$('.submitresetpwd').on('click', function(){
	    var obj = $("#resetpwd-form");
	    var jsonData = obj.serializeArray();
	    $.ajax({
	       type: "POST",
	       url: "/api/user/resetpwd",
	       data: jsonData,
	       success: function(res){
	       		tanchuang(res.msg, 3000, 'reload');
	          if(res.code == 1){
	          		obj[0].reset();
	            
	          }

	       },
	    });
	    return false;
	})

	$('.new_lab').on('change', function(){
		var v = $(this).val();
		if(v == 1){
			$('#et').hide();
		}else{
			$('#et').show();
		}
	})
	
	
	var lockCode = false;
    var countdown = 60;
    var _generate_code = $("#email2");
    
    $('.sendEms').on('click', function(){
        var obj = $(this);
        //var mobile = $('#mobilelogin-form .phone').val();
        var email = obj.parents('.login_tc5').find('.email').val();
     
        getcode(email, obj);

        return false;
    })
	
	/**
     * 認証コードを取得
     */
    function getcode(email, obj) {
        if (lockCode) {
            return;
        }
        var event = obj.attr('data-event');

        lockCode = true;
        $.ajax({
            url: '/api/ems/send',
            type: 'post',
            data: {email: email,event:event},
            dataType: 'json',
            success: function (d) {
             
                if (d.code == 1) {
                    settime(obj);
                } else {
                    lockCode = false;
                	tanchuang(d.msg);
                }
            }
        });
        return false;
    }
    
    function settime(obj) {
        if (countdown == 0) {
            lockCode = false;
            obj.html("配信");
            countdown = 60;
            return false;
        } else {
            obj.html("再配信(" + countdown + ")");
            countdown--;
        }
        setTimeout(function () {
            settime(obj);
        }, 1000);
    }
	
	
	function tanchuang(msg, time=2000,url='')
	{
		$('.tips_tc .tips_tc3').html( msg );
        $('.tips_tc').show();
        setTimeout(function(time){
        	$('.tips_tc').hide();
        	if(url != ''){
        		if(url == 'reload'){
        			location.reload();
	        	}else{
	        		window.location.href = url;
	        	}
        	}
        	
        },time)
	}
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
})
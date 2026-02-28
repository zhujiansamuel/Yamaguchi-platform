<?php

namespace app\index\controller;

use app\common\controller\Frontend;
use app\common\model\Goods;
use app\common\model\News;
use app\common\model\Order;
use custom\ConfigStatus as CS;
use think\Db;
class Index extends Base
{

    protected $noNeedLogin = '*';
    protected $noNeedRight = '*';
    //protected $layout = '';

    public function _initialize()
    {
        // 编辑器相关方法不需要数据库初始化
        $action = $this->request->action();
        if (in_array($action, ['template_editor', 'get_template', 'save_template'])) {
            // 跳过父类初始化
            return;
        }
        parent::_initialize();
    }

    public function index()
    {
    	//スライドショー
    	$lunbo = db('lunbo')->order('weigh desc')->select();
    	//ニュース
    	$news = db('news')->where('recomm', 1)->order('weigh desc')->limit(3)->select();
    	//商品カテゴリ
    	$goodsCategory = db('category')->where('type', 'goods')->where('pid', 0)->order('weigh desc')->select();
    	//商品おすすめ
    	$goods = Goods::where('recomm', 1)->order('weigh desc')->limit(8)->select();

    	$category = db('category')->field('id,type,name,image,description')
    	  ->whereIn('type', 'buy_way,select_reason')
    	  ->where('pid', 0)
    	  ->order('weigh desc')->select();
    	$buy_way = $select_reason = [];
    	foreach ($category as $key => $val) {
    		if($val['type'] == 'buy_way'){
    			$buy_way[] = $val;
    		}else if($val['type'] == 'select_reason'){
    			$select_reason[] = $val;
    		}
    	}
    	
    	$this->view->assign('lunbo', $lunbo);
    	$this->view->assign('goods', $goods);
    	$this->view->assign('news', $news);
    	$this->view->assign('goodsCategory', $goodsCategory);
    	$this->view->assign('buy_way', $buy_way);
    	$this->view->assign('select_reason', $select_reason);
    	$this->view->assign('title', __('ホーム'));

    	// Open Graph設定
    	$this->view->assign('og_type', 'website');
    	$this->view->assign('og_title', 'Mobile Zone 買取 - スマートフォン・パソコン高価買取専門店');
    	$this->view->assign('og_description', '東京都中央区でスマートフォン、パソコン、デジタル機器の高価買取を行っています。店頭買取・郵送買取に対応。お気軽にお問い合わせください。');

        return $this->view->fetch();
    }

    /*
     * 商品一覧
     */
    public function goods()
    {
    	$keywords = $this->request->request('kwd');
    	$category_id = $this->request->param('category_id');
    	$category_second = $this->request->param('category_second');
    	$category_three = $this->request->param('category_three');
    	$where = [];
    	$category_name = '';
    	if($category_id){
    		$where['category_id'] = $category_id;
    		$category_name = db('category')->where('id', $category_id)->value('name');
    	}
    	if($keywords){
    		$where['title'] = ['like', '%'.$keywords.'%'];
    	}
    	$category_second_name = '';
    	if($category_second){
    		$where['category_second'] = $category_second;
    		$category_second_name = db('category')->where('id', $category_second)->value('name');
    	}
    	$category_three_name = '';
    	if($category_three){
    		$where['category_three'] = $category_three;
    		$category_three_name = db('category')->where('id', $category_three)->value('name');
    	}
    	$goods = Goods::where($where)->order('weigh desc, id desc')->paginate(16);
    	$page = $goods->render();
    
    	$this->view->assign('title', __('商品一覧'));
    	$this->view->assign('goods', $goods);
    	$this->view->assign('category_id', $category_id);
    	$this->view->assign('category_second', $category_second);
    	$this->view->assign('category_three', $category_three);
    	$this->view->assign('category_name', $category_name);
    	$this->view->assign('category_second_name', $category_second_name);
    	$this->view->assign('category_three_name', $category_three_name);
    	$this->view->assign('page', $page);
    	return $this->view->fetch();
    }

    /*
     * 商品詳細
     */
    public function goods_details()
    {
    	$id = $this->request->param('id');
    	$where = [];
    	$where['id'] = $id;
    	$goods = Goods::where($where)->find();
    	if(!$goods){
    		$this->error('商品が存在しません');
    	}
    	$goods['color'] = $goods['color'] ? json_decode($goods['color'], true) : [];//db('category')->field('id,name')->whereIn('id', $goods['color_id'])->select();
    	$this->view->assign('title', __('商品一覧') . $goods['title']);
    	$this->view->assign('goods', $goods);

    	// Open Graph設定
    	$this->view->assign('og_type', 'product');
    	$this->view->assign('og_title', $goods['title'] . ' - 高価買取中');
    	$this->view->assign('og_description', $goods['memo'] ? $goods['memo'] : $goods['title'] . 'の買取を行っています。東京都中央区の買取専門店Mobile Zone。');
    	$this->view->assign('og_image', $goods['image']);

        return $this->view->fetch();
    }

    /*
     * ニュース一覧
     */
    public function news()
    {
    	$category_id = $this->request->param('category_id');
    	$category_second = $this->request->param('category_second');
    	$category_three = $this->request->param('category_three');
    	$where = [];
    	$category_name = '';
    	if($category_id){
    		$where['category_id'] = $category_id;
    		$category_name = db('category')->where('id', $category_id)->value('name');
    	}
    	$category_second_name = '';
    	if($category_second){
    		$where['category_second'] = $category_second;
    		$category_second_name = db('category')->where('id', $category_second)->value('name');
    	}
    	$category_three_name = '';
    	if($category_three){
    		$where['category_three'] = $category_three;
    		$category_three_name = db('category')->where('id', $category_three)->value('name');
    	}
    	$news = News::where($where)->order('weigh desc, id desc')->paginate(8);
    	$page = $news->render();
    
    	$this->view->assign('title', __('お知らせ'));
    	$this->view->assign('news', $news);
    	$this->view->assign('category_id', $category_id);
    	$this->view->assign('category_second', $category_second);
    	$this->view->assign('category_three', $category_three);
    	$this->view->assign('category_name', $category_name);
    	$this->view->assign('category_second_name', $category_second_name);
    	$this->view->assign('category_three_name', $category_three_name);
    	$this->view->assign('page', $page);
    	return $this->view->fetch();
    }

    /*
     * ニュース詳細
     */
    public function news_details()
    {
    	$id = $this->request->param('id');
    	$where = [];
    	$where['id'] = $id;
    	$news = News::where($where)->find();
    	if(!$news){
    		$this->error('商品が存在しません');
    	}
    	$this->view->assign('title', __('お知らせ').'-'.$news['title']);
    	$this->view->assign('news', $news);

    	// Open Graph設定
    	$this->view->assign('og_type', 'article');
    	$this->view->assign('og_title', $news['title']);
    	$this->view->assign('og_description', $news['desc'] ? $news['desc'] : mb_substr(strip_tags($news['content']), 0, 150));
    	if($news['image']){
    		$this->view->assign('og_image', $news['image']);
    	}

        return $this->view->fetch();
    }

    /*
     * 店舗紹介
     */
    public function shop()
    {
    	$this->view->assign('title', __('店舗紹介'));
        return $this->view->fetch();
    }

    /*
     * 買取方法
     */
    public function buy_way()
    {
    	$buy_way_type = db('category')->where('type', 'buy_way')->order('weigh desc')->select();

    	$buy_way = db('buy_way')->order('weigh desc')->select();
    	$buy_way_list = [];
    	foreach ($buy_way as $key => $val) {
    		$buy_way_list[$val['category_id']][] = $val;
    	}
    	$this->view->assign('title', __('買取方法'));
    	$this->view->assign('buy_way_type', $buy_way_type);
    	$this->view->assign('buy_way_list', $buy_way_list);
        return $this->view->fetch();
    }

    /*
     * 利用ガイド
     */
    public function guide()
    {
    	$guide_type = db('category')->where('type', 'guide')->order('weigh desc')->select();

    	$guide = db('guide')->order('weigh desc')->select();
    	$guide_list = [];
    	foreach ($guide as $key => $val) {
    		$guide_list[$val['category_id']][] = $val;
    	}
    	$this->view->assign('title', __('ご利用ガイド'));
    	$this->view->assign('guide_type', $guide_type);
    	$this->view->assign('guide_list', $guide_list);
        return $this->view->fetch();
    }

    /*
     * 利用規約 - 買取利用規約
     */
    public function use_terms()
    {
    	$this->view->assign('title', __('買取利用規約'));
        return $this->view->fetch();
    }

    /*
     * お問い合わせ
     */
    public function contactus()
    {
    	$this->view->assign('title', __('お問い合わせ'));
        return $this->view->fetch();
    }

    /*
     * プライバシーーポリシー - プライバシー-ポリシー-
     */
    public function privacy_policy()
    {
    	$this->view->assign('title', __('プライバシー'));
        return $this->view->fetch();
    }

    /*
     * よくある質問 - よくある質問
     */
    public function faq()
    {
    	$faq = db('category')->where('type', 'faq')->order('weigh desc')->select();
    	$this->view->assign('title', __('よくある質問'));
    	$this->view->assign('faq', $faq);
        return $this->view->fetch();
    }

    /*
     * 特定商取引法に基づく表示 - 特定商取引法に基づく表示
     */
    public function trading_law()
    {
    	$this->view->assign('title', config('site.trading_law_name'));
        return $this->view->fetch();
    }

    /*
     * 買取申込書（空模板）- 用于生成空白PDF
     */
    public function ylindex_empty()
    {
        $rt = 0;
        $today = date('Y-m-d');
        $order = [
            'createtime' => $today,
            'details' => [],
            'total_price' => '0',
            'bank' => '',
            'bank_branch_no' => '',
            'bank_branch' => '',
            'bank_account' => '',
            'bank_account_name' => '',
            'store' => null,
        ];
        $user = [
            'katakana' => '',
            'gender' => null,
            'name' => '',
            'birthday' => '2000-01-01',
            'mobile' => '',
            'address' => '',
            'zip_code' => '',
            'business_number' => '',
            'occupation' => null,
            'szb' => null,
        ];
        $this->view->assign('title', '申込書');
        $this->view->assign('order', $order);
        $this->view->assign('user', $user);
        $this->view->assign('age', '');
        $this->view->assign('totalNum', 0);
        $this->view->assign('rt', $rt);
        $this->view->assign('formatted_phone', '');
        $this->view->assign('zip_part1', '');
        $this->view->assign('zip_part2', '');
        $this->view->assign('ornum', 1);
        $this->view->assign('is_szb_other', 0);
        $this->view->assign('site', config('site'));
        return $this->view->fetch('index/ylindex');
    }

    /*
     * 買取申込書
     */
    public function ylindex()
    {
    	$order_id = $this->request->param('id');
    	$rt = $this->request->request('rt') ?: 0;

    	$where = [];
    	$where['id'] = $order_id;

        $order = Order::with('user,store,details')
        ->where($where)->order('id desc')->find();

        if (!$order) {
            $this->error('注文が見つかりません');
        }

        $totalNum = 0;
        foreach ($order['details'] ?? [] as $key => $val) {
        	$totalNum += $val['num'];
        	$val['total_price'] = number_format($val['num'] * str_replace(',','',$val['price']));
        }
        $age = 0;
        $user = db('user')->where('id', $order['user_id'])->find() ?: [];
        if(!empty($user)){
            $today = new \DateTime();
            $diff = $today->diff(new \DateTime($user['birthday']));
            $age = $diff->y;
        }

        // 電話番号 日本格式分段：携帯3-4-4、固定2-4-4
        $formatted_phone = '';
        if(!empty($user) && !empty($user['mobile'])){
            $digits = preg_replace('/\D/', '', $user['mobile']);
            if(strlen($digits) >= 10 && $digits[0] == '0'){
                if(in_array(substr($digits,1,2), ['90','80','70','60','50'])) {
                    $formatted_phone = substr($digits,0,3).'-'.substr($digits,3,4).'-'.substr($digits,7);
                } else {
                    $formatted_phone = substr($digits,0,2).'-'.substr($digits,2,4).'-'.substr($digits,6);
                }
            } else {
                $formatted_phone = $user['mobile'];
            }
        }

        // 郵便番号 3桁-4桁
        $zip_part1 = $zip_part2 = '';
        if(!empty($user) && !empty($user['zip_code'])){
            $zip_digits = preg_replace('/\D/', '', $user['zip_code']);
            if(strlen($zip_digits) >= 7){
                $zip_part1 = substr($zip_digits,0,3);
                $zip_part2 = substr($zip_digits,3,4);
            } else {
                $zip_part1 = $user['zip_code'];
            }
        }

        // 当店のご利用回数：該当ユーザーの完了済み注文数（入庫完了7・入金完了8）で新規/2回目以降
        // 新規=初回利用、２回目以降=既に1回以上完了済み
        $completedStatuses = [7, 8]; // 入庫完了、入金完了
        $ordCount = db('order')->where('user_id', $order['user_id'])->whereIn('admin_status', $completedStatuses)->count();
        $currentCompleted = !empty($order['admin_status']) && in_array($order['admin_status'], $completedStatuses);
        if ($currentCompleted) {
            $ornum = ($ordCount <= 1) ? 1 : 0;  // 当前订单已计入，1件=新規
        } else {
            $ornum = ($ordCount == 0) ? 1 : 0;   // 当前订单未计入，0件=新規
        }

        // 身分証明書 szb その他判定（個人）
        $is_szb_other = (!empty($user) && ($user['persion_type'] ?? 1) == 1 && !empty($user['szb']) && !in_array($user['szb'], [46,50,51,55])) ? 1 : 0;
        // 法人：corporate_szb_1 の種別表示用（fa_category.name でマッピング）
        // ※管理画面で corporate_szb_1 のカテゴリ名称を変更した場合は、以下の文字列比較を合わせて修正すること
        $corp_szb_name = !empty($user) && ($user['persion_type'] ?? 1) == 2 && !empty($user['corporate_szb_1']) ? getCategoryName($user['corporate_szb_1']) : '';
        $is_corp_driver = ($corp_szb_name == '運転免許証のコピー');
        $is_corp_mynum = ($corp_szb_name == '個人番号カード');
        $is_corp_pass = ($corp_szb_name == 'パスポート写し(写真面＋住所面)');
        $is_corp_zairyu = ($corp_szb_name == '在留カード');
        $is_corp_other = ($corp_szb_name == 'その他');

    	$this->view->assign('title', '申込書');
    	$this->view->assign('order', $order);
    	$this->view->assign('user', $user);
    	$this->view->assign('age', $age);
    	$this->view->assign('totalNum', $totalNum);
    	$this->view->assign('rt', $rt);
    	$this->view->assign('ornum', $ornum);
    	$this->view->assign('formatted_phone', $formatted_phone);
    	$this->view->assign('zip_part1', $zip_part1);
    	$this->view->assign('zip_part2', $zip_part2);
    	$this->view->assign('is_szb_other', $is_szb_other);
    	$this->view->assign('is_corp_driver', $is_corp_driver);
    	$this->view->assign('is_corp_mynum', $is_corp_mynum);
    	$this->view->assign('is_corp_pass', $is_corp_pass);
    	$this->view->assign('is_corp_zairyu', $is_corp_zairyu);
    	$this->view->assign('is_corp_other', $is_corp_other);
        return $this->view->fetch();
    }

    /*
     * 模板编辑器 - 使用 GrapesJS
     */
    public function template_editor()
    {
        // 禁用模板布局
        $this->view->engine->layout(false);
        $this->view->assign('title', '買取申込書模板编辑器');
        return $this->view->fetch();
    }

    /*
     * 获取模板内容
     */
    public function get_template()
    {
        $template_file = APP_PATH . 'index/view/index/ylindex.html';
        if (file_exists($template_file)) {
            $content = file_get_contents($template_file);
            return json(['code' => 1, 'data' => $content]);
        } else {
            return json(['code' => 0, 'msg' => '模板文件不存在']);
        }
    }

    /*
     * 保存模板内容
     */
    public function save_template()
    {
        if ($this->request->isPost()) {
            $content = $this->request->post('content');
            if (empty($content)) {
                return json(['code' => 0, 'msg' => '内容不能为空']);
            }

            $template_file = APP_PATH . 'index/view/index/ylindex.html';

            // 备份原文件
            $backup_file = APP_PATH . 'index/view/index/ylindex.html.backup.' . date('YmdHis');
            if (file_exists($template_file)) {
                copy($template_file, $backup_file);
            }

            // 保存新内容
            if (file_put_contents($template_file, $content)) {
                return json(['code' => 1, 'msg' => '保存成功', 'backup' => basename($backup_file)]);
            } else {
                return json(['code' => 0, 'msg' => '保存失败']);
            }
        }
        return json(['code' => 0, 'msg' => '非法请求']);
    }

}

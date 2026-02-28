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

    public function index()
    {
    	//轮播
    	$lunbo = db('lunbo')->order('weigh desc')->select();
    	//新闻
    	$news = db('news')->where('recomm', 1)->order('weigh desc')->limit(3)->select();
    	//商品大类
    	$goodsCategory = db('category')->where('type', 'goods')->where('pid', 0)->order('weigh desc')->select();
    	//商品推荐
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
        return $this->view->fetch();
    }

    /*
     * 商品列表
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
     * 商品详情
     */
    public function goods_details()
    {
    	$id = $this->request->param('id');
    	$where = [];
    	$where['id'] = $id;
    	$goods = Goods::where($where)->find();
    	if(!$goods){
    		$this->error('商品不存在');
    	}
    	$goods['color'] = $goods['color'] ? json_decode($goods['color'], true) : [];//db('category')->field('id,name')->whereIn('id', $goods['color_id'])->select();
    	$this->view->assign('title', __('商品一覧') . $goods['title']);
    	$this->view->assign('goods', $goods);
        return $this->view->fetch();
    }

    /*
     * 新闻列表
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
     * 新闻详情
     */
    public function news_details()
    {
    	$id = $this->request->param('id');
    	$where = [];
    	$where['id'] = $id;
    	$news = News::where($where)->find();
    	if(!$news){
    		$this->error('商品不存在');
    	}
    	$this->view->assign('title', __('お知らせ').'-'.$news['title']);
    	$this->view->assign('news', $news);
        return $this->view->fetch();
    }

    /*
     * 店铺介绍
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
     * 使用指南
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
     * 使用条款 - 買取利用規豹
     */
    public function use_terms()
    {
    	$this->view->assign('title', __('買取利用規約'));
        return $this->view->fetch();
    }

    /*
     * 联系我们
     */
    public function contactus()
    {
    	$this->view->assign('title', __('お問い合わせ'));
        return $this->view->fetch();
    }

    /*
     * 隐私政策 - プライバシ-ボリシ-
     */
    public function privacy_policy()
    {
    	$this->view->assign('title', __('プライバシー'));
        return $this->view->fetch();
    }

    /*
     * 常见问题 - よくある質問
     */
    public function faq()
    {
    	$faq = db('category')->where('type', 'faq')->order('weigh desc')->select();
    	$this->view->assign('title', __('よくある質問'));
    	$this->view->assign('faq', $faq);
        return $this->view->fetch();
    }

    /*
     * 根据特定商品交易法的公示 - 特定商取引法に基づく表示
     */
    public function trading_law()
    {
    	$this->view->assign('title', config('site.trading_law_name'));
        return $this->view->fetch();
    }

    /*
     * 买取申请书
     */
    public function ylindex()
    {
    	$order_id = $this->request->param('id');
    	$rt = $this->request->request('rt') ?: 0;
    
    	$where = [];
    	$where['id'] = $order_id;
        
        $order = Order::with('user,store,details')
        ->where($where)->order('id desc')->find();

        $totalNum = 0;
        foreach ($order['details'] as $key => $val) {
        	$totalNum += $val['num'];
        	$val['total_price'] = number_format($val['num'] * str_replace(',','',$val['price']));
        }
        $age = 0;
        $user = db('user')->where('id', $order['user_id'])->find();
        if($user){
            $today = new \DateTime();
            $diff = $today->diff(new \DateTime($user['birthday']));
            $age = $diff->y;
        }
   
    	$this->view->assign('title', '申请书');
    	$this->view->assign('order', $order);
    	$this->view->assign('user', $user);
    	$this->view->assign('age', $age);
    	$this->view->assign('totalNum', $totalNum);
    	$this->view->assign('rt', $rt);
        return $this->view->fetch();
    }

    

}

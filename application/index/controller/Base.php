<?php

namespace app\index\controller;

use app\common\controller\Frontend;
use fast\Tree;
class Base extends Frontend
{

    public function _initialize()
    {
        parent::_initialize();
        $auth = $this->auth;
        $this->view->assign('userInfo', $auth);
        $webController = $this->request->controller();
        $webAction = $this->request->action();
        $this->view->assign('webController', $webController);

        $this->view->assign('webAction', $webAction);
    
        //商品カテゴリ
        $goodsCategory = db('category')->where('type', 'goods')->order('weigh desc')->select();
        $goodsCategoryTree = getTree($goodsCategory);
        //FAQS
        $faqs = db('category')->where('type', 'faqs')->order('weigh desc')->select();
        //sns
        $sns = db('sns')->order('weigh desc')->select();
        $this->view->assign('sns', $sns);
        if($webAction == 'index'){
            // $tree = Tree::instance();
            // $tree->init($itineraryCategory);
            // $indexItineraryCategory = $tree->getTreeList($tree->getTreeArray(0), 'name');
            // $this->view->assign('indexItineraryCategory', $indexItineraryCategory);
        }

        if($webAction == 'index'){
            // $tree = Tree::instance();
            // $tree->init($destination);
            // $indexDestinationCategory = $tree->getTreeList($tree->getTreeArray(0), 'name');
            // $this->view->assign('indexDestinationCategory', $indexDestinationCategory);
        }
        
        $this->view->assign('goodsCategory', $goodsCategory);
        $this->view->assign('goodsCategoryTree', $goodsCategoryTree);
        unset($webAction, $webController);
    }
}

<?php

namespace app\admin\controller;

use app\common\controller\Backend;

/**
 * 注文詳細管理
 *
 * @icon fa fa-circle-o
 */
class OrderDetails extends Backend
{

    /**
     * OrderDetailsモデルオブジェクト
     * @var \app\admin\model\OrderDetails
     */
    protected $model = null;

    public function _initialize()
    {
        parent::_initialize();
        $this->model = new \app\admin\model\OrderDetails;
        $this->view->assign("typeList", $this->model->getTypeList());

        $this->order_id = $this->request->request('order_id');
        $this->view->assign("order_id", $this->order_id);
        $this->assignconfig('order_id', $this->order_id);
    }



    public function setEditData($row)
    {
        $goods = db('goods')->where('id', $row['goods_id'])->find();
        $goods['spec_info'] = json_decode($goods['spec_info'], true);
        $goods['color'] = json_decode($goods['color'], true);
        $row['goods'] = $goods;
        $row['color_id'] = db('category')->where('name', $row['color'])->value('id');

        return $row;
    }

    public function setDelData($data=null)
    {
        if($data){
            $order_details = db('order_details')->where('order_id', $data['order_id'])->select();
            $totalPrice = 0;
            foreach ($order_details as $key => $value) {
                $totalPrice += $value['num'] * $value['price'];
            }
            db('order')->where('id', $data['order_id'])->update([
                'total_price' => $totalPrice,
                'price' => $totalPrice,
            ]);
        }
    }

    public function handleParams($params=[])
    {
        if(!empty($params['color'])){
           
            //$params['color'] = db('category')->where('id', $params['color'])->value('name');
        }
        return $params;
    }

    public function handleDbOther($extend, $params, $row=[])
    {
        $id = $row ? $row['id'] : $extend['id'];
        $order_details = db('order_details')->where('order_id', $params['order_id'])->select();
        $totalPrice = 0;
        foreach ($order_details as $key => $value) {
            $totalPrice += $value['num'] * $value['price'];
        }
        db('order')->where('id', $params['order_id'])->update([
            'total_price' => $totalPrice,
            'price' => $totalPrice,
        ]);
    }


}

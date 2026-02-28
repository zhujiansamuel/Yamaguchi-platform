<?php

namespace app\admin\controller;

use app\common\controller\Backend;
use custom\ConfigStatus as CS;
use think\Db;

use PhpOffice\PhpSpreadsheet\Spreadsheet;
use PhpOffice\PhpSpreadsheet\Writer\Xlsx;
use PhpOffice\PhpSpreadsheet\Style\Alignment;
use PhpOffice\PhpSpreadsheet\Style\Border;
use PhpOffice\PhpSpreadsheet\Worksheet\Worksheet;
use PhpOffice\PhpSpreadsheet\IOFactory;
use PhpOffice\PhpSpreadsheet\Style\NumberFormat;

/**
 * 订单管理
 *
 * @icon fa fa-circle-o
 */
class Order extends Backend
{

    /**
     * Order模型对象
     * @var \app\admin\model\Order
     */
    protected $model = null;
    
    protected $noNeedLogin = ['details'];

    public function _initialize()
    {
        parent::_initialize();
        $this->model = new \app\admin\model\Order;
        $this->view->assign("bankAccountTypeList", $this->model->getBankAccountTypeList());
        $this->view->assign("payModeList", $this->model->getPayModeList());
        $this->view->assign("typeList", $this->model->getTypeList());

        $this->assignconfig("statusList", CS::ORDER_STATUS_LIST);
        $this->assignconfig("adminStatusList", CS::ORDER_STATUS_ADMIN_LIST);
    }



    public function handleList($list)
    {
        // $data = $list->items();
        // foreach ($data as $key => $val) {
        //     if($val['type'] == 1){
        //         $type_text = '店頭買取<br>('.$val['store_name'].')';
        //     }else{
        //         $type_text = '郵送買取';
        //     }
        //     $val['type'] = $type_text;
        // }
        return $list;
    }

    /*
     * 订单详情
     */
    public function details($ids=null)
    {
        $row = $this->model->get($ids);

        if ($this->request->isPost()) {
            $post = $this->request->post();
            // 启动事务
            Db::startTrans();
            try {
                
                if($post['type'] == 1){
                    db('user')->where('id', $post['user_id'])->update(['status' => 'normal']);
                    
                    db('drivers_license')->where('user_id', $post['user_id'])->update(['review' => 1]);

                    db('pay_auth')->where('user_id', $post['user_id'])->update(['review' => 1]);
                }else{
                    $this->model->where('id', $post['user_id'])->delete();

                    db('drivers_license')->where('user_id', $post['user_id'])->delete();

                    db('pay_auth')->where('user_id', $post['user_id'])->delete();
                }

                // 提交事务
                Db::commit();
            } catch (\Exception $e) {
                // 回滚事务
                Db::rollback();
                $this->error($e->getMessage());
            }
            $this->success('成功');
        }

        $order_details = db('order_details')->where('order_id', $row['id'])->select();
        $user = db('user')->where('id', $row['user_id'])->find();
        if($user){
            $user['szb_image'] = explode(',', $user['szb_image']);
        }
        $store = db('store')->where('id', $row['store_id'])->find();

        $this->view->assign("row", $row);
        $this->view->assign("user", $user);
        $this->view->assign("store", $store);
        $this->view->assign("order_details", $order_details);
        $orderStatusList = [];
        foreach (CS::ORDER_STATUS_ADMIN_LIST as $key => $val) {
            $orderStatusList[] = [
                'name' => $val,
                'value' => $key,
            ];
        }
        $this->view->assign("orderAdminStatusList", $orderStatusList);
        $this->view->assign('is_pdf', $this->is_pdf ?? false);
       
        return $this->view->fetch('details');
    }

    public function edit_status($order_id=null,$status=null)
    {
        $row = $this->model->get($order_id);
        $this->model->where('id', $order_id)->update([
            'status' => CS::ORDER_STATUS_DY_ADMIN_LIST[$status],
            'admin_status' => $status
        ]);
    
        $this->success('成功');
    }

    //修改订单信息
    public function edit_order_info($order_id=null)
    {
        $data = $this->request->post('row/a');
        $row = $this->model->get($order_id);
        if (false === $this->request->isPost()) {
            $this->view->assign("row", $row);
            return $this->view->fetch();
        }
        $update = [];
        $update['memo'] = $data['memo'];
        $update['determine_memo'] = $data['determine_memo'];
        $update['cancel_memo'] = $data['cancel_memo'];
        // 启动事务
        Db::startTrans();
        try {

            $this->model->where('id',$order_id)->update($update);

            // 提交事务
            Db::commit();
        } catch (\Exception $e) {
            // 回滚事务
            Db::rollback();
            throw new \think\Exception($e->getMessage());
        }
        $this->success('操作成功');
    }

    public function sendEms($ids=null,$type=null)
    {
        $row = $this->model->get($ids);
        $extend = [];
        $extend['user'] = db('user')->where('id', $row['user_id'])->find();
        $row['store'] = db('store')->where('id', $row['store_id'])->find();
        $row['details'] = db('order_details')->where('order_id', $row['id'])->select();
        $extend['order'] = $row;
        switch ($type) {
            case 1:
                //预约邮件
                #if($row['type'] == 1 && $row['pay_mode'] == 1){
                if($row['type'] == 1){
                    orderStoreManualYuYueSendEmail(
                        date('Y/m/d'),
                        $row['no'],
                        $extend['user']['email'],
                        $extend
                    );
                }else if($row['type'] == 2){ // && $row['pay_mode'] == 2
                    $extend['email_type'] = 2;
                    orderStoreManualYuYueSendEmail(
                        date('Y/m/d'),
                        $row['no'],
                        $extend['user']['email'],
                        $extend
                    );
                }
                $this->model->where('id', $ids)->update(['is_send_yuyue' => 1]);
                break;
            
            case 2:
                //$extend['user']['email'] = '1158870182@qq.com';
                //查定邮件
                if($row['type'] == 1){ // && $row['pay_mode'] == 1
                    $extend['subject'] = '査定完了のご案内「Mobile Zone」';
                    orderStoreManualQueDingSendEmail(
                        date('Y/m/d'),
                        $row['no'],
                        $extend['user']['email'],
                        $extend
                    );
                }else if($row['type'] == 2){ // && $row['pay_mode'] == 2
                    $extend['email_type'] = 2;
                    $extend['subject'] = '査定完了のご案内「Mobile Zone」';
                    orderStoreManualQueDingSendEmail(
                        date('Y/m/d'),
                        $row['no'],
                        $extend['user']['email'],
                        $extend
                    );
                }
                break;
            case 3:
                //取消订单邮件
                $extend['subject'] = 'ご予約がキャンセルされました「Mobile Zone」';
                orderStoreManualCancelSendEmail(
                    date('Y/m/d'),
                    $row['no'],
                    $extend['user']['email'],
                    $extend
                );
                break;
        }
        $this->success('成功');
    }
    
    /*
     * 导出
     */
    public function export()
    {
        $store_id = $this->request->request('store_id');
        $filter = $this->request->post('filter');
        $filter = json_decode($filter, true);

        $spreadsheet = new Spreadsheet();
        $sheet = $spreadsheet->getActiveSheet();
        $sheet->setCellValue('A1', '订单统计');
        //$sheet->setCellValue('A2', 'Hello PhpSpreadsheet !');
         
        $sheet->mergeCells('A1:G1');
        $sheet->getColumnDimension('A')->setWidth(50);
        // 设置列宽和行高
        $sheet->getColumnDimension('B')->setWidth(35);
        $sheet->getRowDimension(1)->setRowHeight(30);
        $sheet->getColumnDimension('C')->setWidth(20);
        $sheet->getColumnDimension('D')->setWidth(30);
        $sheet->getColumnDimension('E')->setWidth(30);
        //$sheet->getColumnDimension('F')->setWidth(30);

        $data = [
            [
                __('ID'),
                __('单号'),
                __('E-mail'),
                __('お名前(カナ)'),
                __('商品金额'),
                __('总价'),
                __('用户端状态'),
                __('管理员状态'),
                __('支付方式'),
                __('类型'),
                __('创建时间'),
            ],
        ];
         
        // 添加更多的数据和格式设置
        
        $where = [];
        if($filter){
            foreach ($filter as $key => $val) {
                $where['a.'.$key] = $val;
            }
        }

        $perFile = 3000;
        
        $rootPath = ROOT_PATH . 'public';

        $file_path = '/order/'.date('Ymd');
        $totalNum = db('order')->alias('a')->field('a.*')
          ->where($where)->count();

        $fileCount = ceil($totalNum / $perFile);
        $successFiles = [];
        for ($i=1; $i <= $fileCount; $i++) { 
            $list = db('order')->alias('a')->field('a.*')
              ->where($where)
              ->page($i)
              ->limit($perFile)
              ->order('a.id desc')
              ->select();
            $xingshu = 0;
            foreach ($list as $key => $val) {
                $user = db('user')->where('id', $val['user_id'])->find();
                if($val['type'] == 1){
                    //$store = db('store')->where('id', $val['store_id'])->find();
                    $type = '店頭買取('.$val['store_name'].')';
                }else{
                    $type = '郵送買取';
                }
                $data[$key+1] = [
                    $val['id'],
                    $val['no'],
                    $user['email'],
                    $user['name'],
                    $val['price'],
                    $val['total_price'],
                    CS::ORDER_STATUS_LIST[$val['status']],
                    CS::ORDER_STATUS_ADMIN_LIST[$val['admin_status']],
                    __('Pay_mode '.$val['pay_mode']),
                    $type,
                    date('Y-m-d H:i:s', $val['createtime'])
                ];
                
                $order_details = db('order_details')->where('order_id', $val['id'])->select();
                
                $order_details_data = [
                    [
                        __('商品'),
                        __('JAN'),
                        __('单价'),
                        __('台数'),
                        __('总金额'),
                    ],
                ];
                foreach ($order_details as $index => $item) {
                    $order_details_data[$index+1] = [
                        $item['title'],
                        (string)$item['jan'],
                        $item['price'],
                        $item['num'],
                        $item['price'] * $item['num'],
                    ];
                }
                
                $sheet->setCellValue('A'.($xingshu + 2), '订单ID:'.$val['id']);
                $sheet->mergeCells('A'.($xingshu + 2).':B'.($xingshu + 2));
                
                $sheet->setCellValue('C'.($xingshu + 2), '订单编号:'.$val['no']);
                $sheet->mergeCells('C'.($xingshu + 2).':G'.($xingshu + 2));
                
                $styleArray = [
                    'borders' => [
                        'outline' => [
                            'borderStyle' => Border::BORDER_THIN,
                            'color' => ['argb' => '000000'],
                        ],
                    ],
                ];
                
                
                
                //dump($order_details_data);
                foreach ($order_details_data as $rowIndex => $rowData) {
                    $columnIndex = 'A'; // 从A列开始
                    foreach ($rowData as $cellKey => $cellValue) {
                        $sheet->getStyle($columnIndex . ($rowIndex + 3 +$xingshu))->applyFromArray($styleArray);
                        $sheet->setCellValue($columnIndex . ($rowIndex + 3 +$xingshu), $cellValue); // 从第3行开始写入数据，跳过标题行
                        //$sheet->getStyle($columnIndex . ($rowIndex + 3 +$xingshu))->getNumberFormat()->setFormatCode(NumberFormat::FORMAT_TEXT);
                        $columnIndex++; // 移动到下一列
                    }
                }
                $xingshu += count($order_details_data) + 2;
                //dump($xingshu);
            }
            
            $sheet = $spreadsheet->createSheet();
            $sheet->setTitle("订单列表");
            $sheet->getColumnDimension('A')->setWidth(15);
            // 设置列宽和行高
            $sheet->getColumnDimension('B')->setWidth(30);
            $sheet->getRowDimension(1)->setRowHeight(30);
            $sheet->getColumnDimension('C')->setWidth(30);
            $sheet->getColumnDimension('D')->setWidth(30);
            $sheet->getColumnDimension('E')->setWidth(15);
            $sheet->getColumnDimension('F')->setWidth(15);
            $sheet->getColumnDimension('G')->setWidth(25);
            $sheet->getColumnDimension('H')->setWidth(25);
            $sheet->getColumnDimension('I')->setWidth(20);
            $sheet->getColumnDimension('J')->setWidth(35);
            $sheet->getColumnDimension('K')->setWidth(25);
          
            foreach ($data as $rowIndex => $rowData) {
                $columnIndex = 'A'; // 从A列开始
                foreach ($rowData as $cellValue) {
                    //$sheet->getColumnDimension($columnIndex . ($rowIndex + 2))->setWidth(60);
                    //$sheet->getRowDimension(1)->setRowHeight(20);
                    $sheet->setCellValue($columnIndex . ($rowIndex + 2), $cellValue); // 从第3行开始写入数据，跳过标题行
                    $columnIndex++; // 移动到下一列
                }
            }
            
            
            //die;

            // 设置单元格居中（例如，A1）
            $sheet->getStyle('A1')->getAlignment()->setHorizontal(Alignment::HORIZONTAL_CENTER);

            // 设置边框（例如，A1）
            // $styleArray = [
            //     'borders' => [
            //         'outline' => [
            //             'borderStyle' => Border::BORDER_THICK,
            //             'color' => ['argb' => 'FFFF0000'],
            //         ],
            //     ],
            // ];
            // $sheet->getStyle('A1')->applyFromArray($styleArray);

                        // 生成文件名
            $fileName = sprintf('order_%d_%d.xlsx', $i, time());
            //$filePath = $rootPath . '/member/' . $fileName;
            $writer = new Xlsx($spreadsheet);

            if (!is_dir($rootPath.$file_path)){ //判断目录是否存在 不存在就创建
                mkdir($rootPath.$file_path,0755,true);
            }
            $filename = $file_path.'/'.$fileName;
            
            $writer->save($rootPath.$filename);
            $successFiles[] = [
                'file' => $filename,
            ];
        }
        //dump($successFiles);
        
        
        
        $this->success('请求成功',null,$successFiles);
      
        // $zipname = $rootPath . $file_path . '/order.zip';
        // echo $zipname;die;
        // $zip = new \ZipArchive();

        // // 创建并打开ZIP文件
        // if ($zip->open($zipname, \ZipArchive::CREATE) !== TRUE) {
        //     //无法创建ZIP文件
        //     $this->error('无法创建ZIP文件');
        // }
        // foreach ($successFiles as $key => $val) {
        //     // 检查文件是否存在
        //     // if (!file_exists(ROOT_PATH . 'public'.$val)) {
        //     //     die('指定的图片文件不存在');
        //     // }
        //     // 添加文件到ZIP
        //     $zip->addFile($rootPath.$file_path.$val['file'], 'order'.$key.'.' . pathinfo($rootPath.$file_path.$val['file'], PATHINFO_EXTENSION));
        // }
        // // 关闭ZIP文件
        // $zip->close();
        
        // 设置HTTP头以触发下载
        // header('Content-Type: application/zip');
        // header('Content-Disposition: attachment; filename="' . basename($zipname) . '"');
        // header('Content-Length: ' . filesize($zipname));
        
        // // 读取并输出文件内容
        // readfile($zipname);
        //删除临时文件
        //unlink($zipname);
        
        exit;
        // ob_end_clean();     //清除缓冲区,避免乱码
        // $filename = date('YmdHis').'.xlsx';
        // /* 直接导出Excel，无需保存到本地，输出07Excel文件 */
        // // MIME 协议，文件的类型，不设置，会默认html
        // header('Content-Type:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'); 

        // // MIME 协议的扩展
        // header('Content-Disposition: attachment;filename="' . iconv("utf-8", "GB2312", $filename) . '.xlsx');
  
        // // 缓存控制
        // header('Cache-Control:max-age=0');
        
        // $objWriter = IOFactory::createWriter($spreadsheet, 'Xlsx');
        // $objWriter->save('php://output');
    }

    public function handleReturn($filter)
    {
        $where = [];
        
        return ['filter' => $filter];
        
    }
    
    public function pdfFile($ids=null)
    {
        //composer require mpdf/mpdf
        //$html = file_get_contents('https://www.fastrade-cloud.cn/index/index/tradedatapdf?id=9');
        $mpdf = new \Mpdf\Mpdf([
            'mode' => 'utf-8', 
            'format' => 'A4',
            'autoScriptToLang' => true,
            'autoLangToFont'   => true,
            'useSubstitutions' => true,
        ]);
        $mpdf->SetDisplayMode('fullpage');
        // $mpdf->autoScriptToLang = true;
        // $mpdf->autoLangToFont = true;
        
        $rootPath = ROOT_PATH . 'public';

        $file_path = '/order/'.date('Ymd').'/details/';
        if (!is_dir($rootPath.$file_path)){ //判断目录是否存在 不存在就创建
            mkdir($rootPath.$file_path,0755,true);
        }
        
        
        
        // 水印设置
        //追加盖章图片，貌似可以获取远程的，非必要请使用服务器本地的，以前tcpdf就是无法获取远程的，mpdf未测试远程图片
        // $file = 'images/seal/150.png';
        // $mpdf->Image($file, 140, 200);
        // //文字水印
        // $mpdf->SetWatermarkText(‘xxx’,0.5);//参数一是文字，参数二是透明度
        // $mpdf->showWatermarkText = true；
        // $mpdf->SetWatermarkImage(图片路径，0.5);//参数一是图片的位置，参数二是透明度
        // $mpdf->showWatermarkImage = true;
        $this->is_pdf = true;
        $html = $this->daochupdf($ids);
        //$html = file_get_contents('http://mobilezone.minamoto2025.com/index/index/daochupdf?ids='.$ids);

        $domainName = getProtocol();
        /***
        $html = preg_replace("/(<link .*?href=\")(\/.*?)(\".*?>)/is","\${1}".$domainName."\${2}\${3}",$html);
        $html = preg_replace("/(<script .*?src=\")(\/.*?)(\".*?>)/is","\${1}".$domainName."\${2}\${3}",$html);
        $html = preg_replace("/(<script .*?data-main=\")(\/.*?)(\".*?>)/is","\${1}".$domainName."\${2}\${3}",$html);
        $html = preg_replace("/(<img .*?src=\")(\/.*?)(\".*?>)/is","\${1}".$domainName."\${2}\${3}",$html);
        **/
        //echo $html;die;
        $mpdf->WriteHTML($html);
        
        $fileName = $rootPath.$file_path.$ids.".pdf";
        
        $mpdf->Output($fileName, 'F');
          // 设置HTTP头以触发下载
        header('Content-Type: application/zip');
        header('Content-Disposition: attachment; filename="' . basename($fileName) . '"');
        header('Content-Length: ' . filesize($fileName));
        
        // 读取并输出文件内容
        readfile($fileName);
        //删除临时文件
        unlink($fileName);
        
        exit;
    }

    /*
     * 订单详情
     */
    public function daochupdf($ids=null)
    {
        $row = db('order')->where('id', $ids)->find();

        $order_details = db('order_details')->where('order_id', $row['id'])->select();
        $user = db('user')->where('id', $row['user_id'])->find();
        if($user){
            $user['szb_image'] = explode(',', $user['szb_image']);
        }
        $store = db('store')->where('id', $row['store_id'])->find();

        $this->view->assign("row", $row);
        $this->view->assign("user", $user);
        $this->view->assign("store", $store);
        $this->view->assign("order_details", $order_details);
        $orderStatusList = [];
        foreach (CS::ORDER_STATUS_ADMIN_LIST as $key => $val) {
            $orderStatusList[] = [
                'name' => $val,
                'value' => $key,
            ];
        }
        $this->view->assign("orderAdminStatusList", $orderStatusList);
        $this->view->assign('is_pdf', $this->is_pdf ?? false);
        
        $this->view->engine->layout(false);
        return $this->view->fetch('daochupdf');
    }


}

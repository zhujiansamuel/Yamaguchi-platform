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
 * 注文管理
 *
 * @icon fa fa-circle-o
 */
class Order extends Backend
{

    /**
     * Orderモデルオブジェクト
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
     * 注文詳細
     */
    public function details($ids=null)
    {
        $row = $this->model->get($ids);

        if ($this->request->isPost()) {
            $post = $this->request->post();
            // トランザクションを開始
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

                // トランザクションをコミットする
                Db::commit();
            } catch (\Exception $e) {
                // トランザクションをロールバック
                Db::rollback();
                $this->error($e->getMessage());
            }
            $this->success('成功');
        }

        $order_details = db('order_details')->where('order_id', $row['id'])->select();
        $user = db('user')->where('id', $row['user_id'])->find();
        if($user){
            $user['szb_image'] = !empty($user['szb_image']) ? explode(',', $user['szb_image']) : [];
            if(($user['persion_type'] ?? 1) == 2){
                $user['corporate_szb_image_1'] = !empty($user['corporate_szb_image_1']) ? explode(',', $user['corporate_szb_image_1']) : [];
                $user['corporate_szb_image_2'] = !empty($user['corporate_szb_image_2']) ? explode(',', $user['corporate_szb_image_2']) : [];
                $user['corporate_szb_image_3'] = !empty($user['corporate_szb_image_3']) ? explode(',', $user['corporate_szb_image_3']) : [];
            }
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

    //注文情報を編集
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
        // トランザクションを開始
        Db::startTrans();
        try {

            $this->model->where('id',$order_id)->update($update);

            // トランザクションをコミットする
            Db::commit();
        } catch (\Exception $e) {
            // トランザクションをロールバック
            Db::rollback();
            throw new \think\Exception($e->getMessage());
        }
        $this->success('操作が成功しました');
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
                //予約メール
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
                //査定メール
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
                //注文キャンセルメール
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
     * エクスポート
     */
    public function export()
    {
        $store_id = $this->request->request('store_id');
        $filter = $this->request->post('filter');
        $filter = json_decode($filter, true);

        $spreadsheet = new Spreadsheet();
        $sheet = $spreadsheet->getActiveSheet();
        $sheet->setCellValue('A1', '注文統計');
        //$sheet->setCellValue('A2', 'Hello PhpSpreadsheet !');
         
        $sheet->mergeCells('A1:G1');
        $sheet->getColumnDimension('A')->setWidth(50);
        // 列幅と行高を設定
        $sheet->getColumnDimension('B')->setWidth(35);
        $sheet->getRowDimension(1)->setRowHeight(30);
        $sheet->getColumnDimension('C')->setWidth(20);
        $sheet->getColumnDimension('D')->setWidth(30);
        $sheet->getColumnDimension('E')->setWidth(30);
        //$sheet->getColumnDimension('F')->setWidth(30);

        $data = [
            [
                __('ID'),
                __('伝票番号'),
                __('E-mail'),
                __('お名前(カナ)'),
                __('商品金額'),
                __('合計金額'),
                __('ユーザー側ステータス'),
                __('管理者ステータス'),
                __('支払方法'),
                __('タイプ'),
                __('作成時間'),
            ],
        ];
         
        // さらにデータと書式設定を追加
        
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
                        __('単価'),
                        __('台数'),
                        __('合計金額'),
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
                
                $sheet->setCellValue('A'.($xingshu + 2), '注文ID:'.$val['id']);
                $sheet->mergeCells('A'.($xingshu + 2).':B'.($xingshu + 2));
                
                $sheet->setCellValue('C'.($xingshu + 2), '注文番号:'.$val['no']);
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
                    $columnIndex = 'A'; // 〜からA列の開始
                    foreach ($rowData as $cellKey => $cellValue) {
                        $sheet->getStyle($columnIndex . ($rowIndex + 3 +$xingshu))->applyFromArray($styleArray);
                        $sheet->setCellValue($columnIndex . ($rowIndex + 3 +$xingshu), $cellValue); // 第3行目からデータを書き込む，タイトル行をスキップ
                        //$sheet->getStyle($columnIndex . ($rowIndex + 3 +$xingshu))->getNumberFormat()->setFormatCode(NumberFormat::FORMAT_TEXT);
                        $columnIndex++; // 次の列に移動
                    }
                }
                $xingshu += count($order_details_data) + 2;
                //dump($xingshu);
            }
            
            $sheet = $spreadsheet->createSheet();
            $sheet->setTitle("注文一覧");
            $sheet->getColumnDimension('A')->setWidth(15);
            // 列幅と行高を設定
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
                $columnIndex = 'A'; // 〜からA列の開始
                foreach ($rowData as $cellValue) {
                    //$sheet->getColumnDimension($columnIndex . ($rowIndex + 2))->setWidth(60);
                    //$sheet->getRowDimension(1)->setRowHeight(20);
                    $sheet->setCellValue($columnIndex . ($rowIndex + 2), $cellValue); // 第3行目からデータを書き込む，タイトル行をスキップ
                    $columnIndex++; // 次の列に移動
                }
            }
            
            
            //die;

            // セルを中央揃えに設定（例えば，A1）
            $sheet->getStyle('A1')->getAlignment()->setHorizontal(Alignment::HORIZONTAL_CENTER);

            // 罫線を設定（例えば，A1）
            // $styleArray = [
            //     'borders' => [
            //         'outline' => [
            //             'borderStyle' => Border::BORDER_THICK,
            //             'color' => ['argb' => 'FFFF0000'],
            //         ],
            //     ],
            // ];
            // $sheet->getStyle('A1')->applyFromArray($styleArray);

                        // ファイル名を生成
            $fileName = sprintf('order_%d_%d.xlsx', $i, time());
            //$filePath = $rootPath . '/member/' . $fileName;
            $writer = new Xlsx($spreadsheet);

            if (!is_dir($rootPath.$file_path)){ //ディレクトリが存在するか判定 存在しなければ作成
                mkdir($rootPath.$file_path,0755,true);
            }
            $filename = $file_path.'/'.$fileName;
            
            $writer->save($rootPath.$filename);
            $successFiles[] = [
                'file' => $filename,
            ];
        }
        //dump($successFiles);
        
        
        
        $this->success('リクエスト成功',null,$successFiles);
      
        // $zipname = $rootPath . $file_path . '/order.zip';
        // echo $zipname;die;
        // $zip = new \ZipArchive();

        // // 作成して開くZIPファイル
        // if ($zip->open($zipname, \ZipArchive::CREATE) !== TRUE) {
        //     //作成できないZIPファイル
        //     $this->error('作成できないZIPファイル');
        // }
        // foreach ($successFiles as $key => $val) {
        //     // ファイルが存在するか確認
        //     // if (!file_exists(ROOT_PATH . 'public'.$val)) {
        //     //     die('指定された画像ファイルが存在しません');
        //     // }
        //     // ファイルを追加ZIP
        //     $zip->addFile($rootPath.$file_path.$val['file'], 'order'.$key.'.' . pathinfo($rootPath.$file_path.$val['file'], PATHINFO_EXTENSION));
        // }
        // // 無効ZIPファイル
        // $zip->close();
        
        // 設定を行うHTTPヘッダーを設定してダウンロードを開始
        // header('Content-Type: application/zip');
        // header('Content-Disposition: attachment; filename="' . basename($zipname) . '"');
        // header('Content-Length: ' . filesize($zipname));
        
        // // ファイル内容を読み込んで出力
        // readfile($zipname);
        //一時ファイルを削除
        //unlink($zipname);
        
        exit;
        // ob_end_clean();     //バッファをクリア,文字化けを回避
        // $filename = date('YmdHis').'.xlsx';
        // /* 直接エクスポートExcel，ローカルに保存する必要なし，出力07Excelファイル */
        // // MIME プロトコル，ファイルの種類，設定しない場合，デフォルトになるhtml
        // header('Content-Type:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'); 

        // // MIME プロトコルの拡張
        // header('Content-Disposition: attachment;filename="' . iconv("utf-8", "GB2312", $filename) . '.xlsx');
  
        // // キャッシュ制御
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
        if (!is_dir($rootPath.$file_path)){ //ディレクトリが存在するか判定 存在しなければ作成
            mkdir($rootPath.$file_path,0755,true);
        }
        
        
        
        // ウォーターマーク設定
        //印鑑画像を追加，リモートから取得できるようだ，不要な場合はサーバーローカルを使用してください，以前はtcpdfリモートを取得できなかった，mpdfリモート画像は未テスト
        // $file = 'images/seal/150.png';
        // $mpdf->Image($file, 140, 200);
        // //文字ウォーターマーク
        // $mpdf->SetWatermarkText(‘xxx’,0.5);//第1引数は文字列，第2パラメーターは透明度です
        // $mpdf->showWatermarkText = true；
        // $mpdf->SetWatermarkImage(画像パス，0.5);//第1パラメーターは画像の位置です，第2パラメーターは透明度です
        // $mpdf->showWatermarkImage = true;
        $this->is_pdf = true;
        $html = $this->daochupdf($ids);
        //$html = file_get_contents('http://mobilezone.minamoto2025.com/index/index/daochupdf?ids='.$ids);

        $domainName = getProtocol();

        // 将 HTTP URL 图片路径转换为本地文件路径，避免 mpdf HTTP 超时
        // 匹配类似 http://xxx/uploads/xxx.jpg 的URL，转换为 /path/to/public/uploads/xxx.jpg
        $publicPath = ROOT_PATH . 'public';
        $html = preg_replace_callback(
            "/(<img .*?src=\")(" . preg_quote($domainName, '/') . ")(\/.*?)(\".*?>)/is",
            function($matches) use ($publicPath) {
                // $matches[1] = '<img src="'
                // $matches[2] = 'http://domain'
                // $matches[3] = '/uploads/xxx.jpg'
                // $matches[4] = '" ...>'
                return $matches[1] . $publicPath . $matches[3] . $matches[4];
            },
            $html
        );

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
          // 設定を行うHTTPヘッダーを設定してダウンロードを開始
        header('Content-Type: application/zip');
        header('Content-Disposition: attachment; filename="' . basename($fileName) . '"');
        header('Content-Length: ' . filesize($fileName));
        
        // ファイル内容を読み込んで出力
        readfile($fileName);
        //一時ファイルを削除
        unlink($fileName);
        
        exit;
    }

    /*
     * 注文詳細
     */
    public function daochupdf($ids=null)
    {
        $row = db('order')->where('id', $ids)->find();

        $order_details = db('order_details')->where('order_id', $row['id'])->select();
        $user = db('user')->where('id', $row['user_id'])->find();
        if($user){
            $user['szb_image'] = !empty($user['szb_image']) ? explode(',', $user['szb_image']) : [];
            if(($user['persion_type'] ?? 1) == 2){
                $user['corporate_szb_image_1'] = !empty($user['corporate_szb_image_1']) ? explode(',', $user['corporate_szb_image_1']) : [];
                $user['corporate_szb_image_2'] = !empty($user['corporate_szb_image_2']) ? explode(',', $user['corporate_szb_image_2']) : [];
                $user['corporate_szb_image_3'] = !empty($user['corporate_szb_image_3']) ? explode(',', $user['corporate_szb_image_3']) : [];
            }
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

<?php

namespace app\admin\controller;

use app\common\controller\Backend;

/**
 * カルーセル画像管理
 *
 * @icon fa fa-circle-o
 */
class Lunbo extends Backend
{

    /**
     * Lunboモデルオブジェクト
     * @var \app\admin\model\Lunbo
     */
    protected $model = null;

    public function _initialize()
    {
        parent::_initialize();
        $this->model = new \app\admin\model\Lunbo;

    }



    /**
     * デフォルトで生成されるコントローラーが継承する親クラスにはindex/add/edit/del/multi5つの基本メソッド、destroy/restore/recyclebin3つのゴミ箱関連メソッド
     * そのため現在のコントローラーでは、CRUDコードを記述する必要はありません,この部分のロジックを自分で制御する必要がある場合を除き
     * をapplication/admin/library/traits/Backend.php中の対応するメソッドを現在のコントローラーにコピー,その後、修正を行う
     */


}

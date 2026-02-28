<?php

namespace app\api\controller;

use app\common\controller\Api;

/**
 * サンプルインターフェース
 */
class Demo extends Api
{

    //もし$noNeedLogin空の場合、すべてのインターフェースはログインが必要です
    //もし$noNeedRight空の場合、すべてのインターフェースは権限の検証が必要です
    //インターフェースがログイン不要に設定されている場合,認可も不要となります
    //
    // ログイン不要のインターフェース,*すべてを表示
    protected $noNeedLogin = ['test', 'test1'];
    // 認証不要のインターフェース,*すべてを表示
    protected $noNeedRight = ['test2'];

    /**
     * テストメソッド
     *
     * @ApiTitle    (テスト名)
     * @ApiSummary  (テストの説明情報)
     * @ApiMethod   (POST)
     * @ApiRoute    (/api/demo/test/id/{id}/name/{name})
     * @ApiHeaders  (name=token, type=string, required=true, description="リクエストのToken")
     * @ApiParams   (name="id", type="integer", required=true, description="会員ID")
     * @ApiParams   (name="name", type="string", required=true, description="ユーザー名")
     * @ApiParams   (name="data", type="object", sample="{'user_id':'int','user_name':'string','profile':{'email':'string','age':'integer'}}", description="拡張データ")
     * @ApiReturnParams   (name="code", type="integer", required=true, sample="0")
     * @ApiReturnParams   (name="msg", type="string", required=true, sample="返却成功")
     * @ApiReturnParams   (name="data", type="object", sample="{'user_id':'int','user_name':'string','profile':{'email':'string','age':'integer'}}", description="拡張データ返却")
     * @ApiReturn   ({
         'code':'1',
         'msg':'返却成功'
        })
     */
    public function test()
    {
        $this->success('返却成功', $this->request->param());
    }

    /**
     * ログイン不要のインターフェース
     *
     */
    public function test1()
    {
        $this->success('返却成功', ['action' => 'test1']);
    }

    /**
     * ログインが必要なインターフェース
     *
     */
    public function test2()
    {
        $this->success('返却成功', ['action' => 'test2']);
    }

    /**
     * ログインが必要かつ対応するグループの権限検証が必要
     *
     */
    public function test3()
    {
        $this->success('返却成功', ['action' => 'test3']);
    }

}

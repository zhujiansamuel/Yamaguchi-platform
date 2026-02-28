<?php

namespace app\api\controller;

use app\common\controller\Api;
use app\admin\model\Goods as GoodsModel;

/**
 * 商品价格管理API
 * 提供商品规格价格的查询和批量更新功能
 */
class Goodsprice extends Api
{
    // 所有接口都需要登录认证（需要提供token）
    // gettoken、listusers 和 createtestuser 方法不需要登录，用于获取测试token
    protected $noNeedLogin = ['gettoken', 'listusers', 'createtestuser', 'test'];
    protected $noNeedRight = '*';

    protected $model = null;

    public function _initialize()
    {
        parent::_initialize();
        $this->model = new GoodsModel();
    }

    /**
     * 获取商品价格列表（按规格展开）
     *
     * @ApiMethod (GET)
     * @ApiRoute  (/api/goodsprice/list)
     * @ApiHeaders (name=token, type=string, required=true, description="用户token")
     * @ApiParams (name="page", type="int", required=false, description="页码", default="1")
     * @ApiParams (name="limit", type="int", required=false, description="每页数量", default="50")
     * @ApiParams (name="title", type="string", required=false, description="商品标题（模糊搜索）")
     * @ApiParams (name="category_id", type="int", required=false, description="分类ID")
     * @ApiParams (name="status", type="int", required=false, description="状态：0=下架，1=上架")
     * @ApiParams (name="goods_id", type="int", required=false, description="商品ID（精确查询）")
     *
     * @ApiReturn ({
     *   "code": 1,
     *   "msg": "获取成功",
     *   "time": "1638000000",
     *   "data": {
     *     "total": 100,
     *     "per_page": 50,
     *     "current_page": 1,
     *     "last_page": 2,
     *     "data": [
     *       {
     *         "goods_id": 1,
     *         "title": "iPhone 13",
     *         "image": "/uploads/xxx.jpg",
     *         "category_name": "手机",
     *         "category_second_name": "智能手机",
     *         "category_three_name": "苹果手机",
     *         "status": 1,
     *         "spec_index": 0,
     *         "spec_name": "128GB 黑色",
     *         "price": 5999.00
     *       }
     *     ]
     *   }
     * })
     */
    public function list()
    {
        $page = $this->request->param('page/d', 1);
        $limit = $this->request->param('limit/d', 500);
        $title = $this->request->param('title', '');
        $categoryId = $this->request->param('category_id/d', 0);
        $status = $this->request->param('status', '');
        $goodsId = $this->request->param('goods_id/d', 0);

        // 构建查询 - 使用链式调用避免查询表达式错误
        $query = $this->model->with(['category', 'second', 'three']);

        if ($title) {
            $query = $query->where('title', 'like', '%' . $title . '%');
        }
        if ($categoryId > 0) {
            $query = $query->where('category_id', '=', $categoryId);
        }
        if ($status !== '') {
            $query = $query->where('status', '=', $status);
        }
        if ($goodsId > 0) {
            $query = $query->where('id', '=', $goodsId);
        }

        // 执行查询
        $list = $query->order('id', 'desc')->paginate($limit, false, ['page' => $page]);

        // 展开规格信息
        $expandedRows = [];
        foreach ($list->items() as $item) {
            $baseData = [
                'goods_id' => $item->id,
                'title' => $item->title,
                'image' => $item->image ? cdnurl($item->image, true) : '',
                'category_name' => isset($item->category) ? $item->category->name : '',
                'category_second_name' => isset($item->second) ? $item->second->name : '',
                'category_three_name' => isset($item->three) ? $item->three->name : '',
                'status' => $item->status,
                'status_text' => $item->status == 1 ? '上架' : '下架',
                'memo' => $item->memo ?? '',
            ];

            // 解析规格信息
            $specInfo = json_decode($item->spec_info, true);
            if (!empty($specInfo) && is_array($specInfo)) {
                foreach ($specInfo as $specIndex => $spec) {
                    $expandedRows[] = array_merge($baseData, [
                        'spec_index' => $specIndex,
                        'spec_name' => isset($spec['name']) ? $spec['name'] : '',
                        'price' => isset($spec['price']) ? floatval($spec['price']) : 0,
                    ]);
                }
            } else {
                // 如果没有规格信息，显示商品本身的价格
                $expandedRows[] = array_merge($baseData, [
                    'spec_index' => 0,
                    'spec_name' => '',
                    'price' => floatval($item->price),
                ]);
            }
        }

        $result = [
            'total' => $list->total(),
            'per_page' => $list->listRows(),
            'current_page' => $list->currentPage(),
            'last_page' => $list->lastPage(),
            'data' => $expandedRows,
        ];

        $this->success('获取成功', $result);
    }

    /**
     * 获取单个商品的价格信息
     *
     * @ApiMethod (GET)
     * @ApiRoute  (/api/goodsprice/detail)
     * @ApiHeaders (name=token, type=string, required=true, description="用户token")
     * @ApiParams (name="goods_id", type="int", required=true, description="商品ID")
     *
     * @ApiReturn ({
     *   "code": 1,
     *   "msg": "获取成功",
     *   "time": "1638000000",
     *   "data": {
     *     "goods_id": 1,
     *     "title": "iPhone 13",
     *     "image": "/uploads/xxx.jpg",
     *     "category_name": "手机",
     *     "category_second_name": "智能手机",
     *     "category_three_name": "苹果手机",
     *     "status": 1,
     *     "status_text": "上架",
     *     "specs": [
     *       {
     *         "spec_index": 0,
     *         "spec_name": "128GB 黑色",
     *         "price": 5999.00
     *       },
     *       {
     *         "spec_index": 1,
     *         "spec_name": "256GB 白色",
     *         "price": 6999.00
     *       }
     *     ]
     *   }
     * })
     */
    public function detail()
    {
        $goodsId = $this->request->param('goods_id/d', 0);

        if ($goodsId <= 0) {
            $this->error('商品ID不能为空');
        }

        $goods = $this->model->with(['category', 'second', 'three'])->find($goodsId);
        if (!$goods) {
            $this->error('商品不存在');
        }

        // 解析规格信息
        $specInfo = json_decode($goods->spec_info, true);
        $specs = [];
        if (!empty($specInfo) && is_array($specInfo)) {
            foreach ($specInfo as $specIndex => $spec) {
                $specs[] = [
                    'spec_index' => $specIndex,
                    'spec_name' => isset($spec['name']) ? $spec['name'] : '',
                    'price' => isset($spec['price']) ? floatval($spec['price']) : 0,
                ];
            }
        }

        $result = [
            'goods_id' => $goods->id,
            'title' => $goods->title,
            'image' => $goods->image ? cdnurl($goods->image, true) : '',
            'category_name' => isset($goods->category) ? $goods->category->name : '',
            'category_second_name' => isset($goods->second) ? $goods->second->name : '',
            'category_three_name' => isset($goods->three) ? $goods->three->name : '',
            'status' => $goods->status,
            'status_text' => $goods->status == 1 ? '上架' : '下架',
            'memo' => $goods->memo ?? '',
            'specs' => $specs,
        ];

        $this->success('获取成功', $result);
    }

    /**
     * 批量更新商品规格价格
     *
     * @ApiMethod (POST)
     * @ApiRoute  (/api/goodsprice/update)
     * @ApiHeaders (name=token, type=string, required=true, description="用户token")
     * @ApiParams (name="prices", type="array", required=true, description="价格数据数组", sample="[{goods_id:1,spec_index:0,price:5999}]")
     *
     * @ApiReturnParams (name="code", type="integer", description="状态码")
     * @ApiReturnParams (name="msg", type="string", description="返回消息")
     * @ApiReturnParams (name="data", type="object", description="返回数据")
     *
     * @ApiReturn ({
     *   "code": 1,
     *   "msg": "成功更新了3个商品",
     *   "time": "1638000000",
     *   "data": {
     *     "updated_count": 3,
     *     "updated_goods": [1, 2, 3]
     *   }
     * })
     */
    public function update()
    {
        $prices = $this->request->param('prices/a', []);

        if (empty($prices) || !is_array($prices)) {
            $this->error('价格数据不能为空');
        }

        // 按商品ID分组价格数据和备注
        $goodsPrices = [];
        $goodsMemos = [];
        foreach ($prices as $item) {
            if (!isset($item['goods_id']) || !isset($item['spec_index']) || !isset($item['price'])) {
                continue;
            }

            $goodsId = intval($item['goods_id']);
            $specIndex = intval($item['spec_index']);
            $price = floatval($item['price']);
            $memo = isset($item['memo']) ? $item['memo'] : null;

            if (!isset($goodsPrices[$goodsId])) {
                $goodsPrices[$goodsId] = [];
            }
            $goodsPrices[$goodsId][$specIndex] = $price;

            // 记录备注（同一个商品只记录一次，以最后一个为准）
            if ($memo !== null) {
                $goodsMemos[$goodsId] = $memo;
            }
        }

        if (empty($goodsPrices)) {
            $this->error('没有有效的价格数据');
        }

        $count = 0;
        $updatedGoods = [];
        $this->model->startTrans();
        try {
            foreach ($goodsPrices as $goodsId => $specs) {
                // 获取商品当前的spec_info
                $goods = $this->model->find($goodsId);
                if (!$goods) {
                    throw new \Exception("商品ID {$goodsId} 不存在");
                }

                // 获取spec_info，可能是字符串或已经是数组（如果模型有获取器）
                $specInfoRaw = $goods->getData('spec_info'); // 获取原始数据，不经过获取器
                if (is_string($specInfoRaw)) {
                    $specInfo = json_decode($specInfoRaw, true);
                } else if (is_array($specInfoRaw)) {
                    $specInfo = $specInfoRaw;
                } else {
                    $specInfo = [];
                }

                if (empty($specInfo)) {
                    $specInfo = [];
                }

                // 更新规格价格
                foreach ($specs as $specIndex => $price) {
                    if (!isset($specInfo[$specIndex])) {
                        $specInfo[$specIndex] = ['name' => '', 'price' => 0];
                    }
                    $specInfo[$specIndex]['price'] = $price;
                }

                // 计算最高价格作为商品的参考价格
                $priceList = array_column($specInfo, 'price');
                $maxPrice = $priceList ? max($priceList) : 0;

                // 更新商品 - 使用数据库直接更新避免模型问题
                $updateData = [
                    'spec_info' => json_encode($specInfo, JSON_UNESCAPED_UNICODE),
                    'price' => $maxPrice,
                ];

                // 如果提供了memo，也更新它
                if (isset($goodsMemos[$goodsId])) {
                    $updateData['memo'] = $goodsMemos[$goodsId];
                }

                $result = $this->model->where('id', $goodsId)->update($updateData);
                if ($result === false) {
                    throw new \Exception("保存商品ID {$goodsId} 失败，数据库更新返回false");
                }

                $count++;
                $updatedGoods[] = $goodsId;
            }

            // 提交事务
            $this->model->commit();
        } catch (\Throwable $e) {
            $this->model->rollback();
            $errorMsg = $e->getMessage() ?: '未知错误';
            $errorDetail = [
                'type' => get_class($e),
                'message' => $errorMsg,
                'file' => $e->getFile(),
                'line' => $e->getLine(),
                'trace' => explode("\n", $e->getTraceAsString()),
            ];
            // 记录详细错误到日志
            \think\Log::error('商品价格更新失败: ' . json_encode($errorDetail, JSON_UNESCAPED_UNICODE));
            // 如果是开发环境，返回详细错误
            if (config('app_debug')) {
                $this->error('更新失败：' . $errorMsg . ' [' . basename($e->getFile()) . ':' . $e->getLine() . ']');
            } else {
                $this->error('更新失败：' . $errorMsg);
            }
        }

        // 事务提交成功后返回结果
        $this->success('成功更新了' . $count . '个商品', [
            'updated_count' => $count,
            'updated_goods' => $updatedGoods,
        ]);
    }

    /**
     * 批量设置价格（简化版）
     * 可以一次性设置一个商品的所有规格价格
     *
     * @ApiMethod (POST)
     * @ApiRoute  (/api/goodsprice/setprices)
     * @ApiHeaders (name=token, type=string, required=true, description="用户token")
     * @ApiParams (name="goods_id", type="int", required=true, description="商品ID")
     * @ApiParams (name="prices", type="array", required=true, description="规格价格数组", sample="[5999, 6999, 7999]")
     *
     * @ApiReturn ({
     *   "code": 1,
     *   "msg": "价格更新成功",
     *   "time": "1638000000",
     *   "data": {
     *     "goods_id": 1,
     *     "updated_specs": 3
     *   }
     * })
     */
    public function setprices()
    {
        $goodsId = $this->request->param('goods_id/d', 0);
        $prices = $this->request->param('prices/a', []);
        $memo = $this->request->param('memo', null);

        if ($goodsId <= 0) {
            $this->error('商品ID不能为空');
        }

        if (empty($prices) || !is_array($prices)) {
            $this->error('价格数据不能为空');
        }

        $goods = $this->model->find($goodsId);
        if (!$goods) {
            $this->error('商品不存在');
        }

        // 获取spec_info，可能是字符串或已经是数组（如果模型有获取器）
        $specInfoRaw = $goods->getData('spec_info'); // 获取原始数据，不经过获取器
        if (is_string($specInfoRaw)) {
            $specInfo = json_decode($specInfoRaw, true);
        } else if (is_array($specInfoRaw)) {
            $specInfo = $specInfoRaw;
        } else {
            $specInfo = [];
        }

        if (empty($specInfo)) {
            $this->error('商品没有规格信息');
        }

        $this->model->startTrans();
        try {
            // 更新规格价格
            $updatedCount = 0;
            foreach ($prices as $index => $price) {
                if (isset($specInfo[$index])) {
                    $specInfo[$index]['price'] = floatval($price);
                    $updatedCount++;
                }
            }

            // 计算最高价格作为商品的参考价格
            $allPrices = array_column($specInfo, 'price');
            $maxPrice = $allPrices ? max($allPrices) : 0;

            // 更新商品 - 使用数据库直接更新避免模型问题
            $updateData = [
                'spec_info' => json_encode($specInfo, JSON_UNESCAPED_UNICODE),
                'price' => $maxPrice,
            ];

            // 如果提供了memo，也更新它
            if ($memo !== null) {
                $updateData['memo'] = $memo;
            }

            $result = $this->model->where('id', $goodsId)->update($updateData);
            if ($result === false) {
                throw new \Exception("保存商品ID {$goodsId} 失败，数据库更新返回false");
            }

            // 提交事务
            $this->model->commit();
        } catch (\Throwable $e) {
            $this->model->rollback();
            $errorMsg = $e->getMessage() ?: '未知错误';
            $errorDetail = [
                'type' => get_class($e),
                'message' => $errorMsg,
                'file' => $e->getFile(),
                'line' => $e->getLine(),
                'trace' => explode("\n", $e->getTraceAsString()),
            ];
            // 记录详细错误到日志
            \think\Log::error('商品价格更新失败: ' . json_encode($errorDetail, JSON_UNESCAPED_UNICODE));
            // 如果是开发环境，返回详细错误
            if (config('app_debug')) {
                $this->error('更新失败：' . $errorMsg . ' [' . basename($e->getFile()) . ':' . $e->getLine() . ']');
            } else {
                $this->error('更新失败：' . $errorMsg);
            }
        }

        // 事务提交成功后返回结果
        $this->success('价格更新成功', [
            'goods_id' => $goodsId,
            'updated_specs' => $updatedCount,
        ]);
    }

    /**
     * 获取测试Token（仅用于开发测试）
     *
     * @ApiMethod (GET)
     * @ApiRoute  (/api/goodsprice/gettoken)
     * @ApiParams (name="user_id", type="int", required=false, description="用户ID，默认为1")
     *
     * @ApiReturn ({
     *   "code": 1,
     *   "msg": "Token获取成功",
     *   "time": "1638000000",
     *   "data": {
     *     "token": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
     *     "user_id": 1,
     *     "expire_time": "2592000秒 (30天)"
     *   }
     * })
     */
    public function gettoken()
    {
        $userId = $this->request->param('user_id/d', 1);

        // 检查用户是否存在
        $user = \app\common\model\User::get($userId);
        if (!$user) {
            $this->error('用户不存在，请提供有效的 user_id。请先访问 /api/goodsprice/listusers 查看可用的用户ID');
        }

        // 生成Token（开发环境不检查用户状态）
        $token = \fast\Random::uuid();
        \app\common\library\Token::set($token, $userId, 2592000); // 30天有效期

        $this->success('Token获取成功', [
            'token' => $token,
            'user_id' => $userId,
            'username' => $user->username,
            'user_status' => $user->status,
            'expire_time' => '2592000秒 (30天)',
            'usage' => '请在API请求时通过 HTTP Header "token: ' . $token . '" 或 URL参数 "?token=' . $token . '" 传递此token'
        ]);
    }

    /**
     * 列出所有可用用户（仅用于开发测试）
     *
     * @ApiMethod (GET)
     * @ApiRoute  (/api/goodsprice/listusers)
     *
     * @ApiReturn ({
     *   "code": 1,
     *   "msg": "获取成功",
     *   "time": "1638000000",
     *   "data": {
     *     "users": [
     *       {
     *         "id": 1,
     *         "username": "admin",
     *         "email": "admin@example.com",
     *         "status": "normal"
     *       }
     *     ]
     *   }
     * })
     */
    public function listusers()
    {
        // 查询 fa_user 表中的用户
        $users = \app\common\model\User::limit(10)->select();
        $userCount = \app\common\model\User::count();

        // 查询 fa_admin 表中的管理员
        $admins = \app\admin\model\Admin::limit(10)->select();
        $adminCount = \app\admin\model\Admin::count();

        // 处理查询结果（兼容数组和集合）
        $userList = $users;
        if (is_object($users) && method_exists($users, 'toArray')) {
            $userList = $users->toArray();
        }

        $adminList = $admins;
        if (is_object($admins) && method_exists($admins, 'toArray')) {
            $adminList = $admins->toArray();
        }

        $this->success('获取成功', [
            'fa_user' => [
                'count' => $userCount,
                'list' => $userList ?: [],
                'tip' => '这些是前台用户，可用于生成token'
            ],
            'fa_admin' => [
                'count' => $adminCount,
                'list' => $adminList ?: [],
                'tip' => '这些是后台管理员，但API认证系统只支持fa_user表的用户'
            ],
            'usage' => '请使用 fa_user 中的任意用户 id 访问 /api/goodsprice/gettoken?user_id=X 来获取token',
            'note' => '如果 fa_user 为空，可以访问 /api/goodsprice/createtestuser 创建测试用户'
        ]);
    }

    /**
     * 创建测试用户（仅用于开发测试）
     *
     * @ApiMethod (POST)
     * @ApiRoute  (/api/goodsprice/createtestuser)
     * @ApiParams (name="username", type="string", required=false, description="用户名，默认为testuser")
     * @ApiParams (name="password", type="string", required=false, description="密码，默认为123456")
     * @ApiParams (name="email", type="string", required=false, description="邮箱，默认为test@test.com")
     *
     * @ApiReturn ({
     *   "code": 1,
     *   "msg": "测试用户创建成功",
     *   "time": "1638000000",
     *   "data": {
     *     "user_id": 1,
     *     "username": "testuser",
     *     "email": "test@test.com"
     *   }
     * })
     */
    public function createtestuser()
    {
        $username = $this->request->param('username', 'testuser_' . time());
        $password = $this->request->param('password', '123456');
        $email = $this->request->param('email', 'test_' . time() . '@test.com');

        // 检查用户名是否已存在
        $existUser = \app\common\model\User::where('username', $username)->find();
        if ($existUser) {
            $this->error('用户名已存在，请使用其他用户名或不传username参数（将自动生成）');
        }

        // 检查邮箱是否已存在
        $existEmail = \app\common\model\User::where('email', $email)->find();
        if ($existEmail) {
            $this->error('邮箱已存在，请使用其他邮箱或不传email参数（将自动生成）');
        }

        try {
            $salt = \fast\Random::alnum();
            $encryptPassword = md5(md5($password) . $salt);

            $userData = [
                'username' => $username,
                'nickname' => $username,
                'password' => $encryptPassword,
                'email' => $email,
                'mobile' => '',
                'salt' => $salt,
                'avatar' => '',
                'level' => 1,
                'score' => 0,
                'successions' => 1,
                'maxsuccessions' => 1,
                'logintime' => time(),
                'loginip' => request()->ip(),
                'jointime' => time(),
                'joinip' => request()->ip(),
                'prevtime' => time(),
                'status' => 'normal'
            ];

            $user = \app\common\model\User::create($userData);

            $this->success('测试用户创建成功', [
                'user_id' => $user->id,
                'username' => $user->username,
                'email' => $user->email,
                'password' => $password,
                'next_step' => '请访问 /api/goodsprice/gettoken?user_id=' . $user->id . ' 获取token'
            ]);
        } catch (\Exception $e) {
            $this->error('创建失败：' . $e->getMessage());
        }
    }

    /**
     * 简单测试接口（用于排查问题）
     */
    public function test()
    {
        $this->success('GoodsPrice API is working', [
            'time' => date('Y-m-d H:i:s'),
            'controller' => 'GoodsPrice',
            'method' => 'test'
        ]);
    }
}

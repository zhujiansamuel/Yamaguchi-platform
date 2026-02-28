# 商品价格管理 API 文档

## 概述

商品价格管理API提供了查询和修改商品规格价格的功能。所有接口都需要token认证。

**Base URL**: `http://your-domain.com/api`

**认证方式**: Bearer Token (在请求头中传递)

---

## 认证说明

### 获取Token

首先需要通过用户登录接口获取token，然后在后续请求的Header中携带token。

**请求头格式**:
```
token: your-access-token-here
```

或者使用标准的Bearer Token格式：
```
Authorization: Bearer your-access-token-here
```

### Token有效期

Token默认有效期为30天（2592000秒），可以通过 `/api/token/check` 检查token状态，通过 `/api/token/refresh` 刷新token。

---

## API接口列表

### 1. 获取商品价格列表

获取所有商品的规格价格信息，每个规格展开为单独的一条记录。

**接口地址**: `GET /api/goodsprice/list`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| page | int | 否 | 页码，默认1 | 1 |
| limit | int | 否 | 每页数量，默认50 | 50 |
| title | string | 否 | 商品标题（模糊搜索） | iPhone |
| category_id | int | 否 | 分类ID | 1 |
| status | int | 否 | 状态：0=下架，1=上架 | 1 |
| goods_id | int | 否 | 商品ID（精确查询） | 123 |

**请求示例**:
```bash
curl -X GET "http://your-domain.com/api/goodsprice/list?page=1&limit=20&title=iPhone" \
  -H "token: your-token-here"
```

**响应示例**:
```json
{
  "code": 1,
  "msg": "获取成功",
  "time": "1701234567",
  "data": {
    "total": 100,
    "per_page": 20,
    "current_page": 1,
    "last_page": 5,
    "data": [
      {
        "goods_id": 1,
        "title": "iPhone 13",
        "image": "http://domain.com/uploads/xxx.jpg",
        "category_name": "手机",
        "status": 1,
        "status_text": "上架",
        "spec_index": 0,
        "spec_name": "128GB 黑色",
        "price": 5999.00
      },
      {
        "goods_id": 1,
        "title": "iPhone 13",
        "image": "http://domain.com/uploads/xxx.jpg",
        "category_name": "手机",
        "status": 1,
        "status_text": "上架",
        "spec_index": 1,
        "spec_name": "256GB 白色",
        "price": 6999.00
      }
    ]
  }
}
```

---

### 2. 获取单个商品价格详情

获取指定商品的所有规格价格信息。

**接口地址**: `GET /api/goodsprice/detail`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| goods_id | int | 是 | 商品ID | 1 |

**请求示例**:
```bash
curl -X GET "http://your-domain.com/api/goodsprice/detail?goods_id=1" \
  -H "token: your-token-here"
```

**响应示例**:
```json
{
  "code": 1,
  "msg": "获取成功",
  "time": "1701234567",
  "data": {
    "goods_id": 1,
    "title": "iPhone 13",
    "image": "http://domain.com/uploads/xxx.jpg",
    "category_name": "手机",
    "status": 1,
    "status_text": "上架",
    "specs": [
      {
        "spec_index": 0,
        "spec_name": "128GB 黑色",
        "price": 5999.00
      },
      {
        "spec_index": 1,
        "spec_name": "256GB 白色",
        "price": 6999.00
      },
      {
        "spec_index": 2,
        "spec_name": "512GB 金色",
        "price": 7999.00
      }
    ]
  }
}
```

---

### 3. 批量更新商品规格价格

批量更新多个商品的多个规格价格。

**接口地址**: `POST /api/goodsprice/update`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| prices | array | 是 | 价格数据数组 |

**prices数组元素结构**:

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| goods_id | int | 是 | 商品ID |
| spec_index | int | 是 | 规格索引（从0开始） |
| price | float | 是 | 新价格 |

**请求示例**:
```bash
curl -X POST "http://your-domain.com/api/goodsprice/update" \
  -H "token: your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "prices": [
      {
        "goods_id": 1,
        "spec_index": 0,
        "price": 5899.00
      },
      {
        "goods_id": 1,
        "spec_index": 1,
        "price": 6899.00
      },
      {
        "goods_id": 2,
        "spec_index": 0,
        "price": 3999.00
      }
    ]
  }'
```

**响应示例**:
```json
{
  "code": 1,
  "msg": "成功更新了2个商品",
  "time": "1701234567",
  "data": {
    "updated_count": 2,
    "updated_goods": [1, 2]
  }
}
```

---

### 4. 设置商品所有规格价格（简化版）

一次性设置一个商品的所有规格价格，按规格顺序传递价格数组。

**接口地址**: `POST /api/goodsprice/setprices`

**请求参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| goods_id | int | 是 | 商品ID |
| prices | array | 是 | 价格数组，按规格索引顺序 |

**请求示例**:
```bash
curl -X POST "http://your-domain.com/api/goodsprice/setprices" \
  -H "token: your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "goods_id": 1,
    "prices": [5899, 6899, 7899]
  }'
```

**响应示例**:
```json
{
  "code": 1,
  "msg": "价格更新成功",
  "time": "1701234567",
  "data": {
    "goods_id": 1,
    "updated_specs": 3
  }
}
```

---

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 0 | 请求失败 |
| 1 | 请求成功 |
| -1 | 未登录或token失效 |
| -2 | 参数错误 |

**错误响应示例**:
```json
{
  "code": 0,
  "msg": "商品不存在",
  "time": "1701234567",
  "data": null
}
```

---

## 使用场景示例

### 场景1：查询并更新单个商品价格

```javascript
// 1. 获取商品价格详情
const response1 = await fetch('http://domain.com/api/goodsprice/detail?goods_id=1', {
  headers: {
    'token': 'your-token-here'
  }
});
const data1 = await response1.json();
console.log('当前价格:', data1.data.specs);

// 2. 更新价格（所有规格统一降价100）
const newPrices = data1.data.specs.map(spec => spec.price - 100);
const response2 = await fetch('http://domain.com/api/goodsprice/setprices', {
  method: 'POST',
  headers: {
    'token': 'your-token-here',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    goods_id: 1,
    prices: newPrices
  })
});
const data2 = await response2.json();
console.log('更新结果:', data2);
```

### 场景2：批量更新多个商品价格

```javascript
// 批量更新多个商品的指定规格价格
const response = await fetch('http://domain.com/api/goodsprice/update', {
  method: 'POST',
  headers: {
    'token': 'your-token-here',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    prices: [
      { goods_id: 1, spec_index: 0, price: 5899 },
      { goods_id: 1, spec_index: 1, price: 6899 },
      { goods_id: 2, spec_index: 0, price: 3999 },
      { goods_id: 3, spec_index: 0, price: 2999 }
    ]
  })
});
const data = await response.json();
console.log('批量更新结果:', data);
```

### 场景3：查询特定分类商品并批量调价

```python
import requests

# API配置
BASE_URL = 'http://domain.com/api'
TOKEN = 'your-token-here'
HEADERS = {'token': TOKEN}

# 1. 获取指定分类的商品价格列表
response = requests.get(
    f'{BASE_URL}/goodsprice/list',
    params={'category_id': 1, 'limit': 100},
    headers=HEADERS
)
goods_list = response.json()['data']['data']

# 2. 构建批量更新数据（所有商品价格上涨5%）
update_data = []
for item in goods_list:
    new_price = round(item['price'] * 1.05, 2)
    update_data.append({
        'goods_id': item['goods_id'],
        'spec_index': item['spec_index'],
        'price': new_price
    })

# 3. 批量更新价格
response = requests.post(
    f'{BASE_URL}/goodsprice/update',
    json={'prices': update_data},
    headers=HEADERS
)
print('更新结果:', response.json())
```

---

## 注意事项

1. **Token安全**: 请妥善保管您的token，不要在客户端代码中明文硬编码。

2. **价格更新逻辑**:
   - 更新规格价格时，系统会自动计算所有规格中的最高价作为商品的参考价格
   - 价格会自动转换为浮点数类型

3. **并发更新**: 批量更新使用数据库事务，确保数据一致性。如果部分更新失败，整个批次会回滚。

4. **分页查询**: 列表接口支持分页，建议每页不超过200条记录。

5. **规格索引**: spec_index从0开始，对应商品spec_info JSON数组的索引位置。

6. **数据格式**: 所有价格字段都是浮点数，建议保留2位小数。

7. **筛选条件**: list接口的筛选条件可以组合使用。

8. **错误处理**: 建议在客户端实现重试机制，处理网络异常情况。

---

## PHP示例代码

```php
<?php
// API配置
$baseUrl = 'http://your-domain.com/api';
$token = 'your-token-here';

// 获取商品价格列表
function getGoodsPriceList($token, $page = 1) {
    global $baseUrl;

    $url = $baseUrl . '/goodsprice/list?page=' . $page . '&limit=50';

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'token: ' . $token
    ]);

    $response = curl_exec($ch);
    curl_close($ch);

    return json_decode($response, true);
}

// 批量更新价格
function updateGoodsPrices($token, $prices) {
    global $baseUrl;

    $url = $baseUrl . '/goodsprice/update';
    $data = json_encode(['prices' => $prices]);

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'token: ' . $token,
        'Content-Type: application/json'
    ]);

    $response = curl_exec($ch);
    curl_close($ch);

    return json_decode($response, true);
}

// 使用示例
$list = getGoodsPriceList($token, 1);
print_r($list);

$updateResult = updateGoodsPrices($token, [
    ['goods_id' => 1, 'spec_index' => 0, 'price' => 5899],
    ['goods_id' => 1, 'spec_index' => 1, 'price' => 6899]
]);
print_r($updateResult);
?>
```

---

## 技术支持

如有问题，请联系技术支持团队。

# Data Aggregation API 总览

## 概述

本文档提供 Data Aggregation App 所有模型的 API 状态总览，包括已实现的 API 端点和缺失的 API。

**Base URL**: `/api/aggregation/`

---

## 已实现的 API（13个模型）

### 1. 产品模型 (2)

| 模型 | 端点 | 文档 | 说明 |
|------|------|------|------|
| iPhone | `/iphones/` | [API_IPHONE.md](./API_IPHONE.md) | iPhone 产品管理 |
| iPad | `/ipads/` | [API_IPAD.md](./API_IPAD.md) | iPad 产品管理 |

### 2. 库存管理 (1)

| 模型 | 端点 | 文档 | 说明 |
|------|------|------|------|
| Inventory | `/inventory/` | [API_INVENTORY.md](./API_INVENTORY.md) | 库存管理（核心枢纽） |

### 3. 采购来源渠道 (3)

| 模型 | 端点 | 文档 | 说明 |
|------|------|------|------|
| EcSite | `/ec-sites/` | [API_EC_SITE.md](./API_EC_SITE.md) | 电商网站订单 (source1) |
| LegalPersonOffline | `/legal-person-offline/` | [API_LEGAL_PERSON_OFFLINE.md](./API_LEGAL_PERSON_OFFLINE.md) | 法人线下采购 (source3) |
| TemporaryChannel | `/temporary-channels/` | [API_TEMPORARY_CHANNEL.md](./API_TEMPORARY_CHANNEL.md) | 临时渠道 (source4) |

### 4. 账号与采购 (2)

| 模型 | 端点 | 文档 | 说明 |
|------|------|------|------|
| OfficialAccount | `/official-accounts/` | [API_OFFICIAL_ACCOUNT.md](./API_OFFICIAL_ACCOUNT.md) | 官方账号管理 |
| Purchasing | `/purchasing/` | [API_PURCHASING.md](./API_PURCHASING.md) | 采购订单管理 (source2) |

### 5. 支付方式 (5)

| 模型 | 端点 | 文档 | 说明 |
|------|------|------|------|
| GiftCard | `/giftcards/` | [API_GIFT_CARD.md](./API_GIFT_CARD.md) | 礼品卡管理 |
| DebitCard | `/debitcards/` | [API_DEBIT_CARD.md](./API_DEBIT_CARD.md) | 借记卡管理 |
| DebitCardPayment | `/debitcard-payments/` | [API_DEBIT_CARD_PAYMENT.md](./API_DEBIT_CARD_PAYMENT.md) | 借记卡支付记录 |
| CreditCard | `/creditcards/` | [API_CREDIT_CARD.md](./API_CREDIT_CARD.md) | 信用卡管理 |
| CreditCardPayment | `/creditcard-payments/` | [API_CREDIT_CARD_PAYMENT.md](./API_CREDIT_CARD_PAYMENT.md) | 信用卡支付记录 |

---

## 缺失的 API（3个模型）

以下模型存在于 models.py 中，但**尚未实现** Serializer、ViewSet 和 URL 路由：

### 数据聚合基础模型

| 模型 | 用途 | 建议优先级 |
|------|------|-----------|
| AggregationSource | 聚合数据源管理 | 中 |
| AggregatedData | 聚合后的数据存储 | 中 |
| AggregationTask | 聚合任务执行跟踪 | 低 |

**说明**：
- 这些模型是数据聚合框架的基础组件
- 目前系统主要关注业务模型（产品、库存、采购、支付）
- 如需实现完整的数据聚合功能，应优先实现这些 API

---

## 抽象模型（不需要 API）

| 模型 | 说明 |
|------|------|
| ElectronicProduct | 抽象基类，iPhone 和 iPad 的父类，不直接使用 |

---

## API 端点完整列表

### 完整的 URL 映射

```
/api/aggregation/
├── iphones/                      # iPhone API
├── ipads/                        # iPad API
├── inventory/                    # Inventory API
├── ec-sites/                     # EcSite API
├── legal-person-offline/         # LegalPersonOffline API
├── temporary-channels/           # TemporaryChannel API
├── official-accounts/            # OfficialAccount API
├── purchasing/                   # Purchasing API
├── giftcards/                    # GiftCard API
├── debitcards/                   # DebitCard API
├── debitcard-payments/           # DebitCardPayment API
├── creditcards/                  # CreditCard API
├── creditcard-payments/          # CreditCardPayment API
└── export-to-excel/              # Excel 导出 API (导出到 Nextcloud)
```

---

## API 调用示例

### 基础操作模式

所有 API 遵循 RESTful 规范，支持标准的 CRUD 操作：

```http
# List - 获取列表
GET /api/aggregation/{endpoint}/

# Create - 创建
POST /api/aggregation/{endpoint}/

# Retrieve - 获取详情
GET /api/aggregation/{endpoint}/{id}/

# Update - 完整更新
PUT /api/aggregation/{endpoint}/{id}/

# Partial Update - 部分更新
PATCH /api/aggregation/{endpoint}/{id}/

# Delete - 删除
DELETE /api/aggregation/{endpoint}/{id}/
```

### 通用查询参数

所有 API 支持以下通用查询参数：

```http
# 过滤
?field_name=value

# 搜索
?search=keyword

# 排序
?ordering=field_name          # 升序
?ordering=-field_name         # 降序

# 分页
?page=1
?page_size=20
```

---

## 模型依赖关系图

### 核心业务流程

```
OfficialAccount (官方账号)
    ↓
Purchasing (采购订单) ←→ 支付方式
    ↓                    ├─ GiftCard (礼品卡)
Inventory (库存)        ├─ DebitCard (借记卡) ←→ DebitCardPayment
    ↓                    └─ CreditCard (信用卡) ←→ CreditCardPayment
iPhone / iPad (产品)

采购来源：
├─ source1 → EcSite (电商网站)
├─ source2 → Purchasing (采购订单)
├─ source3 → LegalPersonOffline (法人线下)
└─ source4 → TemporaryChannel (临时渠道)
```

---

## 数据流向

### 典型业务场景

```
1. 创建采购订单
   OfficialAccount → Purchasing → Payment (GiftCard/DebitCard/CreditCard)

2. 库存入库
   Purchasing → Inventory → Product (iPhone/iPad)

3. 支付处理
   DebitCard/CreditCard → DebitCardPayment/CreditCardPayment → Purchasing
```

---

## API 统计

| 类别 | 已实现 | 缺失 | 抽象 | 总计 |
|------|--------|------|------|------|
| 产品模型 | 2 | 0 | 1 | 3 |
| 库存管理 | 1 | 0 | 0 | 1 |
| 采购来源 | 3 | 0 | 0 | 3 |
| 账号采购 | 2 | 0 | 0 | 2 |
| 支付方式 | 5 | 0 | 0 | 5 |
| 数据聚合 | 0 | 3 | 0 | 3 |
| **总计** | **13** | **3** | **1** | **17** |

**API 实现率**: 13/16 = **81.25%** (排除抽象模型)

---

## 实现建议

### 对于缺失的 API

如需实现 `AggregationSource`、`AggregatedData`、`AggregationTask` 的 API：

1. **创建 Serializer** (`serializers.py`)
   ```python
   class AggregationSourceSerializer(serializers.ModelSerializer):
       class Meta:
           model = AggregationSource
           fields = '__all__'
   ```

2. **创建 ViewSet** (`views.py`)
   ```python
   class AggregationSourceViewSet(viewsets.ModelViewSet):
       queryset = AggregationSource.objects.all()
       serializer_class = AggregationSourceSerializer
   ```

3. **注册路由** (`urls.py`)
   ```python
   router.register(r'aggregation-sources', AggregationSourceViewSet)
   ```

4. **创建 API 文档**
   - 参考现有文档格式创建对应的 API 文档

---

## 技术规范

### 统一标准

所有 API 遵循以下技术规范：

1. **认证**: `BATCH_STATS_API_TOKEN` (Bearer Token)
2. **内容类型**: `application/json`
3. **字符编码**: UTF-8
4. **日期时间格式**: ISO 8601 (UTC)
5. **分页**: DRF PageNumberPagination
6. **过滤**: django-filter
7. **搜索**: DRF SearchFilter
8. **排序**: DRF OrderingFilter

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 (GET, PUT, PATCH) |
| 201 | 创建成功 (POST) |
| 204 | 删除成功 (DELETE) |
| 400 | 请求错误（验证失败） |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

---

## 相关文档

### 架构文档
- [系统架构](../ARCHITECTURE.md)
- [电子产品架构](./ELECTRONIC_PRODUCTS_ARCHITECTURE.md)

### API 详细文档

**产品**
- [iPhone API](./API_IPHONE.md)
- [iPad API](./API_IPAD.md)

**库存**
- [Inventory API](./API_INVENTORY.md)

**采购来源**
- [EcSite API](./API_EC_SITE.md)
- [Legal Person Offline API](./API_LEGAL_PERSON_OFFLINE.md)
- [Temporary Channel API](./API_TEMPORARY_CHANNEL.md)

**账号采购**
- [Official Account API](./API_OFFICIAL_ACCOUNT.md)
- [Purchasing API](./API_PURCHASING.md)

**支付方式**
- [Gift Card API](./API_GIFT_CARD.md)
- [Debit Card API](./API_DEBIT_CARD.md)
- [Debit Card Payment API](./API_DEBIT_CARD_PAYMENT.md)
- [Credit Card API](./API_CREDIT_CARD.md)
- [Credit Card Payment API](./API_CREDIT_CARD_PAYMENT.md)

**数据导出**
- [Export to Excel API](./API_EXPORT_TO_EXCEL.md)

---

## 更新日志

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-01-04 | 1.2 | 统一所有 API 使用 BATCH_STATS_API_TOKEN 认证 |
| 2026-01-03 | 1.1 | 添加 Export to Excel API 文档 |
| 2025-01-01 | 1.0 | 初始版本，包含 13 个已实现的 API |
| - | - | 缺失 3 个数据聚合相关 API |

---

## 联系方式

如有 API 相关问题，请查阅相应的详细文档或联系开发团队。

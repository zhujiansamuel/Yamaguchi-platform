# 模拟数据生成工具

## 📋 概述

这个工具用于为 `data_aggregation` app 的所有模型生成随机测试数据。

## 🚀 快速开始

### 在 Docker 环境中运行

```bash
# 生成默认数量（10条）的测试数据
./generate_mock_data.sh --docker

# 生成 50 条记录
./generate_mock_data.sh --docker --count 50

# 清除现有数据并生成新数据
./generate_mock_data.sh --docker --clear --count 30
```

### 在本地环境中运行

```bash
# 生成默认数量的测试数据
./generate_mock_data.sh

# 生成 100 条记录
./generate_mock_data.sh --count 100

# 清除现有数据并生成新数据
./generate_mock_data.sh --clear --count 50
```

## 📖 使用说明

### 命令行选项

| 选项 | 说明 | 示例 |
|-----|-----|------|
| `-c, --count NUM` | 每个模型创建的记录数（默认：10） | `--count 20` |
| `--clear` | 在生成新数据前清除现有数据 | `--clear` |
| `--docker` | 在 Docker 容器中运行 | `--docker` |
| `-h, --help` | 显示帮助信息 | `--help` |

### 示例

```bash
# 生成 20 条记录
./generate_mock_data.sh --docker --count 20

# 清空数据库并生成 50 条新记录
./generate_mock_data.sh --docker --clear --count 50

# 生成 100 条记录（本地环境）
./generate_mock_data.sh --count 100
```

## 📊 生成的数据模型

脚本会为以下模型生成测试数据：

### 核心模型
1. **AggregationSource** - 聚合数据源
2. **AggregatedData** - 聚合数据结果
3. **AggregationTask** - 聚合任务

### 产品模型
4. **iPhone** - iPhone 产品信息
5. **iPad** - iPad 产品信息

### 来源/渠道模型
6. **TemporaryChannel** - 临时渠道
7. **LegalPersonOffline** - 线下法人客户
8. **EcSite** - 电商平台订单

### 账户和订单模型
9. **OfficialAccount** - 官方账号
10. **Purchasing** - 采购订单

### 支付方式模型
11. **GiftCard** - 礼品卡
12. **DebitCard** - 借记卡
13. **CreditCard** - 信用卡
14. **DebitCardPayment** - 借记卡支付记录
15. **CreditCardPayment** - 信用卡支付记录

### 库存模型
16. **Inventory** - 库存管理

## 🎲 生成数据的特点

### iPhone 数据
- 型号：iPhone 15 Pro Max, iPhone 15 Pro, iPhone 15, iPhone 14 Pro, iPhone 14, iPhone 13
- 颜色：Natural Titanium, Blue Titanium, White Titanium, Black Titanium, Purple, Blue, Midnight, Starlight
- 容量：128GB, 256GB, 512GB, 1024GB
- 随机生成的 Part Number 和 JAN 码

### iPad 数据
- 型号：iPad Pro 12.9", iPad Pro 11", iPad Air, iPad mini, iPad
- 颜色：Space Gray, Silver, Starlight, Pink, Blue
- 容量：64GB, 128GB, 256GB, 512GB, 1024GB, 2048GB
- 随机生成的 Part Number 和 JAN 码

### 订单数据
- 订单状态：pending_confirmation, shipped, in_delivery, delivered
- 支付方式：credit_card, gift_card, card, backup
- 随机生成的订单号和追踪号
- 符合逻辑的时间序列（创建 → 确认 → 发货 → 送达）

### 库存数据
- 状态：in_transit, arrived, out_of_stock, abnormal
- 自动关联随机的产品（iPhone 或 iPad）
- 自动关联随机的来源（EcSite, Purchasing, LegalPersonOffline, TemporaryChannel）
- 符合逻辑的时间序列（预计到达 → 实际到达）

### 支付数据
- 真实的卡号格式（借记卡：4xxx, 信用卡：5xxx）
- 有效期验证（2025-2030）
- 支付状态：pending, completed, failed, refunded
- 自动关联订单和卡片

## ⚠️ 注意事项

1. **清除数据警告**：使用 `--clear` 选项会删除所有现有数据，操作前会要求确认
2. **依赖关系**：脚本会按照正确的顺序创建数据，确保外键关系的完整性
3. **数据量**：Inventory 会生成 `count * 2` 条记录（因为通常需要更多库存数据）
4. **唯一性约束**：所有需要唯一的字段（如订单号、卡号等）都会生成随机值以避免冲突

## 🔧 直接使用 Django Management Command

你也可以直接使用 Django management command：

```bash
# Docker 环境
docker compose exec django python manage.py generate_test_data --count 20

# Docker 环境 - 清除并生成
docker compose exec django python manage.py generate_test_data --clear --count 50

# 本地环境
python manage.py generate_test_data --count 20

# 查看帮助
python manage.py generate_test_data --help
```

## 📈 验证生成的数据

### 通过 Django Admin
访问 https://data.yamaguchi.lan/admin/ 查看生成的数据

### 通过 API
访问 https://data.yamaguchi.lan/api/ 浏览所有 API 端点

### 通过 Django Shell
```bash
# Docker 环境
docker compose exec django python manage.py shell

# 本地环境
python manage.py shell
```

```python
from apps.data_aggregation.models import *

# 查看记录数
print(f"iPhones: {iPhone.objects.count()}")
print(f"iPads: {iPad.objects.count()}")
print(f"Inventory: {Inventory.objects.count()}")
print(f"Purchasing: {Purchasing.objects.count()}")

# 查看最新的 5 个库存记录
for inv in Inventory.objects.all()[:5]:
    print(f"{inv.uuid[:8]}... - {inv.product} - {inv.get_status_display()}")

# 查看最新的 5 个订单
for order in Purchasing.objects.all()[:5]:
    print(f"{order.order_number} - {order.get_delivery_status_display()}")
```

## 🐛 故障排查

### 问题：脚本没有执行权限
```bash
chmod +x generate_mock_data.sh
```

### 问题：Docker 容器未运行
```bash
docker compose ps
docker compose up -d
```

### 问题：数据库迁移未完成
```bash
docker compose exec django python manage.py migrate
```

### 问题：唯一性约束冲突
如果多次运行脚本而不清除数据，可能会遇到唯一性约束冲突。使用 `--clear` 选项：
```bash
./generate_mock_data.sh --docker --clear --count 20
```

## 📝 开发说明

### 修改生成的数据

编辑 `apps/data_aggregation/management/commands/generate_test_data.py` 文件来自定义生成的数据。

### 添加新模型

如果添加了新的模型，需要在 `generate_test_data.py` 中：
1. 导入新模型
2. 创建生成方法 `generate_<model_name>(self, count)`
3. 在 `handle()` 方法中调用生成方法
4. 在 `clear_all_data()` 方法中添加模型（注意顺序）

## 🎯 最佳实践

1. **开发环境**：使用较少的数据量（10-20 条）进行快速测试
2. **性能测试**：使用较大的数据量（100-1000 条）测试系统性能
3. **定期清理**：定期使用 `--clear` 选项清理测试数据
4. **备份数据**：在生产环境使用前，确保备份重要数据

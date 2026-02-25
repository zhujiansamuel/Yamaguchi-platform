# Purchasing 模型实例创建方法汇总

| 方法/入口 | 说明 | 关键位置 |
| --- | --- | --- |
| `Purchasing.create_with_inventory(**kwargs)` | 模型类方法，内部使用 `Purchasing.objects.create(**purchasing_data)` 创建实例，并可联动创建库存与支付卡信息。属于代码层的“标准创建入口”。 | 定义：`apps/data_aggregation/models.py` 中 `create_with_inventory` 方法，包含创建逻辑。 |
| 数据采集任务（任务编排） | 在订单规划任务中调用 `Purchasing.create_with_inventory(**order_kwargs)` 批量创建采购订单。 | `apps/data_acquisition/tasks.py` 中订单规划逻辑调用该方法。 |
| 数据采集 Tracker（日本邮政/官网转运） | 当订单不存在时，在两个 Tracker 中调用 `Purchasing.create_with_inventory(...)` 创建新实例。 | `redirect_to_japan_post_tracking.py`、`official_website_redirect_to_yamato_tracking.py` 中调用。 |
| 管理命令测试数据 | `generate_test_data` 命令中使用 `Purchasing.objects.create(...)` 直接创建实例（用于生成测试数据）。 | `apps/data_aggregation/management/commands/generate_test_data.py` 直接调用创建。 |
| API 创建入口（DRF ViewSet） | `PurchasingViewSet` 使用 `PurchasingSerializer`，默认的 ModelSerializer `create` 会走 `Purchasing.objects.create`，因此 API POST 也是实例创建入口。 | `apps/data_aggregation/views.py` 中使用 `PurchasingSerializer` 作为创建入口。 |

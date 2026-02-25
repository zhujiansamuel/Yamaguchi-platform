# OnlyOffice Excel 导入

本文档记录 OnlyOffice 回调触发的 Excel 导入逻辑调整与导出约定。

## 文件命名与模型匹配

OnlyOffice 导入会根据文件名解析模型名称，规则与 `export-to-excel` API 导出一致：

- `{ModelName}_test.xlsx`
- `{ModelName}_test_{timestamp}.xlsx`

解析出的 `ModelName` 仅在下列模型范围内才会触发导入：

- iPhone / iPad
- Inventory
- EcSite
- LegalPersonOffline
- TemporaryChannel
- OfficialAccount
- Purchasing
- GiftCard / GiftCardPayment
- DebitCard / DebitCardPayment
- CreditCard / CreditCardPayment

## 导出约定

- 外键字段同时导出字符串表示与 `*_id` 列。
- 仅导出 `is_deleted=False` 的记录。

## 导入约定

- 首行必须为字段名（与导出一致）。
- 以 `id` 作为唯一基准：
  - Excel 有但数据库无 → 新增
  - Excel 有且字段变化 → 更新
  - 数据库有但 Excel 无 → 软删除（`is_deleted=True`）
- 外键字段优先使用 `*_id` 列进行解析。
- 单行失败会跳过该行，继续处理剩余行。
- 变更来源记录为 `onlyoffice_import`。

## 软删除字段

上述支持导入的模型均新增了 `is_deleted` 字段，用于软删除。

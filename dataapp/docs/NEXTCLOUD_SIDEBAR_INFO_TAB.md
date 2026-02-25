# Nextcloud 文件侧边栏 Info Tab 说明

本说明介绍 `onlyoffice_callback_interceptor` 插件新增的文件侧边栏 Info Tab，用于在 `/data_platform/` 目录下的 Excel 文件中显示可编辑的说明字段占位符。

## 功能说明

* 在 Nextcloud Files 右侧栏注册一个名为 **Info** 的 Tab。
* 仅在 `/data_platform/` 目录下，且文件名满足导出规则的 Excel 文件显示。
* 说明输入框默认占位符为当前文件名，便于手动填写说明。

## 文件名判断规则

Info Tab 仅在满足以下条件时显示：

1. 目录为 `/data_platform/`
2. 文件扩展名为 `.xlsx`
3. 文件名符合导出 API 规则：`{ModelName}_test_{YYYYMMDD_HHMMSS}.xlsx`

该规则与导出 API（`apps/data_aggregation/views.py` 中的 `export_models_to_excel`）保持一致，文件名生成逻辑由 `upload_excel_files` 负责：

* `apps/data_aggregation/views.py` → `export_models_to_excel`
* `apps/data_aggregation/utils.py` → `upload_excel_files`

## 说明文字修改位置

说明字段的占位符与辅助提示文字在以下文件中修改：

* `nextcloud_apps/onlyoffice_callback_interceptor/js/sidebar-info.js`
    * `descriptionField.placeholder`：占位符（当前为文件名）
    * `helperText.textContent`：辅助提示文字（当前为“在此处填写文件说明。”）

如需自定义默认说明文本或提示文案，请在上述位置更新。

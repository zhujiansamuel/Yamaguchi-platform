# Excel Exporters 架构

## 概述

此目录包含 data_aggregation 应用中所有模型的 Excel 导出器。每个模型都有一个独立的导出器文件，允许对 Excel 导出进行精细控制。

## 架构设计

### 基础类

`base.py` 包含 `BaseExcelExporter` 基类，提供以下功能：

- 获取模型类
- 获取查询集
- 获取要导出的字段
- 自定义表头名称
- 格式化单元格值
- 自定义工作簿样式
- 执行导出

### 模型导出器

每个模型都有一个独立的导出器文件：

1. **iphone_exporter.py** - iPhone 模型导出器
2. **ipad_exporter.py** - iPad 模型导出器
3. **inventory_exporter.py** - Inventory 模型导出器
4. **purchasing_exporter.py** - Purchasing 模型导出器
5. **official_account_exporter.py** - OfficialAccount 模型导出器
6. **temporary_channel_exporter.py** - TemporaryChannel 模型导出器
7. **legal_person_offline_exporter.py** - LegalPersonOffline 模型导出器
8. **ec_site_exporter.py** - EcSite 模型导出器
9. **gift_card_exporter.py** - GiftCard 模型导出器
10. **debit_card_exporter.py** - DebitCard 模型导出器
11. **debit_card_payment_exporter.py** - DebitCardPayment 模型导出器
12. **credit_card_exporter.py** - CreditCard 模型导出器
13. **credit_card_payment_exporter.py** - CreditCardPayment 模型导出器
14. **aggregation_source_exporter.py** - AggregationSource 模型导出器
15. **aggregated_data_exporter.py** - AggregatedData 模型导出器
16. **aggregation_task_exporter.py** - AggregationTask 模型导出器

## 使用方法

### 基本用法

```python
from apps.data_aggregation.excel_exporters import get_exporter

# 获取特定模型的导出器
exporter = get_exporter('iPhone')

# 执行导出
excel_file = exporter.export()
```

### 自定义导出

每个导出器都可以通过以下方法进行自定义：

#### 1. 自定义查询集

```python
class iPhoneExporter(BaseExcelExporter):
    def get_queryset(self):
        model = self.get_model()
        # 自定义查询集，例如：过滤、排序等
        return model.objects.filter(release_date__year=2025).order_by('-release_date')
```

#### 2. 自定义表头名称

```python
class iPhoneExporter(BaseExcelExporter):
    def get_header_names(self):
        return {
            'id': 'ID',
            'part_number': '部件编号',
            'model_name': '型号名称',
            'capacity_gb': '容量 (GB)',
            # ...
        }
```

#### 3. 自定义字段列表

```python
class iPhoneExporter(BaseExcelExporter):
    def get_fields(self):
        # 只导出特定字段
        return ['id', 'part_number', 'model_name', 'color']
```

#### 4. 自定义单元格格式化

```python
class iPhoneExporter(BaseExcelExporter):
    def format_cell_value(self, obj, field_name):
        if field_name == 'capacity_gb':
            # 添加单位
            value = getattr(obj, field_name, None)
            return f"{value} GB" if value else ''
        return super().format_cell_value(obj, field_name)
```

#### 5. 自定义工作簿样式

```python
from openpyxl.styles import PatternFill

class iPhoneExporter(BaseExcelExporter):
    def customize_workbook(self, wb, ws):
        # 调用父类方法
        super().customize_workbook(wb, ws)

        # 添加自定义样式
        # 例如：给表头添加背景色
        for cell in ws[1]:
            cell.fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
```

## 导出器注册表

所有导出器都在 `__init__.py` 中的 `EXPORTER_REGISTRY` 字典中注册：

```python
EXPORTER_REGISTRY = {
    'iPhone': iPhoneExporter,
    'iPad': iPadExporter,
    # ... 其他模型
}
```

## API 集成

Excel 导出 API (`/api/aggregation/export-to-excel/`) 已更新为使用新的导出器架构。API 使用方法保持不变：

### GET 请求

列出所有可用的模型：

```bash
GET /api/aggregation/export-to-excel/
```

### POST 请求

导出指定模型：

```bash
POST /api/aggregation/export-to-excel/
Content-Type: application/json

{
    "models": ["iPhone", "iPad", "Inventory"]
}
```

## 下一步工作

现在所有16个模型的导出器都已创建，您可以根据每个模型的具体需求进行详细修改：

1. **自定义表头名称** - 将英文字段名改为中文或其他语言
2. **调整列顺序** - 通过 `get_fields()` 方法重新排列列
3. **添加计算字段** - 添加不在模型中但需要在 Excel 中显示的字段
4. **应用样式** - 为不同类型的数据添加不同的颜色、字体等
5. **添加数据验证** - 为某些列添加下拉列表或数据验证规则
6. **合并单元格** - 为相关数据合并单元格
7. **添加图表** - 在 Excel 文件中添加图表
8. **多工作表** - 为复杂的模型创建多个工作表

## 示例：完整自定义

```python
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from .base import BaseExcelExporter

class iPhoneExporter(BaseExcelExporter):
    model_name = 'iPhone'

    def get_queryset(self):
        model = self.get_model()
        return model.objects.filter(
            release_date__year__gte=2023
        ).order_by('-release_date', 'model_name')

    def get_fields(self):
        # 自定义字段顺序
        return [
            'part_number',
            'model_name',
            'capacity_gb',
            'color',
            'release_date',
            'jan',
        ]

    def get_header_names(self):
        return {
            'part_number': '部件编号',
            'model_name': '型号名称',
            'capacity_gb': '容量',
            'color': '颜色',
            'release_date': '发布日期',
            'jan': 'JAN 代码',
        }

    def format_cell_value(self, obj, field_name):
        if field_name == 'capacity_gb':
            value = getattr(obj, field_name, None)
            return f"{value}GB" if value else ''
        elif field_name == 'release_date':
            value = getattr(obj, field_name, None)
            return value.strftime('%Y年%m月%d日') if value else ''
        return super().format_cell_value(obj, field_name)

    def customize_workbook(self, wb, ws):
        # 设置列宽
        column_widths = {
            'A': 15,  # part_number
            'B': 25,  # model_name
            'C': 10,  # capacity_gb
            'D': 15,  # color
            'E': 15,  # release_date
            'F': 15,  # jan
        }

        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width

        # 表头样式
        header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
        header_font = Font(bold=True, color='FFFFFF', size=12)

        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')

        # 添加边框
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=len(self.get_fields())):
            for cell in row:
                cell.border = thin_border
```

## 注意事项

1. **性能考虑** - 对于大数据集，考虑使用 `queryset.iterator()` 或分批处理
2. **内存管理** - Excel 文件保存在内存中（BytesIO），对于非常大的数据集可能需要优化
3. **错误处理** - 建议在自定义方法中添加适当的错误处理
4. **测试** - 修改导出器后，务必测试导出功能是否正常工作

## 支持

如有问题或需要帮助，请参考：
- Django 文档：https://docs.djangoproject.com/
- openpyxl 文档：https://openpyxl.readthedocs.io/

# 电子商品模型架构文档

## 概述

为了减少代码重复并提高可维护性，我们采用了面向对象的继承设计模式，创建了一个抽象基类 `ElectronicProduct`（电子商品），所有具体的电子产品模型都继承自这个基类。

## 架构设计

### 类继承关系

```
ElectronicProduct (抽象基类)
    ├── iPhone
    ├── iPad
    ├── AppleWatch (未来)
    └── AirPods (未来)
```

## ElectronicProduct 抽象基类

### 设计目的

1. **代码复用**: 将所有电子产品的共同属性集中管理
2. **一致性**: 确保所有产品具有统一的基础字段
3. **可扩展性**: 方便添加新的产品类别
4. **维护性**: 修改共同属性只需在一处更新

### 共同字段

| 字段 | 类型 | 必填 | 唯一 | 说明 |
|------|------|------|------|------|
| `part_number` | CharField(50) | ✓ | ✓ | 产品型号 |
| `model_name` | CharField(100) | ✓ | - | 产品名称 |
| `capacity_gb` | IntegerField | - | - | 存储容量（GB）* |
| `color` | CharField(50) | ✓ | - | 颜色 |
| `release_date` | DateField | ✓ | - | 发布日期 |
| `jan` | CharField(13) | ✓ | ✓ | JAN码 |
| `created_at` | DateTimeField | 自动 | - | 创建时间 |
| `updated_at` | DateTimeField | 自动 | - | 更新时间 |

\* `capacity_gb` 在基类中为可选字段，以支持没有存储容量概念的产品（如 AirPods）。具体产品类可以根据需要覆盖此字段。

### Meta 配置

- `abstract = True`: 声明为抽象模型，不会创建数据库表
- `ordering = ['-release_date', 'model_name']`: 默认排序规则

### __str__ 方法

```python
def __str__(self):
    if self.capacity_gb:
        return f"{self.model_name} {self.capacity_gb}GB {self.color}"
    return f"{self.model_name} {self.color}"
```

智能显示：有容量时显示容量，无容量时省略。

---

## 具体产品模型

### 1. iPhone

**继承**: `ElectronicProduct`

**特殊配置**:
- 数据库表名: `iphones`
- 覆盖 `capacity_gb` 为必填字段

**索引**:
- `model_name`
- `release_date`
- `jan`
- `part_number`

**API端点**: `/api/aggregation/iphones/`

---

### 2. iPad

**继承**: `ElectronicProduct`

**特殊配置**:
- 数据库表名: `ipads`
- 覆盖 `capacity_gb` 为必填字段

**索引**:
- `model_name`
- `release_date`
- `jan`
- `part_number`

**API端点**: `/api/aggregation/ipads/`

---

### 3. Apple Watch (规划中)

**继承**: `ElectronicProduct`

**预期特殊字段**:
- `case_size_mm`: 表壳尺寸（毫米）
- `band_type`: 表带类型
- `gps_cellular`: GPS/蜂窝网络版本

**数据库表名**: `apple_watches`

**API端点**: `/api/aggregation/apple-watches/` (规划中)

---

### 4. AirPods (规划中)

**继承**: `ElectronicProduct`

**预期特殊配置**:
- `capacity_gb` 保持可选（AirPods 无存储容量）

**预期特殊字段**:
- `noise_cancellation`: 降噪功能
- `charging_case_type`: 充电盒类型

**数据库表名**: `airpods`

**API端点**: `/api/aggregation/airpods/` (规划中)

---

## 优势

### 1. 代码复用

**重构前**:
```python
class iPhone(models.Model):
    part_number = models.CharField(...)
    model_name = models.CharField(...)
    capacity_gb = models.IntegerField(...)
    color = models.CharField(...)
    release_date = models.DateField(...)
    jan = models.CharField(...)
    created_at = models.DateTimeField(...)
    updated_at = models.DateTimeField(...)

class iPad(models.Model):
    part_number = models.CharField(...)  # 重复
    model_name = models.CharField(...)   # 重复
    capacity_gb = models.IntegerField(...) # 重复
    # ... 所有字段都重复
```

**重构后**:
```python
class ElectronicProduct(models.Model):
    # 共同字段定义一次
    part_number = models.CharField(...)
    model_name = models.CharField(...)
    # ...
    class Meta:
        abstract = True

class iPhone(ElectronicProduct):
    # 只需要覆盖特殊字段
    capacity_gb = models.IntegerField(...)  # 设为必填

class iPad(ElectronicProduct):
    # 只需要覆盖特殊字段
    capacity_gb = models.IntegerField(...)  # 设为必填
```

### 2. 易于维护

如果需要为所有产品添加新字段（如 `discontinued_date`），只需在 `ElectronicProduct` 中添加一次。

### 3. 一致性保证

所有产品自动拥有相同的基础字段，确保数据结构一致。

### 4. 灵活性

- 子类可以覆盖父类字段以满足特殊需求
- 子类可以添加专属字段
- 保持各自独立的数据库表

---

## 数据库结构

### 抽象基类不创建表

`ElectronicProduct` 是抽象模型（`abstract = True`），不会在数据库中创建表。

### 子类独立表

每个具体产品类都有自己的数据库表：

- `iphones` 表（包含所有继承的字段）
- `ipads` 表（包含所有继承的字段）
- 未来：`apple_watches` 表
- 未来：`airpods` 表

### 表结构示例 (iphones)

```sql
CREATE TABLE iphones (
    id SERIAL PRIMARY KEY,
    part_number VARCHAR(50) UNIQUE NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    capacity_gb INTEGER NOT NULL,  -- 被子类覆盖为必填
    color VARCHAR(50) NOT NULL,
    release_date DATE NOT NULL,
    jan VARCHAR(13) UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- 索引
CREATE INDEX ON iphones(model_name);
CREATE INDEX ON iphones(release_date);
CREATE INDEX ON iphones(jan);
CREATE INDEX ON iphones(part_number);
```

---

## 序列化器和API

### 序列化器无需修改

由于继承是在模型层面，序列化器仍然直接引用具体的模型类，字段通过继承自动可用。

**iPhone Serializer**:
```python
class iPhoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = iPhone  # 自动包含继承的所有字段
        fields = ['id', 'part_number', 'model_name', ...]
```

### API端点保持不变

- `/api/aggregation/iphones/` - iPhone API
- `/api/aggregation/ipads/` - iPad API

---

## 添加新产品类别的步骤

### 1. 创建模型类

```python
class AppleWatch(ElectronicProduct):
    """Apple Watch 产品模型"""
    # 可选：覆盖容量字段（如果需要）
    # capacity_gb = None  # Apple Watch 可能不需要容量

    # 添加专属字段
    case_size_mm = models.IntegerField(
        verbose_name='Case Size (mm)',
        help_text='Watch case size in millimeters'
    )

    class Meta:
        db_table = 'apple_watches'
        verbose_name = 'Apple Watch'
        verbose_name_plural = 'Apple Watches'
        ordering = ['-release_date', 'model_name']
```

### 2. 创建序列化器

```python
class AppleWatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppleWatch
        fields = '__all__'
```

### 3. 创建视图

```python
class AppleWatchViewSet(viewsets.ModelViewSet):
    queryset = AppleWatch.objects.all()
    serializer_class = AppleWatchSerializer
```

### 4. 注册路由

```python
router.register(r'apple-watches', AppleWatchViewSet, basename='apple-watch')
```

### 5. 注册到 Admin

```python
@admin.register(AppleWatch)
class AppleWatchAdmin(admin.ModelAdmin):
    list_display = ['part_number', 'model_name', 'case_size_mm', 'color']
```

### 6. 生成迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 注意事项

### 1. 字段覆盖

子类可以覆盖父类字段以改变其属性：

```python
class iPhone(ElectronicProduct):
    # 将可选字段改为必填
    capacity_gb = models.IntegerField(
        verbose_name='Capacity (GB)',
        help_text='Storage capacity in GB'
    )
```

### 2. 迁移管理

- 修改抽象基类会影响所有子类
- Django 会为每个受影响的子类生成迁移
- 确保在修改基类后测试所有子类

### 3. 唯一性约束

`part_number` 和 `jan` 在每个子类表中独立唯一，不是跨表唯一：
- iPhone 和 iPad 可以有相同的 part_number（虽然实际不会）
- 唯一性在每个产品类别内部保证

---

## 测试

### 验证继承关系

```python
# Python shell
from apps.data_aggregation.models import iPhone, iPad, ElectronicProduct

# 检查继承
assert issubclass(iPhone, ElectronicProduct)
assert issubclass(iPad, ElectronicProduct)

# 检查字段
iphone = iPhone.objects.first()
assert hasattr(iphone, 'part_number')
assert hasattr(iphone, 'model_name')
assert hasattr(iphone, 'capacity_gb')
```

---

## 总结

通过使用抽象基类模式，我们实现了：

✅ **代码复用**: 共同字段定义一次
✅ **易于维护**: 集中管理共同属性
✅ **灵活扩展**: 轻松添加新产品类别
✅ **类型安全**: 每个产品有独立的模型类
✅ **数据隔离**: 每个产品有独立的数据库表
✅ **性能优化**: 独立的索引和查询优化

这种设计为平台的长期发展和维护奠定了良好的基础。

# 迁移修复指南 (Migration Fix Guide)

## 问题描述

Django 容器不断重启，因为迁移历史不一致：
```
InconsistentMigrationHistory: Migration data_acquisition.0003_alter_historicalsynclog_operation_type_and_more
is applied before its dependency data_acquisition.0002_historicalsynclog on database 'default'.
```

## 原因

数据库的 `django_migrations` 表中已经记录了 `0003` 迁移，但我们新创建的 `0002` 迁移还未被标记为已应用。

## 解决方案

### 方案 1：自动修复脚本（推荐）

运行自动修复脚本，它会：
1. 停止所有容器
2. 只启动 postgres 和 redis
3. 直接在数据库中插入缺失的 0002 迁移记录
4. 重新启动所有容器
5. 应用剩余迁移

```bash
bash fix_migrations_docker.sh
```

### 方案 2：手动修复（更可控）

#### 步骤 1：停止所有容器

```bash
docker compose down
```

#### 步骤 2：只启动 postgres

```bash
docker compose up -d postgres redis
```

等待 postgres 就绪：
```bash
# 检查 postgres 是否就绪
docker compose exec postgres pg_isready -U postgres
```

#### 步骤 3：直接在数据库中修复迁移记录

**选项 A - 使用 SQL 文件：**
```bash
docker compose exec -T postgres psql -U postgres -d data_platform < fix_migrations.sql
```

**选项 B - 直接执行 SQL：**
```bash
docker compose exec postgres psql -U postgres -d data_platform -c "
INSERT INTO django_migrations (app, name, applied)
VALUES ('data_acquisition', '0002_historicalsynclog', NOW())
ON CONFLICT DO NOTHING;
"
```

**选项 C - 进入 psql 交互模式：**
```bash
docker compose exec postgres psql -U postgres -d data_platform
```

然后执行：
```sql
-- 查看当前 data_acquisition 迁移
SELECT app, name, applied FROM django_migrations WHERE app = 'data_acquisition' ORDER BY applied;

-- 插入缺失的 0002 迁移
INSERT INTO django_migrations (app, name, applied)
VALUES ('data_acquisition', '0002_historicalsynclog', NOW())
ON CONFLICT DO NOTHING;

-- 验证修复
SELECT app, name, applied FROM django_migrations WHERE app = 'data_acquisition' ORDER BY applied;

-- 退出
\q
```

#### 步骤 4：启动所有容器

```bash
docker compose up -d
```

#### 步骤 5：等待 Django 启动

```bash
# 查看 Django 日志，确认启动成功
docker compose logs -f django
```

如果看到 "Booting worker with pid" 或类似信息，说明启动成功。按 Ctrl+C 退出日志查看。

#### 步骤 6：应用剩余迁移

```bash
docker compose exec django python manage.py migrate
```

#### 步骤 7：验证迁移状态

```bash
docker compose exec django python manage.py showmigrations data_acquisition data_aggregation
```

应该看到所有迁移前面都有 `[X]` 标记。

## 验证修复成功

```bash
# 1. 检查容器状态（所有容器应该是 healthy 或 running）
docker compose ps

# 2. 检查 Django 日志（应该没有错误）
docker compose logs django | tail -50

# 3. 检查 Celery worker 日志
docker compose logs celery_worker_acquisition | tail -20

# 4. 测试 API（如果配置了）
curl http://localhost:8000/api/schema/
```

## 预期的迁移顺序

修复后，`data_acquisition` 应该有以下迁移：

```
[X] 0001_initial
[X] 0002_historicalsynclog
[X] 0003_alter_historicalsynclog_operation_type_and_more
[X] 0004_trackingbatch_trackingjob
```

`data_aggregation` 应该有以下迁移：

```
[X] 0001_initial
...
[X] 0006_historicalaggregateddata_historicalaggregationsource_and_more
[X] 0007_add_latest_delivery_status_to_purchasing
[X] 0007_alter_creditcard_alternative_name_and_more
[X] 0008_merge_20260109
```

## 如果仍然失败

如果容器仍然无法启动，查看详细日志：

```bash
# 查看 Django 完整日志
docker compose logs django

# 查看 postgres 日志
docker compose logs postgres

# 强制重新创建容器
docker compose down -v  # 注意：-v 会删除数据卷！谨慎使用
docker compose up -d
```

## 相关文件

- `fix_migrations_docker.sh` - 自动修复脚本
- `fix_migrations.sql` - SQL 修复脚本
- `fix_migrations.sh` - 容器内修复脚本（需要容器运行）

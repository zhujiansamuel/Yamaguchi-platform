# ELK Stack for YamagotiProjects

这是一个配置好的 ELK Stack，用于收集和管理 YamagotiProjects Docker 容器的日志。

## 组件

- **Elasticsearch**: 日志存储和搜索引擎 (端口 9200, 9300)
- **Kibana**: 日志可视化界面 (端口 5601)
- **Logstash**: 日志处理管道 (端口 5044)
- **Filebeat**: 日志收集器

## 已实现的优化

### ✅ 1. 容器名称标签

每条日志都包含 `container_name` 字段，方便按容器过滤日志。

**更新容器映射**：
```bash
cd /home/samuelzhu/ELK
./logstash/update-container-mapping.sh
docker compose restart logstash
```

建议：添加到 crontab，每小时自动更新：
```bash
0 * * * * /home/samuelzhu/ELK/logstash/update-container-mapping.sh && docker compose -f /home/samuelzhu/ELK/docker-compose.yml restart logstash >/dev/null 2>&1
```

### ✅ 2. 日志解析规则

自动解析以下类型的日志：

- **Django/Daphne HTTP 日志**：提取 IP、端口、HTTP 方法、路径、状态码、响应大小
- **Celery Worker 日志**：提取任务 ID、日志级别、时间戳
- **JSON 格式日志**：自动解析 JSON 内容

解析后的字段可在 Kibana 中进行高级过滤和聚合。

### ✅ 3. 日志保留策略

**自动策略**：
- 新索引自动应用 ILM 策略
- 日志保留 30 天后自动删除
- 每日自动轮转索引

**手动清理**：
```bash
cd /home/samuelzhu/ELK
./cleanup-old-logs.sh
```

建议：添加到 crontab，每天自动清理：
```bash
0 2 * * * /home/samuelzhu/ELK/cleanup-old-logs.sh >/dev/null 2>&1
```

## 使用方法

### 启动 ELK Stack

```bash
cd /home/samuelzhu/ELK
docker compose up -d
```

### 停止 ELK Stack

```bash
cd /home/samuelzhu/ELK
docker compose down
```

### 查看服务状态

```bash
docker compose ps
```

### 查看日志

**Filebeat 日志**：
```bash
docker logs filebeat
```

**Logstash 日志**：
```bash
docker logs logstash
```

**Elasticsearch 日志**：
```bash
docker logs elasticsearch
```

## 访问 Kibana

打开浏览器访问：http://localhost:5601

### 首次配置

1. 进入 Kibana
2. 点击左侧菜单 -> Management -> Stack Management
3. 选择 "Index Patterns" (或 "Data Views")
4. 点击 "Create index pattern"
5. 输入索引模式：`docker-logs-*`
6. 选择时间字段：`@timestamp`
7. 点击 "Create index pattern"

### 查看日志

1. 点击左侧菜单 -> Analytics -> Discover
2. 选择 `docker-logs-*` 索引模式
3. 使用 KQL (Kibana Query Language) 进行搜索

**常用查询示例**：

- 查看特定容器的日志：
  ```
  container_name: "ypa_web"
  ```

- 查看 HTTP 错误（5xx）：
  ```
  http_status >= 500
  ```

- 查看 Celery 错误日志：
  ```
  log_level: "ERROR" AND container_name: ypa_worker_*
  ```

- 查看特定 IP 的请求：
  ```
  client_ip: "172.22.0.1"
  ```

## API 查询示例

### 搜索最近的日志

```bash
curl -X POST "http://localhost:9200/docker-logs-*/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "size": 10,
  "query": {
    "match_all": {}
  },
  "sort": [
    {
      "@timestamp": {
        "order": "desc"
      }
    }
  ]
}'
```

### 按容器名称过滤

```bash
curl -X POST "http://localhost:9200/docker-logs-*/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "term": {
      "container_name.keyword": "ypa_web"
    }
  }
}'
```

### 查看索引列表

```bash
curl "http://localhost:9200/_cat/indices/docker-logs-*?v"
```

### 查看索引大小统计

```bash
curl "http://localhost:9200/_cat/indices/docker-logs-*?v&h=index,docs.count,store.size&s=index:desc"
```

## 维护

### 监控磁盘使用

```bash
# 查看 Elasticsearch 数据卷大小
docker volume inspect elk_elasticsearch_data

# 查看索引统计
curl "http://localhost:9200/_cat/indices?v&h=index,docs.count,store.size&s=store.size:desc"
```

### 手动删除索引

```bash
# 删除特定日期的索引
curl -X DELETE "http://localhost:9200/docker-logs-2026.01.01"

# 删除所有旧索引（谨慎使用！）
curl -X DELETE "http://localhost:9200/docker-logs-2026.01.*"
```

### 重建索引

```bash
# 停止服务
docker compose down

# 删除数据卷（会删除所有日志！）
docker volume rm elk_elasticsearch_data

# 重新启动
docker compose up -d
```

## 故障排查

### Filebeat 未收集日志

```bash
# 检查 Filebeat 状态
docker logs filebeat

# 确认配置文件权限
ls -l /home/samuelzhu/ELK/filebeat/filebeat.yml

# 重启 Filebeat
docker compose restart filebeat
```

### Logstash 启动失败

```bash
# 查看错误日志
docker logs logstash

# 验证配置文件语法
docker exec logstash /usr/share/logstash/bin/logstash --config.test_and_exit -f /usr/share/logstash/pipeline/logstash.conf

# 重启 Logstash
docker compose restart logstash
```

### Elasticsearch 内存不足

编辑 `docker-compose.yml`，调整 ES_JAVA_OPTS：

```yaml
environment:
  - "ES_JAVA_OPTS=-Xms1g -Xmx1g"  # 增加到 1GB
```

### Kibana 无法连接

```bash
# 检查 Elasticsearch 健康状态
curl "http://localhost:9200/_cluster/health?pretty"

# 重启 Kibana
docker compose restart kibana
```

## 配置文件

- `filebeat/filebeat.yml`: Filebeat 配置
- `logstash/pipeline/logstash.conf`: Logstash 管道配置
- `logstash/data/container-mapping.yml`: 容器 ID 到名称的映射
- `docker-compose.yml`: Docker Compose 配置

## 性能优化建议

1. **调整刷新间隔**：对于不需要实时搜索的场景，增加索引刷新间隔
2. **禁用副本**：单节点部署时禁用副本（已默认设置）
3. **定期清理**：设置 cron 任务定期清理旧日志
4. **监控资源**：定期检查磁盘和内存使用情况

## 安全建议

⚠️ **注意**：当前配置禁用了 Elasticsearch 安全功能，仅适用于开发环境。

生产环境请启用以下安全功能：
- Elasticsearch 身份验证
- HTTPS/TLS 加密
- 网络隔离
- 访问控制

## 支持的日志格式

1. **标准输出/错误**：所有容器的 stdout/stderr
2. **Django 日志**：自动解析 HTTP 请求
3. **Celery 日志**：自动解析任务信息
4. **JSON 日志**：自动解析 JSON 格式
5. **纯文本日志**：原样存储

## 更多资源

- [Elasticsearch 文档](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Kibana 文档](https://www.elastic.co/guide/en/kibana/current/index.html)
- [Logstash 文档](https://www.elastic.co/guide/en/logstash/current/index.html)
- [Filebeat 文档](https://www.elastic.co/guide/en/beats/filebeat/current/index.html)

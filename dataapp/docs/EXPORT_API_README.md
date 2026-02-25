# Data Export API 使用文档

## 概述

这个API用于将 `data_aggregation` app中的模型数据导出为Excel文件，并上传到Nextcloud。

## 功能特性

- ✅ 导出所有或指定的模型数据到Excel文件
- ✅ 自动上传到Nextcloud WebDAV存储
- ✅ JWT Token认证保护
- ✅ 支持选择性导出特定模型
- ✅ 文件名包含时间戳，避免覆盖

## 安装依赖

确保已安装所需依赖：

```bash
pip install -r requirements.txt
```

新增的依赖包括：
- `PyJWT==2.8.0` - JWT token认证
- `requests==2.31.0` - HTTP请求（用于Nextcloud上传）
- `openpyxl==3.1.2` - Excel文件生成
- `python-decouple==3.8` - 环境变量管理

## 配置

在 `config/settings/base.py` 中已配置：

```python
# Nextcloud Configuration for Data Export
NEXTCLOUD_CONFIG = {
    'webdav_hostname': 'http://nextcloud-app/remote.php/dav/files/username/',
    'webdav_login': 'Data-Platform',
    'webdav_password': 'DACZ7-8aYLi-SAJck-Q3tTR-Aie5B',
}

# Excel Output Path
EXCEL_OUTPUT_PATH = 'data_platform/'
```

## 生成访问Token

使用Django管理命令生成JWT token：

```bash
python manage.py generate_export_token
```

可选参数：
```bash
python manage.py generate_export_token --expires-in 60  # Token有效期60天
```

命令会输出类似以下内容：
```
================================================================================
JWT Token Generated Successfully
================================================================================

Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Expires in: 30 days
Expiration date: 2025-01-30 12:00:00 UTC

Usage example:
curl -X POST http://localhost:8000/api/aggregation/export-to-excel/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"models": ["iPhone", "iPad"]}'

================================================================================
```

## API端点

### 基础URL

```
/api/aggregation/export-to-excel/
```

### 1. 获取可用模型列表

**请求方法:** GET

**请求示例:**
```bash
curl -X GET http://localhost:8000/api/aggregation/export-to-excel/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**响应示例:**
```json
{
    "status": "success",
    "available_models": [
        "AggregationSource",
        "AggregatedData",
        "AggregationTask",
        "iPhone",
        "iPad",
        "TemporaryChannel",
        "LegalPersonOffline",
        "EcSite",
        "Inventory",
        "OfficialAccount",
        "Purchasing",
        "GiftCard",
        "DebitCard",
        "DebitCardPayment",
        "CreditCard",
        "CreditCardPayment"
    ],
    "message": "Found 16 models available for export"
}
```

### 2. 导出模型数据

**请求方法:** POST

**请求头:**
```
Authorization: Bearer YOUR_TOKEN_HERE
Content-Type: application/json
```

**请求体参数:**

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| models | array | 否 | 要导出的模型名称列表。如果不提供，将导出所有模型 |

**请求示例 1 - 导出指定模型:**
```bash
curl -X POST http://localhost:8000/api/aggregation/export-to-excel/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "models": ["iPhone", "iPad", "Inventory"]
  }'
```

**请求示例 2 - 导出所有模型:**
```bash
curl -X POST http://localhost:8000/api/aggregation/export-to-excel/ \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**响应示例 - 成功:**
```json
{
    "status": "success",
    "message": "Exported 3 model(s) successfully",
    "results": [
        {
            "model": "iPhone",
            "filename": "iPhone_test_20250101_120000.xlsx",
            "upload_status": "success",
            "upload_url": "http://nextcloud-app/remote.php/dav/files/username/data_platform/iPhone_test_20250101_120000.xlsx",
            "message": "File uploaded successfully to http://..."
        },
        {
            "model": "iPad",
            "filename": "iPad_test_20250101_120001.xlsx",
            "upload_status": "success",
            "upload_url": "http://nextcloud-app/remote.php/dav/files/username/data_platform/iPad_test_20250101_120001.xlsx",
            "message": "File uploaded successfully to http://..."
        },
        {
            "model": "Inventory",
            "filename": "Inventory_test_20250101_120002.xlsx",
            "upload_status": "success",
            "upload_url": "http://nextcloud-app/remote.php/dav/files/username/data_platform/Inventory_test_20250101_120002.xlsx",
            "message": "File uploaded successfully to http://..."
        }
    ]
}
```

**响应示例 - 部分失败:**
```json
{
    "status": "partial_success",
    "message": "Exported 2 model(s) successfully",
    "results": [
        {
            "model": "iPhone",
            "filename": "iPhone_test_20250101_120000.xlsx",
            "upload_status": "success",
            "upload_url": "http://...",
            "message": "File uploaded successfully"
        }
    ],
    "errors": [
        {
            "model": "InvalidModel",
            "error": "Model 'InvalidModel' not found in data_aggregation app"
        }
    ]
}
```

## 认证错误处理

### 无Token
**HTTP状态码:** 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### Token无效
**HTTP状态码:** 401 Unauthorized
```json
{
    "detail": "Invalid token"
}
```

### Token过期
**HTTP状态码:** 401 Unauthorized
```json
{
    "detail": "Token has expired"
}
```

## 使用Python请求示例

```python
import requests
import json

# API配置
API_URL = "http://localhost:8000/api/aggregation/export-to-excel/"
TOKEN = "YOUR_TOKEN_HERE"

# 设置请求头
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 1. 获取可用模型列表
response = requests.get(API_URL, headers=headers)
print(response.json())

# 2. 导出指定模型
data = {
    "models": ["iPhone", "iPad", "Inventory"]
}
response = requests.post(API_URL, headers=headers, json=data)
print(response.json())

# 3. 导出所有模型
response = requests.post(API_URL, headers=headers, json={})
print(response.json())
```

## 文件命名规则

导出的Excel文件命名格式：
```
{模型名称}_test_{时间戳}.xlsx
```

示例：
- `iPhone_test_20250101_120000.xlsx`
- `iPad_test_20250101_120001.xlsx`
- `Inventory_test_20250101_120002.xlsx`

## 注意事项

1. **Token安全**: 请妥善保管生成的token，不要在公开场合泄露
2. **Token过期**: Token有默认30天有效期，过期后需重新生成
3. **Nextcloud配置**: 确保Nextcloud服务可访问且WebDAV凭据正确
4. **大数据量**: 导出大量数据时可能需要较长时间，建议分批导出
5. **模型名称**: 模型名称区分大小写，请使用正确的模型名称

## 故障排查

### 上传到Nextcloud失败

检查以下配置：
1. Nextcloud服务是否正常运行
2. WebDAV URL是否正确
3. 用户名和密码是否正确
4. 目标文件夹是否存在且有写入权限

### 模型未找到错误

使用GET请求获取可用模型列表，确保使用正确的模型名称。

### Token认证失败

1. 检查token是否正确复制（无多余空格）
2. 检查token是否已过期
3. 重新生成新的token

## 支持的模型

当前支持导出以下模型：
- AggregationSource
- AggregatedData
- AggregationTask
- iPhone
- iPad
- TemporaryChannel
- LegalPersonOffline
- EcSite
- Inventory
- OfficialAccount
- Purchasing
- GiftCard
- DebitCard
- DebitCardPayment
- CreditCard
- CreditCardPayment

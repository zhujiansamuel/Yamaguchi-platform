# LegalPersonOffline Create With Inventory API

## Overview

This API endpoint allows you to create a `LegalPersonOffline` instance along with multiple associated `Inventory` items in a single request. The endpoint supports flexible inventory creation with automatic product lookup via JAN codes.

**Endpoint:** `POST /api/aggregation/legal-person-offline/create-with-inventory/`

**Authentication:** BATCH_STATS_API_TOKEN via Authorization header
**Format:** `Authorization: Bearer <BATCH_STATS_API_TOKEN>`

---

## Features

- ✅ Create LegalPersonOffline with multiple inventory items in one request
- ✅ Automatic product lookup (iPhone/iPad) via JAN codes
- ✅ Flexible error handling: skip problematic items and continue
- ✅ Support for empty/null JAN (creates inventory without product)
- ✅ Support for empty/null IMEI
- ✅ Automatic IMEI duplicate detection and skip
- ✅ All inventory items automatically linked to LegalPersonOffline via source3
- ✅ Batch management fields for inventory classification (3 levels)
- ✅ Detailed logging for skipped items

---

## Request Format

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `username` | string | Customer username **(REQUIRED)** |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `appointment_time` | datetime | Scheduled appointment time (ISO 8601 format) |
| `visit_time` | datetime | Actual visit time (ISO 8601 format) |
| `inventory_data` | array | List of inventory items (see below) |
| `inventory_times` | object | Optional time fields for all inventory items (see below) |
| `batch_level_1` | string | First level batch identifier (applied to all inventory items) |
| `batch_level_2` | string | Second level batch identifier (applied to all inventory items) |
| `batch_level_3` | string | Third level batch identifier (applied to all inventory items) |

### Inventory Data Format

`inventory_data` is an array of objects, each representing one inventory item:

```json
{
  "jan": "4547597992388",
  "imei": "123456789012345"
}
```

**Fields:**
- `jan` (string, optional): JAN code (13 digits). Can be empty/null to create inventory without product
- `imei` (string, optional): IMEI number (up to 17 characters). Can be empty/null

### Inventory Times Format

`inventory_times` is an object with optional time fields that will be applied to **all** created inventory items:

```json
{
  "transaction_confirmed_at": "2026-01-15T10:30:00Z",
  "scheduled_arrival_at": "2026-01-22T00:00:00Z",
  "checked_arrival_at_1": "2026-01-25T00:00:00Z",
  "checked_arrival_at_2": "2026-01-28T00:00:00Z"
}
```

**Supported fields:**
- `transaction_confirmed_at`
- `scheduled_arrival_at`
- `checked_arrival_at_1`
- `checked_arrival_at_2`

### Batch Management Fields Format

Batch management fields are used for inventory classification and organization. These fields are applied to **all** created inventory items:

```json
{
  "batch_level_1": "WAREHOUSE-A",
  "batch_level_2": "AREA-1",
  "batch_level_3": "SHELF-01"
}
```

**Fields:**
- `batch_level_1` (string, optional): First level batch identifier (e.g., warehouse, facility)
- `batch_level_2` (string, optional): Second level batch identifier (e.g., area, zone)
- `batch_level_3` (string, optional): Third level batch identifier (e.g., shelf, bin)

**Use Cases:**
- **Physical Location**: Warehouse → Area → Shelf
- **Logical Grouping**: Supplier → Batch → Sub-batch
- **Temporal**: Year → Month → Week

---

## Request Examples

### Example 1: Full Request (All Fields)

```json
{
  "username": "customer123",
  "appointment_time": "2026-01-15T10:00:00Z",
  "visit_time": "2026-01-15T10:30:00Z",
  "inventory_data": [
    {
      "jan": "4547597992388",
      "imei": "123456789012345"
    },
    {
      "jan": "4547597992395",
      "imei": "987654321098765"
    }
  ],
  "inventory_times": {
    "transaction_confirmed_at": "2026-01-15T10:30:00Z",
    "scheduled_arrival_at": "2026-01-22T00:00:00Z"
  },
  "batch_level_1": "WAREHOUSE-A",
  "batch_level_2": "AREA-1",
  "batch_level_3": "SHELF-01"
}
```

### Example 2: Minimal Request (Required Field Only)

```json
{
  "username": "customer123"
}
```

### Example 3: With Empty JAN (Create Without Product)

```json
{
  "username": "customer456",
  "inventory_data": [
    {
      "jan": "",
      "imei": "111222333444555"
    }
  ]
}
```

### Example 4: With Empty IMEI

```json
{
  "username": "customer789",
  "inventory_data": [
    {
      "jan": "4547597992388",
      "imei": ""
    }
  ]
}
```

---

## Response Format

### Success Response (201 Created)

All inventory items created successfully.

```json
{
  "status": "success",
  "message": "LegalPersonOffline created with 2 inventory items",
  "data": {
    "legal_person_offline": {
      "id": 123,
      "uuid": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6-q7r8s9t0-u1v2w3x4"
    },
    "inventories": [
      {
        "id": 456,
        "uuid": "xyz123ab-cdef-4567-89ab-cdef01234567-89abcdef-01234567"
      },
      {
        "id": 457,
        "uuid": "abc456de-f012-3456-7890-abcdef123456-78901234-56789012"
      }
    ]
  }
}
```

### Partial Success Response (207 Multi-Status)

Some inventory items were skipped due to errors (e.g., IMEI duplicate).

```json
{
  "status": "partial_success",
  "message": "LegalPersonOffline created with 1 inventory item. 1 item(s) skipped due to errors.",
  "data": {
    "legal_person_offline": {
      "id": 123,
      "uuid": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6-q7r8s9t0-u1v2w3x4"
    },
    "inventories": [
      {
        "id": 456,
        "uuid": "xyz123ab-cdef-4567-89ab-cdef01234567-89abcdef-01234567"
      }
    ]
  }
}
```

### Error Response (400 Bad Request)

Validation error or other failure.

```json
{
  "status": "error",
  "message": "Validation error",
  "errors": {
    "username": ["This field is required."]
  }
}
```

---

## Behavior Details

### Product Lookup (JAN)

When a JAN code is provided:
1. First searches in `iPhone` model (where `is_deleted=False`)
2. If not found, searches in `iPad` model (where `is_deleted=False`)
3. If found, associates the inventory with the product
4. If not found in either model, creates inventory **without product association** (both `iphone` and `ipad` fields will be `null`)

### IMEI Handling

- If IMEI is empty string or null → stored as `null` in database
- If IMEI already exists → inventory item is **skipped** and error is logged
- IMEI has `unique=True` constraint

### Error Handling

The API uses a **skip-on-error** strategy:
- Errors for individual inventory items are **logged** to Django logs
- The problematic item is **skipped**
- Processing **continues** with remaining items
- LegalPersonOffline is **always created**
- Response status changes to `207` if any items were skipped

### Automatic Fields

For each created inventory:
- `status` = `'arrived'` (always)
- `flag` = `'LPO-{uuid_prefix}-{index}'` (e.g., `LPO-a1b2c3d4-001`)
- `source3` = Created LegalPersonOffline instance
- `actual_arrival_at` = Current timestamp
- Other time fields from `inventory_times` (if provided)

---

## HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 201 | Created | All inventory items created successfully |
| 207 | Multi-Status | Partial success - some items skipped |
| 400 | Bad Request | Validation error or unexpected failure |
| 401 | Unauthorized | Missing or invalid authentication token |

---

## cURL Examples

### Basic Request

```bash
curl -X POST "http://localhost:8000/api/aggregation/legal-person-offline/create-with-inventory/" \
  -H "Authorization: Bearer YOUR_BATCH_STATS_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "customer123",
    "inventory_data": [
      {
        "jan": "4547597992388",
        "imei": "123456789012345"
      }
    ]
  }'
```

### Full Request

```bash
curl -X POST "http://localhost:8000/api/aggregation/legal-person-offline/create-with-inventory/" \
  -H "Authorization: Bearer YOUR_BATCH_STATS_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "customer123",
    "appointment_time": "2026-01-15T10:00:00Z",
    "visit_time": "2026-01-15T10:30:00Z",
    "inventory_data": [
      {
        "jan": "4547597992388",
        "imei": "123456789012345"
      },
      {
        "jan": "4547597992395",
        "imei": "987654321098765"
      }
    ],
    "inventory_times": {
      "transaction_confirmed_at": "2026-01-15T10:30:00Z",
      "scheduled_arrival_at": "2026-01-22T00:00:00Z"
    }
  }'
```

---

## Python Examples

### Using requests library

```python
import requests
from datetime import datetime, timezone

url = "http://localhost:8000/api/aggregation/legal-person-offline/create-with-inventory/"
headers = {
    "Authorization": "Bearer YOUR_BATCH_STATS_API_TOKEN",
    "Content-Type": "application/json"
}

# Full request
data = {
    "username": "customer123",
    "appointment_time": datetime.now(timezone.utc).isoformat(),
    "visit_time": datetime.now(timezone.utc).isoformat(),
    "inventory_data": [
        {
            "jan": "4547597992388",
            "imei": "123456789012345"
        },
        {
            "jan": "4547597992395",
            "imei": "987654321098765"
        }
    ],
    "inventory_times": {
        "transaction_confirmed_at": datetime.now(timezone.utc).isoformat(),
    }
}

response = requests.post(url, json=data, headers=headers)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
```

### Minimal request

```python
import requests

url = "http://localhost:8000/api/aggregation/legal-person-offline/create-with-inventory/"
headers = {
    "Authorization": "Bearer YOUR_BATCH_STATS_API_TOKEN",
    "Content-Type": "application/json"
}

data = {
    "username": "customer123"
}

response = requests.post(url, json=data, headers=headers)
result = response.json()

if response.status_code in [201, 207]:
    print(f"✓ Created LegalPersonOffline ID: {result['data']['legal_person_offline']['id']}")
    print(f"✓ Created {len(result['data']['inventories'])} inventory items")
else:
    print(f"✗ Error: {result['message']}")
```

---

## Common Use Cases

### Case 1: Single Customer with Multiple Devices

```json
{
  "username": "corporate_buyer_001",
  "visit_time": "2026-01-15T14:30:00Z",
  "inventory_data": [
    {"jan": "4547597992388", "imei": "111111111111111"},
    {"jan": "4547597992395", "imei": "222222222222222"},
    {"jan": "4547597992401", "imei": "333333333333333"}
  ]
}
```

### Case 2: Customer Without Inventory

```json
{
  "username": "walk_in_customer_123",
  "visit_time": "2026-01-15T15:00:00Z"
}
```

### Case 3: Unknown Products (Empty JAN)

```json
{
  "username": "special_order_customer",
  "inventory_data": [
    {"jan": "", "imei": "999999999999999"}
  ]
}
```

---

## Logging

Errors for skipped inventory items are logged to Django logs with the following format:

**Warning (IMEI duplicate):**
```
WARNING - Skipped inventory item 2 for LegalPersonOffline a1b2c3d4-...:
JAN=4547597992395, IMEI=123456789012345, Error: UNIQUE constraint failed: inventory.imei
```

**Error (Other errors):**
```
ERROR - Skipped inventory item 3 for LegalPersonOffline a1b2c3d4-...:
JAN=invalid, IMEI=123, Error: [specific error message]
```

---

## Notes

- All datetime fields use **ISO 8601 format** (e.g., `2026-01-15T10:30:00Z`)
- The `uuid` field is **auto-generated** for LegalPersonOffline
- Each inventory gets a unique `flag` in format `LPO-{uuid_prefix}-{index:03d}`
- Response only returns `id` and `uuid` for simplicity
- Error details are **not** returned in response, only logged server-side

---

## Related Documentation

- [API_LEGAL_PERSON_OFFLINE.md](./API_LEGAL_PERSON_OFFLINE.md) - Standard CRUD operations
- [API_INVENTORY.md](./API_INVENTORY.md) - Inventory management
- [CREATE_WITH_INVENTORY_GUIDE.md](./CREATE_WITH_INVENTORY_GUIDE.md) - Purchasing create_with_inventory guide

---

## Support

For issues or questions, please contact the development team or check the project repository.

# 药品添加功能完善说明

## 新增功能

### 1. 生产厂家管理
- **问题**: 添加新药品时，如果填写的生产厂家之前没有出现在数据库中，系统无法处理
- **解决方案**: 
  - 在添加药品时检查生产厂家是否已存在于 `Manufacture` 表中
  - 如果厂家不存在，**必须**填写 `manufacture_address` 字段
  - 系统会自动创建新的生产厂家记录

### 2. 处方药处方ID管理
- **问题**: 处方药应该关联具体的处方，但之前可以留空
- **解决方案**:
  - 添加处方药时，`prescription_id` 字段变为**必填**
  - 系统会验证提供的处方ID是否存在于 `Prescription` 表中
  - 如果处方ID不存在，返回错误提示

## API接口更新

### 修改的接口

#### POST /api/add_medicine
**新增必填字段（条件性）**:
- `manufacture_address`: 当生产厂家不存在时必填
- `prescription_id`: 当药品类型为 "Prescription" 时必填

**请求示例**:

添加OTC药品（新生产厂家）:
```json
{
    "national_code": "OTC001",
    "name": "感冒灵",
    "medicine_type": "OTC",
    "manufacture_name": "新康制药",
    "manufacture_address": "北京市朝阳区健康路123号",  // 新厂家必填
    "manufacture_date": "2024-01-01",
    "expiry_date": "2026-01-01",
    "remaining_quantity": 100,
    "price": 15.5,
    "cabinet_id": 1,
    "direction": "每日三次，每次2粒"
}
```

添加处方药:
```json
{
    "national_code": "RX001", 
    "name": "阿莫西林",
    "medicine_type": "Prescription",
    "manufacture_name": "辉瑞制药",
    "prescription_id": "P20240526001",  // 处方药必填
    "manufacture_date": "2024-01-01",
    "expiry_date": "2026-01-01",
    "remaining_quantity": 50,
    "price": 25.0,
    "cabinet_id": 2
}
```

### 新增的接口

#### GET /api/manufactures
获取所有生产厂家列表

**响应示例**:
```json
[
    {
        "manufacture_name": "辉瑞制药",
        "address": "上海市浦东新区XX路456号"
    },
    {
        "manufacture_name": "新康制药", 
        "address": "北京市朝阳区健康路123号"
    }
]
```

#### GET /api/check_manufacture/{manufacture_name}
检查指定生产厂家是否存在

**响应示例**:
```json
{
    "exists": true,
    "address": "上海市浦东新区XX路456号"
}
```

## 错误处理

### 新增的错误消息

1. **生产厂家不存在且未提供地址**:
   ```json
   {
       "error": "生产厂家 \"新康制药\" 不存在于系统中，请填写厂家地址！"
   }
   ```

2. **处方药未填写处方ID**:
   ```json
   {
       "error": "添加处方药时必须填写处方ID！"
   }
   ```

3. **处方ID不存在**:
   ```json
   {
       "error": "处方ID \"P20240526999\" 不存在！请输入有效的处方ID。"
   }
   ```

## 数据库变更

无需额外的数据库迁移，利用现有的表结构：
- `Manufacture` 表：存储生产厂家信息
- `Prescription` 表：存储处方信息
- `PrescriptionMedicine` 表：关联处方和药品

## 测试

运行测试脚本验证功能：
```bash
python test_medicine_api.py
```

测试内容包括：
- 新生产厂家需要地址验证
- OTC药品添加成功
- 处方药必须填写处方ID验证
- 生产厂家列表获取
- 生产厂家存在性检查

## 前端集成建议

1. **添加药品表单**:
   - 当用户输入生产厂家名称时，调用 `/api/check_manufacture/{name}` 检查是否存在
   - 如果厂家不存在，显示地址输入框并标记为必填
   - 当选择处方药类型时，处方ID字段变为必填

2. **用户体验优化**:
   - 提供生产厂家下拉选择列表（从 `/api/manufactures` 获取）
   - 处方ID可以提供自动完成功能（从 `/api/prescriptions` 获取）
   - 实时表单验证，减少提交后的错误

这些改进确保了数据的完整性和一致性，同时提供了更好的用户体验。

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
药品添加功能完善验证脚本
测试新增的以下功能：
1. 生产厂家不存在时需要填写地址
2. 处方药必须填写处方ID
3. 新增的API接口正常工作
"""

import requests
import json
import time

# API基础URL
BASE_URL = "http://127.0.0.1:5000/api"

def print_separator(title):
    """打印分隔线"""
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")

def test_api_endpoint(url, method='GET', data=None, expected_status=200):
    """测试API端点"""
    try:
        if method == 'GET':
            response = requests.get(url)
        elif method == 'POST':
            response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        
        print(f"请求: {method} {url}")
        if data:
            print(f"数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        if response.status_code == expected_status:
            print("✅ 测试通过")
            return response.json()
        else:
            print(f"❌ 期望状态码 {expected_status}，实际 {response.status_code}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败：请确保Flask应用正在运行")
        return None
    except Exception as e:
        print(f"❌ 测试失败：{str(e)}")
        return None

def test_new_apis():
    """测试新增的API接口"""
    print_separator("测试新增API接口")
    
    # 测试获取生产厂家列表
    print("\n📋 测试获取生产厂家列表")
    manufactures = test_api_endpoint(f"{BASE_URL}/manufactures")
    
    # 测试检查生产厂家存在性
    print("\n🔍 测试检查生产厂家存在性")
    if manufactures and len(manufactures) > 0:
        # 测试存在的厂家
        existing_manufacture = manufactures[0]['manufacture_name']
        test_api_endpoint(f"{BASE_URL}/check_manufacture/{existing_manufacture}")
    
    # 测试不存在的厂家
    test_api_endpoint(f"{BASE_URL}/check_manufacture/不存在的测试厂家")

def test_otc_medicine_scenarios():
    """测试OTC药品添加场景"""
    print_separator("测试OTC药品添加场景")
    
    # 场景1：使用已存在的生产厂家
    print("\n📦 场景1：使用已存在的生产厂家添加OTC药品")
    otc_data_existing = {
        "national_code": "OTC_TEST_001",
        "name": "测试感冒药",
        "medicine_type": "OTC",
        "manufacture_name": "辉瑞制药",  # 假设已存在
        "manufacture_date": "2024-01-01",
        "expiry_date": "2026-01-01",
        "remaining_quantity": 100,
        "price": 15.5,
        "cabinet_id": 1,
        "direction": "每日三次，每次2粒，饭后服用"
    }
    test_api_endpoint(f"{BASE_URL}/add_medicine", 'POST', otc_data_existing)
    
    # 场景2：使用新的生产厂家但不提供地址（应该失败）
    print("\n❌ 场景2：新生产厂家不提供地址（期望失败）")
    otc_data_no_address = {
        "national_code": "OTC_TEST_002",
        "name": "测试止痛药",
        "medicine_type": "OTC",
        "manufacture_name": "新康健制药有限公司",  # 新厂家
        "manufacture_date": "2024-01-01",
        "expiry_date": "2026-01-01",
        "remaining_quantity": 50,
        "price": 20.0,
        "cabinet_id": 1,
        "direction": "每日两次，每次1粒"
        # 故意不提供 manufacture_address
    }
    test_api_endpoint(f"{BASE_URL}/add_medicine", 'POST', otc_data_no_address, 400)
    
    # 场景3：使用新的生产厂家并提供地址（应该成功）
    print("\n✅ 场景3：新生产厂家提供地址（期望成功）")
    otc_data_with_address = {
        "national_code": "OTC_TEST_003",
        "name": "测试维生素",
        "medicine_type": "OTC",
        "manufacture_name": "新康健制药有限公司",
        "manufacture_address": "广州市天河区科技园路888号",  # 提供地址
        "manufacture_date": "2024-01-01",
        "expiry_date": "2026-01-01",
        "remaining_quantity": 200,
        "price": 12.0,
        "cabinet_id": 1,
        "direction": "每日一次，每次1粒，随餐服用"
    }
    test_api_endpoint(f"{BASE_URL}/add_medicine", 'POST', otc_data_with_address)

def test_prescription_medicine_scenarios():
    """测试处方药添加场景"""
    print_separator("测试处方药添加场景")
    
    # 先创建一个测试处方（如果不存在）
    print("\n📝 创建测试处方")
    # 注意：这里假设你有创建处方的API，如果没有需要手动在数据库中添加
    
    # 场景1：不提供处方ID（应该失败）
    print("\n❌ 场景1：处方药不提供处方ID（期望失败）")
    prescription_data_no_id = {
        "national_code": "RX_TEST_001",
        "name": "测试抗生素",
        "medicine_type": "Prescription",
        "manufacture_name": "新康健制药有限公司",  # 使用刚创建的厂家
        "manufacture_date": "2024-01-01",
        "expiry_date": "2026-01-01",
        "remaining_quantity": 30,
        "price": 50.0,
        "cabinet_id": 2
        # 故意不提供 prescription_id
    }
    test_api_endpoint(f"{BASE_URL}/add_medicine", 'POST', prescription_data_no_id, 400)
    
    # 场景2：提供不存在的处方ID（应该失败）
    print("\n❌ 场景2：提供不存在的处方ID（期望失败）")
    prescription_data_invalid_id = {
        "national_code": "RX_TEST_002",
        "name": "测试心脏病药",
        "medicine_type": "Prescription",
        "manufacture_name": "新康健制药有限公司",
        "prescription_id": "INVALID_PRESCRIPTION_999",  # 不存在的处方ID
        "manufacture_date": "2024-01-01",
        "expiry_date": "2026-01-01",
        "remaining_quantity": 25,
        "price": 75.0,
        "cabinet_id": 2
    }
    test_api_endpoint(f"{BASE_URL}/add_medicine", 'POST', prescription_data_invalid_id, 400)
    
    # 场景3：提供有效处方ID（如果存在有效处方的话）
    print("\n🔍 检查是否有可用的处方ID")
    prescriptions = test_api_endpoint(f"{BASE_URL}/prescriptions")
    if prescriptions and len(prescriptions) > 0:
        valid_prescription_id = prescriptions[0]['prescription_id']
        print(f"\n✅ 场景3：使用有效处方ID {valid_prescription_id}")
        prescription_data_valid = {
            "national_code": "RX_TEST_003",
            "name": "测试降压药",
            "medicine_type": "Prescription",
            "manufacture_name": "新康健制药有限公司",
            "prescription_id": valid_prescription_id,
            "manufacture_date": "2024-01-01",
            "expiry_date": "2026-01-01",
            "remaining_quantity": 40,
            "price": 60.0,
            "cabinet_id": 2
        }
        test_api_endpoint(f"{BASE_URL}/add_medicine", 'POST', prescription_data_valid)
    else:
        print("⚠️  数据库中没有可用的处方，跳过有效处方ID测试")

def test_edge_cases():
    """测试边界情况"""
    print_separator("测试边界情况")
    
    # 测试特殊字符的厂家名称
    print("\n🔤 测试特殊字符厂家名称")
    special_name = "测试&制药(有限公司)"
    test_api_endpoint(f"{BASE_URL}/check_manufacture/{special_name}")
    
    # 测试空厂家名称
    print("\n📭 测试空厂家名称")
    empty_data = {
        "national_code": "EMPTY_TEST_001",
        "name": "测试药品",
        "medicine_type": "OTC",
        "manufacture_name": "",  # 空厂家名称
        "direction": "测试用法"
    }
    test_api_endpoint(f"{BASE_URL}/add_medicine", 'POST', empty_data, 400)

def main():
    """主测试函数"""
    print("🧪 开始测试药品添加功能完善...")
    print("📋 测试内容：")
    print("  1. 新增API接口")
    print("  2. OTC药品添加场景")
    print("  3. 处方药添加场景")
    print("  4. 边界情况测试")
    
    # 等待用户确认
    input("\n按回车键开始测试...")
    
    try:
        # 运行所有测试
        test_new_apis()
        time.sleep(1)
        
        test_otc_medicine_scenarios()
        time.sleep(1)
        
        test_prescription_medicine_scenarios()
        time.sleep(1)
        
        test_edge_cases()
        
        print_separator("测试完成")
        print("🎉 所有测试已完成！")
        print("📊 请查看上方的测试结果：")
        print("  ✅ 表示测试通过")
        print("  ❌ 表示测试失败（某些失败是预期的）")
        print("  ⚠️  表示警告或跳过的测试")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n\n💥 测试过程中发生错误：{str(e)}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试药品添加API的脚本
测试新增的功能：
1. 生产厂家不存在时需要填写地址
2. 处方药必须填写处方ID
"""

import requests
import json

# API基础URL
BASE_URL = "http://localhost:5000/api"

def test_add_otc_medicine_new_manufacture():
    """测试添加OTC药品时，新的生产厂家需要填写地址"""
    print("测试1: 添加OTC药品，新生产厂家需要地址")
    
    # 测试数据 - 缺少生产厂家地址
    medicine_data = {
        "national_code": "TEST001",
        "name": "测试感冒药",
        "medicine_type": "OTC",
        "manufacture_name": "新生产厂家A",
        "manufacture_date": "2024-01-01",
        "expiry_date": "2026-01-01",
        "remaining_quantity": 100,
        "price": 15.5,
        "cabinet_id": 1,
        "direction": "每日三次，每次2粒"
        # 注意：故意不提供 manufacture_address
    }
    
    response = requests.post(f"{BASE_URL}/add_medicine", json=medicine_data)
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
    
    # 应该返回错误，要求填写厂家地址
    assert response.status_code == 400
    assert "请填写厂家地址" in response.json()['error']
    print("✓ 测试通过：正确要求填写厂家地址\n")

def test_add_otc_medicine_with_manufacture_address():
    """测试添加OTC药品时，提供生产厂家地址"""
    print("测试2: 添加OTC药品，提供生产厂家地址")
    
    medicine_data = {
        "national_code": "TEST002",
        "name": "测试止痛药",
        "medicine_type": "OTC",
        "manufacture_name": "新生产厂家B",
        "manufacture_address": "北京市朝阳区XX路123号",  # 提供地址
        "manufacture_date": "2024-01-01",
        "expiry_date": "2026-01-01",
        "remaining_quantity": 50,
        "price": 20.0,
        "cabinet_id": 1,
        "direction": "每日两次，每次1粒"
    }
    
    response = requests.post(f"{BASE_URL}/add_medicine", json=medicine_data)
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
    
    # 应该成功
    assert response.status_code == 200
    assert "添加成功" in response.json()['message']
    print("✓ 测试通过：成功添加OTC药品\n")

def test_add_prescription_medicine_without_prescription_id():
    """测试添加处方药时，不提供处方ID"""
    print("测试3: 添加处方药，不提供处方ID")
    
    medicine_data = {
        "national_code": "TEST003",
        "name": "测试抗生素",
        "medicine_type": "Prescription",
        "manufacture_name": "新生产厂家B",  # 使用已存在的厂家
        "manufacture_date": "2024-01-01",
        "expiry_date": "2026-01-01",
        "remaining_quantity": 30,
        "price": 50.0,
        "cabinet_id": 2
        # 注意：故意不提供 prescription_id
    }
    
    response = requests.post(f"{BASE_URL}/add_medicine", json=medicine_data)
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
    
    # 应该返回错误，要求填写处方ID
    assert response.status_code == 400
    assert "必须填写处方ID" in response.json()['error']
    print("✓ 测试通过：正确要求填写处方ID\n")

def test_get_manufactures():
    """测试获取生产厂家列表"""
    print("测试4: 获取生产厂家列表")
    
    response = requests.get(f"{BASE_URL}/manufactures")
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
    
    assert response.status_code == 200
    manufactures = response.json()
    assert isinstance(manufactures, list)
    print("✓ 测试通过：成功获取生产厂家列表\n")

def test_check_manufacture_exists():
    """测试检查生产厂家是否存在"""
    print("测试5: 检查生产厂家是否存在")
    
    # 检查已存在的厂家
    response = requests.get(f"{BASE_URL}/check_manufacture/新生产厂家B")
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
    
    assert response.status_code == 200
    result = response.json()
    assert result['exists'] == True
    assert result['address'] is not None
    print("✓ 测试通过：正确检测到已存在的厂家\n")
    
    # 检查不存在的厂家
    response = requests.get(f"{BASE_URL}/check_manufacture/不存在的厂家")
    print(f"检查不存在厂家 - 响应状态码: {response.status_code}")
    print(f"检查不存在厂家 - 响应内容: {response.json()}")
    
    result = response.json()
    assert result['exists'] == False
    assert result['address'] is None
    print("✓ 测试通过：正确检测到不存在的厂家\n")

if __name__ == "__main__":
    print("开始测试药品添加API的新功能...\n")
    
    try:
        test_add_otc_medicine_new_manufacture()
        test_add_otc_medicine_with_manufacture_address()
        test_add_prescription_medicine_without_prescription_id()
        test_get_manufactures()
        test_check_manufacture_exists()
        
        print("🎉 所有测试通过！新功能工作正常。")
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误：请确保Flask应用正在运行在 http://localhost:5000")
    except AssertionError as e:
        print(f"❌ 测试失败：{e}")
    except Exception as e:
        print(f"❌ 未知错误：{e}")

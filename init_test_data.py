#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化测试数据脚本
为智能药箱系统添加一些基础的测试数据
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000/api"

def add_sample_data():
    """添加示例数据"""
    print("🔧 初始化测试数据...")
    
    # 1. 初始化默认数据（药箱等）
    print("\n📦 初始化药箱数据...")
    try:
        response = requests.post(f"{BASE_URL}/init_data")
        if response.status_code == 200:
            print("✅ 药箱数据初始化成功")
        else:
            print(f"⚠️  药箱数据初始化响应: {response.json()}")
    except Exception as e:
        print(f"❌ 药箱数据初始化失败: {e}")
    
    # 2. 添加一些生产厂家
    print("\n🏭 添加基础生产厂家...")
    manufactures_data = [
        {
            "national_code": "BASE_MED_001",
            "name": "基础药品1号",
            "medicine_type": "OTC",
            "manufacture_name": "辉瑞制药",
            "manufacture_address": "上海市浦东新区科技路123号",
            "manufacture_date": "2024-01-01",
            "expiry_date": "2026-01-01",
            "remaining_quantity": 100,
            "price": 25.5,
            "cabinet_id": 1,
            "direction": "每日三次，每次1粒"
        },
        {
            "national_code": "BASE_MED_002",
            "name": "基础药品2号",
            "medicine_type": "OTC",
            "manufacture_name": "同仁堂",
            "manufacture_address": "北京市东城区前门大街19号",
            "manufacture_date": "2024-02-01",
            "expiry_date": "2026-02-01",
            "remaining_quantity": 80,
            "price": 18.0,
            "cabinet_id": 1,
            "direction": "每日两次，每次2粒"
        }
    ]
    
    for med_data in manufactures_data:
        try:
            response = requests.post(f"{BASE_URL}/add_medicine", json=med_data)
            if response.status_code == 200:
                print(f"✅ 添加 {med_data['name']} 成功")
            else:
                result = response.json()
                if "已更新" in result.get('message', ''):
                    print(f"ℹ️  {med_data['name']} 已存在，数量已更新")
                else:
                    print(f"⚠️  添加 {med_data['name']} 失败: {result}")
        except Exception as e:
            print(f"❌ 添加 {med_data['name']} 出错: {e}")
    
    # 3. 添加一些家庭成员
    print("\n👥 添加测试家庭成员...")
    members_data = [
        {
            "security_id": "TEST_001",
            "name": "张三",
            "gender": "M",
            "age": 35,
            "weight": 70.5,
            "height": 175.0,
            "underlying_disease": "无",
            "allergen": "青霉素"
        },
        {
            "security_id": "TEST_002", 
            "name": "李四",
            "gender": "F",
            "age": 30,
            "weight": 55.0,
            "height": 165.0,
            "underlying_disease": "高血压",
            "allergen": "无"
        }
    ]
    
    for member_data in members_data:
        try:
            response = requests.post(f"{BASE_URL}/add_member", json=member_data)
            if response.status_code == 200:
                print(f"✅ 添加成员 {member_data['name']} 成功")
            else:
                print(f"⚠️  添加成员 {member_data['name']} 失败: {response.json()}")
        except Exception as e:
            print(f"❌ 添加成员 {member_data['name']} 出错: {e}")
    
    print("\n🎉 测试数据初始化完成！")
    print("📋 现在可以运行综合测试：python comprehensive_test.py")

if __name__ == "__main__":
    add_sample_data()

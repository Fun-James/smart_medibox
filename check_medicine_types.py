from app import create_app
from app.models import Medicine, PrescriptionMedicine, OTC
from sqlalchemy import func

# 创建应用上下文
app = create_app()
with app.app_context():
    print("\n=== 检查数据库中真实的数据 ===")
    # 先查询一些处方药记录
    prescription_meds = PrescriptionMedicine.query.all()
    print(f"处方药表中共有 {len(prescription_meds)} 条记录")
    
    # 再查询一些非处方药记录
    otc_meds = OTC.query.all()
    print(f"非处方药表中共有 {len(otc_meds)} 条记录")
    
    # 检查代码与前端显示差异
    print("\n=== 检查每种药品的类型判断 ===")
    medicines = Medicine.query.all()
    print(f"药品总数: {len(medicines)}")
    
    for med in medicines:
        # 模拟routes.py中的判断逻辑
        is_prescription = PrescriptionMedicine.query.filter_by(national_code=med.national_code).first()
        is_otc = OTC.query.filter_by(national_code=med.national_code).first()
        
        if is_prescription:
            med_type = '处方药'
        else:
            if is_otc:
                med_type = '非处方药'
            else:
                med_type = '未知'
        
        print(f"药品编码: {med.national_code}, 名称: {med.name}, 类型判断: {med_type}")
        
        # 输出详细信息来调试
        print(f"  - PrescriptionMedicine查询结果: {'找到' if is_prescription else '未找到'}")
        if is_prescription:
            print(f"  - 处方ID: {is_prescription.prescription_id}")
        print(f"  - OTC查询结果: {'找到' if is_otc else '未找到'}")
        if is_otc:
            print(f"  - 用法: {is_otc.direction[:20]}...")
        print("")  # 输出空行分隔

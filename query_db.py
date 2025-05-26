from app import create_app
from app.models import Medicine, PrescriptionMedicine, OTC

# 创建应用上下文
app = create_app()
with app.app_context():
    print("\n==== 处方药 ====")
    prescription_medicines = PrescriptionMedicine.query.all()
    for m in prescription_medicines:
        med = Medicine.query.get(m.national_code)
        print(f"- {m.national_code} - {med.name if med else '未知'}")
    
    print("\n==== 非处方药 ====")
    otc_medicines = OTC.query.all()
    for m in otc_medicines:
        med = Medicine.query.get(m.national_code)
        print(f"- {m.national_code} - {med.name if med else '未知'}")
        
    print("\n==== 重叠判断 ====")
    # 找出既在处方药表又在OTC表的药品
    prescription_codes = [m.national_code for m in prescription_medicines]
    otc_codes = [m.national_code for m in otc_medicines]
    overlaps = set(prescription_codes) & set(otc_codes)
    if overlaps:
        print(f"警告：以下药品同时出现在处方药和非处方药表中：{overlaps}")
    else:
        print("无重叠药品，数据一致")
        
    print("\n==== 所有药品及其类型判断 ====")
    medicines = Medicine.query.all()
    for m in medicines:
        is_prescription = any(pm.national_code == m.national_code for pm in prescription_medicines)
        is_otc = any(otc.national_code == m.national_code for otc in otc_medicines)
        
        if is_prescription and is_otc:
            med_type = '数据冲突：既是处方药又是非处方药'
        elif is_prescription:
            med_type = '处方药'
        elif is_otc:
            med_type = '非处方药'
        else:
            med_type = '未知类型'
            
        print(f"- {m.national_code} - {m.name} - {med_type}")

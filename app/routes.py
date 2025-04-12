from flask import Blueprint, render_template, request, jsonify
from .models import Medicine, Member, MedicineAdministration, MedicineCabinet, Prescription, Prescribe, PrescriptionMedicine
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from . import db

main = Blueprint('main', __name__)

# 初始化定时任务调度器
scheduler = BackgroundScheduler()
scheduler.start()

@main.route('/')
def index():
    return render_template('index.html')

# 获取药品列表
@main.route('/api/medicines', methods=['GET'])
def get_medicines():
    medicines = Medicine.query.all()
    medicines_data = [{'national_code': m.national_code, 'name': m.name, 'remaining_quantity': m.remaining_quantity} for m in medicines]
    return jsonify(medicines_data)

# 获取成员列表
@main.route('/api/members', methods=['GET'])
def get_members():
    members = Member.query.all()
    members_data = [{'security_id': m.security_id, 'name': m.name, 'gender': m.gender, 'age': m.age} for m in members]
    return jsonify(members_data)

# 获取成员服药记录
@main.route('/api/member_medicine_records/<string:security_id>', methods=['GET'])
def get_member_medicine_records(security_id):
    records = MedicineAdministration.query.filter_by(security_id=security_id).all()
    records_data = []
    for r in records:
        medicine = Medicine.query.get(r.national_code)
        records_data.append({
            'medicine_name': medicine.name if medicine else '未知药品',
            'dosage': r.dosage,
            'start_time': r.start_time.strftime('%Y-%m-%d %H:%M:%S') if r.start_time else '未知',
            'lasting_time': r.lasting_time
        })
    return jsonify(records_data)

# 新增：获取家庭成员详细信息
@main.route('/api/member_details/<string:security_id>', methods=['GET'])
def get_member_details(security_id):
    member = Member.query.get(security_id)
    if not member:
        return jsonify({'error': 'Member not found'}), 404
    
    member_data = {
        'security_id': member.security_id,
        'name': member.name,
        'gender': member.gender,
        'age': member.age,
        'weight': member.weight,
        'height': member.height,
        'underlying_disease': member.underlying_disease,
        'allergen': member.allergen
    }
    return jsonify(member_data)

# 新增：获取药品详细信息（包括存放位置）
@main.route('/api/medicine_details/<string:national_code>', methods=['GET'])
def get_medicine_details(national_code):
    medicine = Medicine.query.get(national_code)
    if not medicine:
        return jsonify({'error': 'Medicine not found'}), 404
    
    cabinet = MedicineCabinet.query.get(medicine.cabinet_id) if medicine.cabinet_id else None
    
    medicine_data = {
        'national_code': medicine.national_code,
        'name': medicine.name,
        'manufacture_name': medicine.manufacture_name,
        'manufacture_date': medicine.manufacture_date.strftime('%Y-%m-%d') if medicine.manufacture_date else '未知',
        'remaining_quantity': medicine.remaining_quantity,
        'expiry_date': medicine.expiry_date.strftime('%Y-%m-%d') if medicine.expiry_date else '未知',
        'price': medicine.price,
        'cabinet_id': medicine.cabinet_id,
        'cabinet_location': cabinet.location if cabinet else '未知'
    }
    return jsonify(medicine_data)

# 新增：获取所有处方信息
@main.route('/api/prescriptions', methods=['GET'])
def get_prescriptions():
    prescriptions = Prescription.query.all()
    prescriptions_data = []
    
    for p in prescriptions:
        prescriptions_data.append({
            'prescription_id': p.prescription_id,
            'time': p.time.strftime('%Y-%m-%d') if p.time else '未知',
            'doctor': p.doctor
        })
    
    return jsonify(prescriptions_data)

# 新增：获取处方详情（包括开给谁和包含哪些药品）
@main.route('/api/prescription_details/<string:prescription_id>', methods=['GET'])
def get_prescription_details(prescription_id):
    prescription = Prescription.query.get(prescription_id)
    if not prescription:
        return jsonify({'error': 'Prescription not found'}), 404
    
    # 查询这个处方开给哪些成员
    prescribe_records = Prescribe.query.filter_by(prescription_id=prescription_id).all()
    members = []
    for record in prescribe_records:
        member = Member.query.get(record.security_id)
        if member:
            members.append({
                'security_id': member.security_id,
                'name': member.name
            })
    
    # 查询这个处方包含哪些药品
    prescription_medicines = PrescriptionMedicine.query.filter_by(prescription_id=prescription_id).all()
    medicines = []
    for pm in prescription_medicines:
        medicine = Medicine.query.get(pm.national_code)
        if medicine:
            medicines.append({
                'national_code': medicine.national_code,
                'name': medicine.name
            })
    
    prescription_data = {
        'prescription_id': prescription.prescription_id,
        'time': prescription.time.strftime('%Y-%m-%d') if prescription.time else '未知',
        'doctor': prescription.doctor,
        'members': members,
        'medicines': medicines
    }
    
    return jsonify(prescription_data)

# 获取家庭成员当前用药情况
@main.route('/api/current_medications', methods=['GET'])
def get_current_medications():
    current_date = datetime.datetime.now()
    # 查询所有正在进行的用药记录
    records = MedicineAdministration.query.filter(
        MedicineAdministration.start_time <= current_date
    ).all()
    
    result = {}
    
    for record in records:
        try:
            # 计算用药是否仍在有效期内
            is_valid = False
            if record.lasting_time == '长期':
                is_valid = True
            elif record.start_time and record.lasting_time:
                # 安全地解析持续时间
                try:
                    days_str = record.lasting_time.replace('天', '')
                    days = int(days_str)
                    # 检查药品是否在有效期内
                    if record.start_time + datetime.timedelta(days=days) >= current_date:
                        is_valid = True
                except (ValueError, AttributeError):
                    # 如果解析失败，假定药品仍然有效
                    is_valid = True
            
            if is_valid:
                member = Member.query.get(record.security_id)
                medicine = Medicine.query.get(record.national_code)
                
                if member and medicine:
                    if record.security_id not in result:
                        result[record.security_id] = {
                            'member_name': member.name,
                            'security_id': record.security_id,
                            'medications': []
                        }
                    
                    medication_info = {
                        'medicine_name': medicine.name,
                        'national_code': record.national_code,
                        'start_time': record.start_time.strftime('%Y-%m-%d %H:%M:%S') if record.start_time else '未知',
                        'dosage': record.dosage,
                        'lasting_time': record.lasting_time
                    }
                    
                    # 直接从MedicineAdministration获取生产日期
                    if record.manufacture_date:
                        medication_info['manufacture_date'] = record.manufacture_date.strftime('%Y-%m-%d')
                    else:
                        medication_info['manufacture_date'] = '未知'
                    
                    result[record.security_id]['medications'].append(medication_info)
        except Exception as e:
            # 记录错误但继续处理其他记录
            print(f"处理药品记录时出错: {str(e)}")
            continue
    
    return jsonify(list(result.values()))

# 新增：获取历史用药情况
@main.route('/api/historical_medications', methods=['GET'])
def get_historical_medications():
    current_date = datetime.datetime.now()
    # 查询所有用药记录
    records = MedicineAdministration.query.all()
    
    result = {}
    
    for record in records:
        try:
            # 计算用药是否已经过期（历史记录）
            is_historical = False
            if record.lasting_time != '长期' and record.start_time and record.lasting_time:
                # 安全地解析持续时间
                try:
                    days_str = record.lasting_time.replace('天', '')
                    days = int(days_str)
                    # 检查药品是否已经过期
                    if record.start_time + datetime.timedelta(days=days) < current_date:
                        is_historical = True
                except (ValueError, AttributeError):
                    # 如果解析失败，跳过此记录
                    continue
            
            if is_historical:
                member = Member.query.get(record.security_id)
                medicine = Medicine.query.get(record.national_code)
                
                if member and medicine:
                    if record.security_id not in result:
                        result[record.security_id] = {
                            'member_name': member.name,
                            'security_id': record.security_id,
                            'medications': []
                        }
                    
                    end_date = None
                    if record.start_time and record.lasting_time and record.lasting_time != '长期':
                        try:
                            days_str = record.lasting_time.replace('天', '')
                            days = int(days_str)
                            end_date = record.start_time + datetime.timedelta(days=days)
                        except (ValueError, AttributeError):
                            pass
                    
                    medication_info = {
                        'medicine_name': medicine.name,
                        'national_code': record.national_code,
                        'start_time': record.start_time.strftime('%Y-%m-%d %H:%M:%S') if record.start_time else '未知',
                        'end_time': end_date.strftime('%Y-%m-%d %H:%M:%S') if end_date else '未知',
                        'dosage': record.dosage,
                        'lasting_time': record.lasting_time
                    }
                    
                    result[record.security_id]['medications'].append(medication_info)
        except Exception as e:
            # 记录错误但继续处理其他记录
            print(f"处理历史药品记录时出错: {str(e)}")
            continue
    
    return jsonify(list(result.values()))

# 添加药品
@main.route('/api/add_medicine', methods=['POST'])
def api_add_medicine():
    data = request.json
    new_medicine = Medicine(national_code=data['national_code'], name=data['name'])
    db.session.add(new_medicine)
    db.session.commit()
    return jsonify({'message': 'Medicine added successfully'})

# 删除药品
@main.route('/api/delete_medicine/<string:national_code>', methods=['DELETE'])
def api_delete_medicine(national_code):
    medicine = Medicine.query.get(national_code)
    if not medicine:
        return jsonify({'error': 'Medicine not found'}), 404

    db.session.delete(medicine)
    db.session.commit()
    return jsonify({'message': 'Medicine deleted successfully'})

# 添加成员
@main.route('/api/add_member', methods=['POST'])
def api_add_member():
    data = request.json
    new_member = Member(
        security_id=data['security_id'],
        name=data['name'],
        gender=data['gender'],
        age=data['age'],
        weight=data['weight'],
        height=data['height'],
        underlying_disease=data['underlying_disease'],
        allergen=data['allergen']
    )
    db.session.add(new_member)
    db.session.commit()
    return jsonify({'message': 'Member added successfully'})

# 删除成员
@main.route('/api/delete_member/<string:security_id>', methods=['DELETE'])
def api_delete_member(security_id):
    member = Member.query.get(security_id)
    if not member:
        return jsonify({'error': 'Member not found'}), 404

    db.session.delete(member)
    db.session.commit()
    return jsonify({'message': 'Member deleted successfully'})

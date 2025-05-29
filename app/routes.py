from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from sqlalchemy import text # 导入 text 函数
from .models import Medicine, Member, MedicineAdministration, MedicineCabinet, Prescription, PrescriptionMedicine, Manufacture, OTC, UserInfo
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from . import db

main = Blueprint('main', __name__)

# 初始化定时任务调度器
scheduler = BackgroundScheduler()
scheduler.start()

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = UserInfo.query.filter_by(username=username).first()
        if user and user.password == password: # 在实际应用中，密码应该是哈希过的
            session['username'] = user.username  # 使用 username 替换 id
            flash('Login successful!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@main.route('/logout')
def logout():
    session.pop('username', None)  # 使用 username 替换 user_id
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

@main.route('/')
def index():
    if 'username' not in session:  # 使用 username 替换 user_id
        return redirect(url_for('main.login'))
    return render_template('index.html')

# 获取药品列表
@main.route('/api/medicines', methods=['GET'])
def get_medicines():
    medicines = Medicine.query.all()
    medicines_data = [{'national_code': m.national_code, 'name': m.name, 'remaining_quantity': m.remaining_quantity, 'medicine_type': m.get_medicine_type()} for m in medicines]
    return jsonify(medicines_data)

# 获取成员列表
@main.route('/api/members', methods=['GET'])
def get_members():
    members = Member.query.all()
    members_data = [{'security_id': m.security_id, 'name': m.name, 'gender': m.gender, 'age': m.age} for m in members]
    return jsonify(members_data)

# 获取药箱位置列表
@main.route('/api/cabinets', methods=['GET'])
def get_cabinets():
    cabinets = MedicineCabinet.query.all()
    cabinets_data = [{'cabinet_id': c.cabinet_id, 'location': c.location} for c in cabinets]
    return jsonify(cabinets_data)

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
        'cabinet_location': cabinet.location if cabinet else '未知',
        'medicine_type': medicine.get_medicine_type()  # 使用方法获取药品类型
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

# 获取生产厂家列表
@main.route('/api/manufactures', methods=['GET'])
def get_manufactures():
    manufactures = Manufacture.query.all()
    manufactures_data = [{'manufacture_name': m.manufacture_name, 'address': m.address} for m in manufactures]
    return jsonify(manufactures_data)

# 检查生产厂家是否存在
@main.route('/api/check_manufacture/<string:manufacture_name>', methods=['GET'])
def check_manufacture(manufacture_name):
    manufacture = Manufacture.query.get(manufacture_name)
    return jsonify({
        'exists': manufacture is not None,
        'address': manufacture.address if manufacture else None
    })

# 新增：获取处方详情（包括开给谁和包含哪些药品）
@main.route('/api/prescription_details/<string:prescription_id>', methods=['GET'])
def get_prescription_details(prescription_id):
    prescription = Prescription.query.get(prescription_id)
    if not prescription:
        return jsonify({'error': 'Prescription not found'}), 404
    
    # 查询这个处方开给哪些成员（加入异常处理）
    members = []
    try:
        prescribe_records = Prescription.query.filter_by(prescription_id=prescription_id).all()
        for record in prescribe_records:
            member = Member.query.get(record.security_id)
            if member:
                members.append({
                    'security_id': member.security_id,
                    'name': member.name
                })
    except Exception as e:
        print(f"查询处方用户时出错: {str(e)}")
        # 如果表不存在或出错，至少返回一个空列表而不是崩溃
    
    # 查询这个处方包含哪些药品
    medicines = []
    try:
        prescription_medicines = PrescriptionMedicine.query.filter_by(prescription_id=prescription_id).all()
        for pm in prescription_medicines:
            medicine = Medicine.query.get(pm.national_code)
            if medicine:
                medicines.append({
                    'national_code': medicine.national_code,
                    'name': medicine.name
                })
    except Exception as e:
        print(f"查询处方药品时出错: {str(e)}")
        # 如果表不存在或出错，至少返回一个空列表而不是崩溃
    
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
    try:
        data = request.json
        medicine_type = data.get('medicine_type') # 获取药品类型
        if not medicine_type or medicine_type not in ['OTC', 'Prescription']:
            return jsonify({'error': '无效的药品类型！必须是 OTC 或 Prescription'}), 400
        
        # 检查生产厂家是否存在，如果不存在则需要提供地址
        manufacture_name = data.get('manufacture_name', '').strip()
        if manufacture_name:
            existing_manufacture = Manufacture.query.get(manufacture_name)
            if not existing_manufacture:
                # 生产厂家不存在，检查是否提供了地址
                manufacture_address = data.get('manufacture_address', '').strip()
                if not manufacture_address:
                    return jsonify({'error': f'生产厂家 "{manufacture_name}" 不存在于系统中，请填写厂家地址！'}), 400
                
                # 创建新的生产厂家记录
                new_manufacture = Manufacture(
                    manufacture_name=manufacture_name,
                    address=manufacture_address
                )
                db.session.add(new_manufacture)
        
        # 如果是处方药，检查处方ID是否必填
        if medicine_type == 'Prescription':
            prescription_id = data.get('prescription_id', '').strip()
            if not prescription_id:
                return jsonify({'error': '添加处方药时必须填写处方ID！'}), 400
            
            # 验证处方ID是否存在
            existing_prescription = Prescription.query.get(prescription_id)
            if not existing_prescription:
                return jsonify({'error': f'处方ID "{prescription_id}" 不存在！请输入有效的处方ID。'}), 400
          # 检查药品编码是否已存在
        existing_medicine = Medicine.query.get(data['national_code'])
        if existing_medicine:
            # 如果药品已存在，检查其他信息是否相同
            if existing_medicine.name == data['name']:
                # 药品名称相同，更新数量和其他信息
                new_quantity = existing_medicine.remaining_quantity + (int(data.get('remaining_quantity', 0)) or 0)
                
                # 更新药品信息
                if data.get('manufacture_name'):
                    # 检查新的生产厂家是否存在
                    new_manufacture_name = data.get('manufacture_name').strip()
                    if new_manufacture_name != existing_medicine.manufacture_name:
                        existing_new_manufacture = Manufacture.query.get(new_manufacture_name)
                        if not existing_new_manufacture:
                            manufacture_address = data.get('manufacture_address', '').strip()
                            if not manufacture_address:
                                return jsonify({'error': f'生产厂家 "{new_manufacture_name}" 不存在于系统中，请填写厂家地址！'}), 400
                            
                            # 创建新的生产厂家记录
                            new_manufacture = Manufacture(
                                manufacture_name=new_manufacture_name,
                                address=manufacture_address
                            )
                            db.session.add(new_manufacture)
                    
                    existing_medicine.manufacture_name = new_manufacture_name
                    
                # 只有在提供了新日期的情况下才更新日期
                if data.get('manufacture_date'):
                    try:
                        manufacture_date = datetime.datetime.strptime(data['manufacture_date'], '%Y-%m-%d').date()
                        existing_medicine.manufacture_date = manufacture_date
                    except ValueError:
                        return jsonify({'error': '生产日期格式不正确！'}), 400
                
                if data.get('expiry_date'):
                    try:
                        expiry_date = datetime.datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
                        existing_medicine.expiry_date = expiry_date
                    except ValueError:
                        return jsonify({'error': '过期日期格式不正确！'}), 400
                
                if data.get('price'):
                    existing_medicine.price = float(data.get('price', 0.0))
                
                if data.get('cabinet_id'):
                    existing_medicine.cabinet_id = int(data.get('cabinet_id'))                
                # 更新数量
                existing_medicine.remaining_quantity = new_quantity
                  # 确保药品类型记录存在
                if medicine_type == 'OTC':
                    from app.models import OTC
                    otc_record = OTC.query.filter_by(national_code=data['national_code']).first()
                    if not otc_record:
                        otc_record = OTC(national_code=data['national_code'], direction=data.get('direction', ''))
                        db.session.add(otc_record)
                elif medicine_type == 'Prescription':
                    from app.models import PrescriptionMedicine
                    prescription_record = PrescriptionMedicine.query.filter_by(national_code=data['national_code']).first()
                    if not prescription_record:
                        # 使用药品的生产日期
                        medicine_manufacture_date = existing_medicine.manufacture_date
                        if data.get('manufacture_date'):
                            try:
                                medicine_manufacture_date = datetime.datetime.strptime(data['manufacture_date'], '%Y-%m-%d').date()
                            except ValueError:
                                pass
                        
                        # 处方ID，处方药必须填写处方ID
                        prescription_id = data.get('prescription_id', '').strip()
                        if not prescription_id:
                            return jsonify({'error': '添加处方药时必须填写处方ID！'}), 400
                        
                        # 验证处方ID是否存在
                        existing_prescription = Prescription.query.get(prescription_id)
                        if not existing_prescription:
                            return jsonify({'error': f'处方ID "{prescription_id}" 不存在！请输入有效的处方ID。'}), 400
                        
                        prescription_record = PrescriptionMedicine(
                            national_code=data['national_code'],
                            prescription_id=prescription_id,
                            manufacture_date=medicine_manufacture_date
                        )
                        db.session.add(prescription_record)
                
                db.session.commit()
                return jsonify({
                    'message': f'药品"{existing_medicine.name}"数量已更新！当前数量：{new_quantity}',
                    'updated': True
                })
            else:
                # 药品编码相同但名称不同，返回错误
                return jsonify({'error': f'药品编码已存在，但名称不同！已有药品名称：{existing_medicine.name}'}), 400
        
        # 处理日期字段
        manufacture_date = None
        expiry_date = None
        
        if data.get('manufacture_date'):
            try:
                manufacture_date = datetime.datetime.strptime(data['manufacture_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': '生产日期格式不正确！'}), 400
        
        if data.get('expiry_date'):
            try:
                expiry_date = datetime.datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
            except ValueError:            return jsonify({'error': '过期日期格式不正确！'}), 400
        
        # 创建新药品记录
        new_medicine = Medicine(
            national_code=data['national_code'],
            name=data['name'],
            manufacture_name=data.get('manufacture_name'),
            manufacture_date=manufacture_date,
            expiry_date=expiry_date,
            remaining_quantity=data.get('remaining_quantity', 0),
            price=data.get('price', 0.0),
            cabinet_id=data.get('cabinet_id')
        )
        db.session.add(new_medicine)
          # 根据药品类型创建相应的记录
        if medicine_type == 'OTC':
            from app.models import OTC
            otc_record = OTC(
                national_code=data['national_code'], 
                direction=data.get('direction', ''),
                manufacture_date=manufacture_date  # 添加生产日期
            )
            db.session.add(otc_record)
        elif medicine_type == 'Prescription':
            from app.models import PrescriptionMedicine
            # 处方药必须填写处方ID
            prescription_id = data.get('prescription_id', '').strip()
            if not prescription_id:
                return jsonify({'error': '添加处方药时必须填写处方ID！'}), 400
            
            # 验证处方ID是否存在
            existing_prescription = Prescription.query.get(prescription_id)
            if not existing_prescription:
                return jsonify({'error': f'处方ID "{prescription_id}" 不存在！请输入有效的处方ID。'}), 400
            
            prescription_record = PrescriptionMedicine(
                national_code=data['national_code'],
                prescription_id=prescription_id,
                manufacture_date=manufacture_date
            )
            db.session.add(prescription_record)
        
        db.session.commit()
        return jsonify({'message': '药品添加成功！'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'添加药品时发生错误：{str(e)}'}), 500

# 删除药品
@main.route('/api/delete_medicine/<string:national_code>', methods=['DELETE'])
def api_delete_medicine(national_code):
    try:
        medicine = Medicine.query.get(national_code)
        if not medicine:
            return jsonify({'error': '找不到指定的药品'}), 404

        # 开始事务
        db.session.begin()
        
        try:
            # 检查是否有正在进行的用药记录
            active_administrations = MedicineAdministration.query.filter_by(national_code=national_code).all()
            
            if active_administrations:
                # 检查是否有正在进行的用药
                current_date = datetime.datetime.now()
                has_active_medication = False
                active_users = []
                
                for admin in active_administrations:
                    # 获取用户信息
                    member = Member.query.get(admin.security_id)
                    user_name = member.name if member else admin.security_id
                    
                    if admin.lasting_time == '长期':
                        has_active_medication = True
                        active_users.append(f"{user_name} (长期用药)")
                    elif admin.start_time and admin.lasting_time:
                        try:
                            days_str = admin.lasting_time.replace('天', '')
                            days = int(days_str)
                            if admin.start_time + datetime.timedelta(days=days) >= current_date:
                                has_active_medication = True
                                active_users.append(f"{user_name} ({admin.lasting_time})")
                        except (ValueError, AttributeError):
                            continue
                
                if has_active_medication:
                    db.session.rollback()
                    return jsonify({
                        'error': f'该药品正在被使用中，无法删除！\n正在使用的用户：{", ".join(active_users)}\n请先停止相关用药记录。'
                    }), 400
            
            # 删除相关的子表记录
            # 1. 删除 OTC 记录
            OTC.query.filter_by(national_code=national_code).delete()
            
            # 2. 删除 PrescriptionMedicine 记录
            PrescriptionMedicine.query.filter_by(national_code=national_code).delete()
            
            # 3. 删除 MedicineAdministration 记录（历史记录）
            MedicineAdministration.query.filter_by(national_code=national_code).delete()
            
            # 4. 最后删除主表记录
            db.session.delete(medicine)
            
            # 提交事务
            db.session.commit()
            
            return jsonify({'message': f'药品"{medicine.name}"已成功删除！'})
            
        except Exception as e:
            # 发生错误时回滚事务
            db.session.rollback()
            raise e
            
    except Exception as e:
        return jsonify({'error': f'删除操作失败：{str(e)}'}), 500

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

# 添加初始化数据库数据的接口
@main.route('/api/init_data', methods=['POST'])
def init_data():
    try:
        # 检查是否已有药箱数据
        existing_cabinets = MedicineCabinet.query.count()
        if existing_cabinets == 0:
            # 添加默认药箱位置
            default_cabinets = [
                MedicineCabinet(cabinet_id=1, location='客厅药箱'),
                MedicineCabinet(cabinet_id=2, location='卧室药箱'),
                MedicineCabinet(cabinet_id=3, location='厨房药箱'),
                MedicineCabinet(cabinet_id=4, location='卫生间药箱')
            ]
            
            for cabinet in default_cabinets:
                db.session.add(cabinet)
        
        db.session.commit()
        return jsonify({'message': '数据初始化成功！'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'数据初始化失败：{str(e)}'}), 500

# 删除药品（按数量删除，带事务处理）
@main.route('/api/remove_medicine', methods=['POST'])
def api_remove_medicine():
    try:
        data = request.json
        national_code = data.get('national_code')
        quantity_to_remove = data.get('quantity_to_remove', 0)
        
        if not national_code:
            return jsonify({'error': '药品编码不能为空！'}), 400
        
        if quantity_to_remove <= 0:
            return jsonify({'error': '删除数量必须大于0！'}), 400
        
        # 开始事务
        db.session.begin()
        
        try:
            # 查找药品记录（加锁防止并发修改）
            medicine = Medicine.query.filter_by(national_code=national_code).with_for_update().first()
            
            if not medicine:
                db.session.rollback()
                return jsonify({'error': '找不到指定的药品！'}), 404
            
            # 检查当前数量
            if medicine.remaining_quantity < quantity_to_remove:
                db.session.rollback()
                return jsonify({'error': f'删除数量({quantity_to_remove})超过当前剩余数量({medicine.remaining_quantity})！'}), 400
              # 计算删除后的数量
            new_quantity = medicine.remaining_quantity - quantity_to_remove
            
            if new_quantity == 0:
                # 数量为0时，需要检查是否有相关的用药记录
                active_administrations = MedicineAdministration.query.filter_by(national_code=national_code).all()
                
                if active_administrations:
                    # 检查是否有正在进行的用药
                    current_date = datetime.datetime.now()
                    has_active_medication = False
                    
                    for admin in active_administrations:
                        if admin.lasting_time == '长期':
                            has_active_medication = True
                            break
                        elif admin.start_time and admin.lasting_time:
                            try:
                                days_str = admin.lasting_time.replace('天', '')
                                days = int(days_str)
                                if admin.start_time + datetime.timedelta(days=days) >= current_date:
                                    has_active_medication = True
                                    break
                            except (ValueError, AttributeError):
                                continue
                    
                    if has_active_medication:
                        db.session.rollback()
                        return jsonify({'error': '该药品正在被使用中，无法完全删除！请先停止相关用药记录。'}), 400
                
                # 删除相关的子表记录，然后删除主表记录
                # 1. 删除 OTC 记录
                OTC.query.filter_by(national_code=national_code).delete()
                
                # 2. 删除 PrescriptionMedicine 记录
                PrescriptionMedicine.query.filter_by(national_code=national_code).delete()
                
                # 3. 删除 MedicineAdministration 记录（历史记录）
                MedicineAdministration.query.filter_by(national_code=national_code).delete()
                
                # 4. 最后删除主表记录
                db.session.delete(medicine)
                message = f'药品"{medicine.name}"已完全删除！'
            else:
                # 更新数量
                medicine.remaining_quantity = new_quantity
                message = f'成功从"{medicine.name}"中删除 {quantity_to_remove} 个，剩余数量：{new_quantity}'
            
            # 记录操作日志（可选，这里简化处理）
            print(f"药品删除操作：{national_code}, 删除数量：{quantity_to_remove}, 操作时间：{datetime.datetime.now()}")
            
            # 提交事务
            db.session.commit()
            
            return jsonify({'message': message})
            
        except Exception as e:
            # 发生错误时回滚事务
            db.session.rollback()
            raise e
            
    except Exception as e:
        return jsonify({'error': f'删除操作失败：{str(e)}'}), 500

# 获取药品的使用状态信息
@main.route('/api/medicine_usage/<string:national_code>', methods=['GET'])
def get_medicine_usage(national_code):
    try:
        medicine = Medicine.query.get(national_code)
        if not medicine:
            return jsonify({'error': 'Medicine not found'}), 404
        
        # 查询该药品的使用记录
        administrations = MedicineAdministration.query.filter_by(national_code=national_code).all()
        current_date = datetime.datetime.now()
        
        active_users = []
        historical_count = 0
        
        for admin in administrations:
            member = Member.query.get(admin.security_id)
            if not member:
                continue
                
            is_active = False
            if admin.lasting_time == '长期':
                is_active = True
            elif admin.start_time and admin.lasting_time:
                try:
                    days_str = admin.lasting_time.replace('天', '')
                    days = int(days_str)
                    if admin.start_time + datetime.timedelta(days=days) >= current_date:
                        is_active = True
                except (ValueError, AttributeError):
                    pass
            
            if is_active:
                active_users.append({
                    'name': member.name,
                    'security_id': member.security_id,
                    'dosage': admin.dosage,
                    'start_time': admin.start_time.strftime('%Y-%m-%d') if admin.start_time else '未知'
                })
            else:
                historical_count += 1
        
        usage_info = {
            'medicine_name': medicine.name,
            'remaining_quantity': medicine.remaining_quantity,
            'active_users': active_users,
            'historical_usage_count': historical_count,
            'can_be_deleted': len(active_users) == 0
        }
        
        return jsonify(usage_info)
        
    except Exception as e:
        return jsonify({'error': f'获取药品使用信息失败：{str(e)}'}), 500

# 专门用于添加新药品（不更新已有药品）
@main.route('/api/add_new_medicine', methods=['POST'])
def api_add_new_medicine():
    try:
        data = request.json
        
        # 验证药品类型
        medicine_type = data.get('medicine_type')
        if not medicine_type or medicine_type not in ['OTC', 'Prescription']:
            return jsonify({'error': '无效的药品类型！必须是 OTC 或 Prescription'}), 400
        
        # 检查药品是否已存在
        existing_medicine = Medicine.query.get(data['national_code'])
        if existing_medicine:
            return jsonify({'error': f'药品编码已存在！请使用"补充药品"功能更新数量。'}), 400
        
        # 处理生产商信息
        manufacture_name = data.get('manufacture_name')
        if manufacture_name:
            # 检查生产商是否存在
            existing_manufacture = Manufacture.query.get(manufacture_name)
            if not existing_manufacture:
                # 如果生产商不存在，则创建新的生产商记录
                new_manufacture = Manufacture(
                    manufacture_name=manufacture_name,
                    address=data.get('manufacture_address', '')  # 获取地址信息，如果没有则为空字符串
                )
                db.session.add(new_manufacture)
                # 暂时不提交，和药品一起提交，保证事务的原子性
        
        # 处理日期字段
        manufacture_date = None
        expiry_date = None
        
        if data.get('manufacture_date'):
            try:
                manufacture_date = datetime.datetime.strptime(data['manufacture_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': '生产日期格式不正确！'}), 400
        
        if data.get('expiry_date'):
            try:
                expiry_date = datetime.datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': '过期日期格式不正确！'}), 400
        
        # 创建新药品记录
        new_medicine = Medicine(
            national_code=data['national_code'],
            name=data['name'],
            manufacture_name=manufacture_name,
            manufacture_date=manufacture_date,
            expiry_date=expiry_date,
            remaining_quantity=data.get('remaining_quantity', 0),
            price=data.get('price', 0.0),
            cabinet_id=data.get('cabinet_id')
        )
        
        db.session.add(new_medicine)
          # 根据药品类型创建相应的记录
        if medicine_type == 'OTC':
            otc_record = OTC(
                national_code=data['national_code'], 
                direction=data.get('direction', ''),
                manufacture_date=manufacture_date
            )
            db.session.add(otc_record)
        elif medicine_type == 'Prescription':
            # 处理处方ID，如果为空则设为None
            prescription_id = data.get('prescription_id', '').strip()
            if not prescription_id:
                prescription_id = None
            else:
                # 验证处方ID是否存在
                existing_prescription = Prescription.query.get(prescription_id)
                if not existing_prescription:
                    return jsonify({'error': f'处方ID "{prescription_id}" 不存在！请输入有效的处方ID或留空。'}), 400
            
            prescription_record = PrescriptionMedicine(
                national_code=data['national_code'],
                prescription_id=prescription_id,
                manufacture_date=manufacture_date
            )
            db.session.add(prescription_record)
        
        db.session.commit()
        
        # 根据是否创建了新的生产商，返回不同的成功消息
        if manufacture_name and not existing_manufacture:
            return jsonify({'message': '新药品和生产商添加成功！'})
        else:
            return jsonify({'message': '新药品添加成功！'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'添加新药品时发生错误：{str(e)}'}), 500

# 专门用于补充药品数量
@main.route('/api/refill_medicine', methods=['POST'])
def api_refill_medicine():
    try:
        data = request.json
        national_code = data.get('national_code')
        quantity_to_add = data.get('quantity_to_add', 0)
        
        if not national_code:
            return jsonify({'error': '药品编码不能为空！'}), 400
        
        if quantity_to_add <= 0:
            return jsonify({'error': '补充数量必须大于0！'}), 400
        
        # 开始事务
        db.session.begin()
        
        try:
            # 查找药品记录（加锁防止并发修改）
            medicine = Medicine.query.filter_by(national_code=national_code).with_for_update().first()
            
            if not medicine:
                db.session.rollback()
                return jsonify({'error': '找不到指定的药品！'}), 404
            
            # 更新数量
            new_quantity = medicine.remaining_quantity + quantity_to_add
            medicine.remaining_quantity = new_quantity
            
            db.session.commit()
            return jsonify({'message': f'成功为"{medicine.name}"补充 {quantity_to_add} 个，当前总数量：{new_quantity}'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'补充药品时发生错误：{str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'处理请求时发生错误：{str(e)}'}), 500

# 获取即将过期的药品（30天内）
@main.route('/api/expiring_medicines', methods=['GET'])
def get_expiring_medicines():
    try:
        current_date = datetime.datetime.now().date()
        expiry_threshold = current_date + datetime.timedelta(days=30)
        
        # 查询所有有过期日期且在30天内过期的药品
        expiring_medicines = Medicine.query.filter(
            Medicine.expiry_date.isnot(None),
            Medicine.expiry_date <= expiry_threshold,
            Medicine.expiry_date >= current_date,
            Medicine.remaining_quantity > 0  # 只显示还有剩余的药品
        ).all()
        
        result = []
        for medicine in expiring_medicines:
            days_until_expiry = (medicine.expiry_date - current_date).days
            
            cabinet = MedicineCabinet.query.get(medicine.cabinet_id) if medicine.cabinet_id else None
            
            result.append({
                'national_code': medicine.national_code,
                'name': medicine.name,
                'expiry_date': medicine.expiry_date.strftime('%Y-%m-%d'),
                'days_until_expiry': days_until_expiry,
                'remaining_quantity': medicine.remaining_quantity,
                'cabinet_location': cabinet.location if cabinet else '未知'
            })
        
        # 按照过期时间排序，最接近过期的排在前面
        result.sort(key=lambda x: x['days_until_expiry'])
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'获取即将过期药品失败：{str(e)}'}), 500

# 获取库存不足的药品（少于3个）
@main.route('/api/low_stock_medicines', methods=['GET'])
def get_low_stock_medicines():
    try:
        # 查询所有库存少于3的药品
        low_stock_medicines = Medicine.query.filter(
            Medicine.remaining_quantity < 3,
            Medicine.remaining_quantity > 0  # 只显示还有剩余的药品
        ).all()
        
        result = []
        for medicine in low_stock_medicines:
            cabinet = MedicineCabinet.query.get(medicine.cabinet_id) if medicine.cabinet_id else None
            
            result.append({
                'national_code': medicine.national_code,
                'name': medicine.name,
                'remaining_quantity': medicine.remaining_quantity,
                'cabinet_location': cabinet.location if cabinet else '未知'
            })
        
        # 按照剩余数量排序，最少的排在前面        
        result.sort(key=lambda x: x['remaining_quantity'])
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'获取库存不足药品失败：{str(e)}'}), 500

# 获取已过期的药品
@main.route('/api/expired_medicines', methods=['GET'])
def get_expired_medicines():
    try:
        current_date = datetime.datetime.now().date()
        
        # 查询所有有过期日期且已经过期的药品
        expired_medicines = Medicine.query.filter(
            Medicine.expiry_date.isnot(None),
            Medicine.expiry_date < current_date,
            Medicine.remaining_quantity > 0  # 只显示还有剩余的药品
        ).all()
        
        result = []
        for medicine in expired_medicines:
            days_expired = (current_date - medicine.expiry_date).days
            
            cabinet = MedicineCabinet.query.get(medicine.cabinet_id) if medicine.cabinet_id else None
            
            result.append({
                'national_code': medicine.national_code,
                'name': medicine.name,
                'expiry_date': medicine.expiry_date.strftime('%Y-%m-%d'),
                'days_expired': days_expired,
                'remaining_quantity': medicine.remaining_quantity,
                'cabinet_location': cabinet.location if cabinet else '未知'
            })
        
        # 按照过期时间排序，最近过期的排在前面
        result.sort(key=lambda x: x['days_expired'])
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'获取已过期药品失败：{str(e)}'}), 500

# 修改成员信息（使用存储过程）
@main.route('/api/update_member', methods=['PUT'])
def api_update_member():
    try:
        data = request.json
        old_security_id = data.get('old_security_id')
        new_security_id = data.get('new_security_id')
        
        # 验证必填字段
        if not old_security_id or not new_security_id:
            return jsonify({'error': '原用户ID和新用户ID不能为空！'}), 400
        
        # 验证其他必填字段
        required_fields = ['name', 'gender', 'age', 'weight', 'height']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'字段 {field} 不能为空！'}), 400
        
        # 调用存储过程
        try:
            result = db.session.execute(
                text("""CALL UpdateMemberSecurityId(:old_security_id, :new_security_id, :name, :gender, 
                   :age, :weight, :height, :underlying_disease, :allergen)"""), # 使用 text() 包装SQL字符串
                {
                    'old_security_id': old_security_id,
                    'new_security_id': new_security_id,
                    'name': data.get('name'),
                    'gender': data.get('gender'),
                    'age': data.get('age'),
                    'weight': data.get('weight'),
                    'height': data.get('height'),
                    'underlying_disease': data.get('underlying_disease', ''),
                    'allergen': data.get('allergen', '')
                }
            )
            
            # 获取存储过程的返回结果
            result_data = result.fetchone()
            if result_data and result_data[0] == 'success':
                db.session.commit()
                return jsonify({'message': result_data[1]})
            else:
                db.session.rollback()
                return jsonify({'error': '更新失败'}), 500
                
        except Exception as e:
            db.session.rollback()
            error_msg = str(e)
            if 'SQLSTATE' in error_msg:
                # 提取存储过程中的自定义错误信息
                if '原用户ID不存在' in error_msg:
                    return jsonify({'error': '原用户ID不存在'}), 404
                elif '新用户ID已存在' in error_msg:
                    return jsonify({'error': '新用户ID已存在'}), 400
            
            return jsonify({'error': f'更新成员信息时发生错误：{error_msg}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'处理请求时发生错误：{str(e)}'}), 500

# 获取成员详细信息（用于编辑页面）
@main.route('/api/member_details_for_edit/<string:security_id>', methods=['GET'])
def get_member_details_for_edit(security_id):
    try:
        member = Member.query.get(security_id)
        if not member:
            return jsonify({'error': '找不到指定的成员'}), 404
        
        # 检查该成员是否有关联的用药记录
        medicine_count = MedicineAdministration.query.filter_by(security_id=security_id).count()
        prescription_count = Prescription.query.filter_by(security_id=security_id).count()
        
        member_data = {
            'security_id': member.security_id,
            'name': member.name,
            'gender': member.gender,
            'age': member.age,
            'weight': member.weight,
            'height': member.height,
            'underlying_disease': member.underlying_disease or '',
            'allergen': member.allergen or '',
            'has_medicine_records': medicine_count > 0,
            'has_prescription_records': prescription_count > 0,
            'total_related_records': medicine_count + prescription_count
        }
        
        return jsonify(member_data)
        
    except Exception as e:
        return jsonify({'error': f'获取成员信息时发生错误：{str(e)}'}), 500

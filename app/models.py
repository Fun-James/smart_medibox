from app import db

class OTC(db.Model):
    __tablename__ = 'OTC'
    national_code = db.Column(db.String(256), db.ForeignKey('medicine.national_code'), primary_key=True)
    direction = db.Column(db.String(1024))


class Manufacture(db.Model):
    __tablename__ = 'manufacture'
    manufacture_name = db.Column(db.String(256), primary_key=True)
    address = db.Column(db.String(256))


class MedicineCabinet(db.Model):
    __tablename__ = 'medicine_cabinet'
    cabinet_id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(256))


class Medicine(db.Model):
    __tablename__ = 'medicine'
    national_code = db.Column(db.String(256), primary_key=True)
    prescription_id = db.Column(db.String(256), db.ForeignKey('prescription.prescription_id'))
    cabinet_id = db.Column(db.Integer, db.ForeignKey('medicine_cabinet.cabinet_id'))
    manufacture_name = db.Column(db.String(256), db.ForeignKey('manufacture.manufacture_name'))
    name = db.Column(db.String(256))
    manufacture_date = db.Column(db.Date)
    remaining_quantity = db.Column(db.SmallInteger)
    expiry_date = db.Column(db.Date)  # 修正拼写错误：expiry_data -> expiry_date
    price = db.Column(db.Float)

    otc_info = db.relationship('OTC', uselist=False, backref='medicine')


class Member(db.Model):
    __tablename__ = 'member'  # 修正表名拼写错误
    security_id = db.Column(db.String(256), primary_key=True)
    name = db.Column(db.String(256))
    gender = db.Column(db.String(1))
    age = db.Column(db.SmallInteger)
    weight = db.Column(db.Float)
    height = db.Column(db.Float)
    underlying_disease = db.Column(db.String(256))
    allergen = db.Column(db.String(256))


class MedicineAdministration(db.Model):
    __tablename__ = 'medicine_administration'
    security_id = db.Column(db.String(256), db.ForeignKey('member.security_id'), primary_key=True)
    national_code = db.Column(db.String(256), db.ForeignKey('medicine.national_code'), primary_key=True)
    dosage = db.Column(db.String(256))
    start_time = db.Column(db.DateTime)
    lasting_time = db.Column(db.String(256))
    manufacture_date = db.Column(db.Date)  # 添加manufacture_date字段


class Prescription(db.Model):
    __tablename__ = 'prescription'
    prescription_id = db.Column(db.String(256), primary_key=True)
    time = db.Column(db.Date)
    doctor = db.Column(db.String(256))


class Prescribe(db.Model):
    __tablename__ = 'prescribe'
    security_id = db.Column(db.String(256), db.ForeignKey('member.security_id'), primary_key=True)
    prescription_id = db.Column(db.String(256), db.ForeignKey('prescription.prescription_id'), primary_key=True)


class PrescriptionMedicine(db.Model):
    __tablename__ = 'prescription_medicine'
    national_code = db.Column(db.String(256), db.ForeignKey('medicine.national_code'), primary_key=True)
    prescription_id = db.Column(db.String(256), db.ForeignKey('prescription.prescription_id'))

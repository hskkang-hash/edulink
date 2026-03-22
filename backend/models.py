"""
EduLink Database Models for Flask-Migrate
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class User(db.Model):
    """사용자 모델"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='instructor')
    organization = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 관계
    postings = db.relationship('Posting', backref='owner', lazy=True)
    applications = db.relationship('Application', lazy=True)
    tax_profiles = db.relationship('TaxProfile', lazy=True)
    tax_claims = db.relationship('TaxClaim', lazy=True)
    tax_events = db.relationship('TaxEvent', lazy=True)
    cms_charges = db.relationship('CMSCharge', lazy=True)

class Posting(db.Model):
    """모집공고 모델"""
    __tablename__ = 'postings'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255))
    subject = db.Column(db.String(255))
    region = db.Column(db.String(100))
    rate = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # 관계
    applications = db.relationship('Application', lazy=True)

class Application(db.Model):
    """지원 모델"""
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    posting_id = db.Column(db.Integer, db.ForeignKey('postings.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class TaxProfile(db.Model):
    """세금 프로필 모델"""
    __tablename__ = 'tax_profiles'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    full_name = db.Column(db.String(255))
    business_number = db.Column(db.String(50))
    bank_name = db.Column(db.String(100))
    bank_account_masked = db.Column(db.String(100))
    consent_withholding = db.Column(db.Integer, default=1)
    provider = db.Column(db.String(100), default='mock-hometax-sam')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))

class TaxClaim(db.Model):
    """세금 청구 모델"""
    __tablename__ = 'tax_claims'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    claim_code = db.Column(db.String(100), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tax_year = db.Column(db.Integer)
    gross_income = db.Column(db.Integer, default=0)
    withholding_amount = db.Column(db.Integer, default=0)
    estimated_refund = db.Column(db.Integer, default=0)
    service_fee_rate = db.Column(db.Float, default=0.22)
    service_fee_amount = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='draft')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))

class TaxEvent(db.Model):
    """세금 이벤트 모델"""
    __tablename__ = 'tax_events'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    claim_code = db.Column(db.String(100))
    event_type = db.Column(db.String(100))
    event_payload = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class CMSCharge(db.Model):
    """CMS 청구 모델"""
    __tablename__ = 'cms_charges'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    charge_code = db.Column(db.String(100), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    claim_code = db.Column(db.String(100))
    amount = db.Column(db.Integer)
    status = db.Column(db.String(50), default='requested')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    processed_at = db.Column(db.DateTime)

class NetworkLink(db.Model):
    """네트워크 링크 모델"""
    __tablename__ = 'network_links'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    sponsor_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))

class NetworkSale(db.Model):
    """네트워크 판매 모델"""
    __tablename__ = 'network_sales'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    seller_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    base_price = db.Column(db.Integer)
    pv = db.Column(db.Integer)
    bv = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

# EduLink Database Migrations Guide

## 개요
EduLink는 Flask-Migrate와 Alembic을 사용하여 데이터베이스 스키마 버전 관리를 수행합니다.

## 마이그레이션 구조
```
backend/
├── migrations/
│   ├── alembic.ini           # Alembic 설정 파일
│   ├── env.py                # 마이그레이션 환경 설정
│   ├── script.py.mako        # 마이그레이션 템플릿
│   └── versions/             # 마이그레이션 파일 저장소
│       └── c175a03cef01_initial_migration_create_all_tables.py
├── models.py                  # SQLAlchemy ORM 모델
├── create_migration.py         # 마이그레이션 생성 스크립트
└── app_jwt.py                 # Flask 애플리케이션
```

## 주요 파일 설명

### models.py
SQLAlchemy ORM 모델 정의:
- `User`: 사용자
- `Posting`: 모집공고
- `Application`: 지원
- `TaxProfile`: 세금 프로필
- `TaxClaim`: 세금 청구
- `TaxEvent`: 세금 이벤트
- `CMSCharge`: CMS 청구
- `NetworkLink`: 네트워크 링크
- `NetworkSale`: 네트워크 판매

### migrations/versions/
각 마이그레이션 파일은 다음을 포함합니다:
- `upgrade()`: 마이그레이션 적용
- `downgrade()`: 마이그레이션 되돌리기

## 명령어

### 1. 마이그레이션 생성 (스키마 변경 시)
```bash
cd backend

# 새로운 마이그레이션 생성 (자동으로 변경 사항 감지)
python create_migration.py

# 또는 수동으로 생성
python -c "
from flask import Flask
from flask_migrate import Migrate
from models import db
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./edulink.db'
db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    from alembic.config import Config
    from alembic import command
    cfg = Config('migrations/alembic.ini')
    cfg.set_main_option('sqlalchemy.url', 'sqlite:///./edulink.db')
    command.revision(cfg, autogenerate=True, message='Your message here')
"
```

### 2. 마이그레이션 적용 (데이터베이스 업데이트)
```bash
# 최신 버전으로 업그레이드
flask db upgrade

# 특정 버전으로 이동
flask db upgrade <revision_number>
```

### 3. 마이그레이션 되돌리기
```bash
# 이전 버전으로 다운그레이드
flask db downgrade

# 특정 버전으로 이동
flask db downgrade <revision_number>
```

### 4. 마이그레이션 히스토리 확인
```bash
flask db history
```

### 5. 현재 버전 확인
```bash
flask db current
```

## Docker에서의 마이그레이션

### docker-compose.yml 설정
```yaml
backend:
  build:
    context: ../backend
    dockerfile: Dockerfile
  environment:
    DATABASE_URL: postgresql://user:password@db:5432/edulink_db
  command: sh -c "flask db upgrade && python app_jwt.py"
```

### 수동 마이그레이션 실행 (Docker)
```bash
# 컨테이너 내에서 마이그레이션 실행
docker-compose exec backend flask db upgrade

# 또는 일회성 컨테이너에서 실행
docker-compose run --rm backend flask db upgrade
```

## 마이그레이션 작성 팁

### 1. 새 테이블 추가
```python
# models.py에 모델 추가
class NewTable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))

# 마이그레이션 생성
python create_migration.py "Add new table"
```

### 2. 컬럼 추가
```python
# models.py에서 기존 모델에 컬럼 추가
class User(db.Model):
    # ... 기존 컬럼들 ...
    new_column = db.Column(db.String(255))

# 마이그레이션 생성
python create_migration.py "Add new_column to users"
```

### 3. 인덱스 추가
```python
# migrations/versions/xxx.py에 직접 작성
def upgrade():
    op.create_index('ix_users_email', 'users', ['email'])

def downgrade():
    op.drop_index('ix_users_email', 'users')
```

## 마이그레이션 파일 구조

```python
"""Initial migration: create all tables

Revision ID: c175a03cef01
Revises: 
Create Date: 2026-03-22 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# Python 버전 (PEP 440)
revision = 'c175a03cef01'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 마이그레이션 적용 시 실행
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

def downgrade():
    # 마이그레이션 되돌릴 때 실행
    op.drop_table('users')
```

## 트러블슈팅

### 문제: "현재 head revision과 업그레이드 상태가 불일치"
```bash
# 현재 상태 확인
flask db current

# 히스토리 확인
flask db history

# 강제로 특정 버전으로 표시 (신중히 사용)
flask db stamp <revision_number>
```

### 문제: 마이그레이션이 감지되지 않음
```bash
# models.py를 임포트하는지 확인
python -c "from models import db, User, Posting"

# 마이그레이션 파일의 imports 확인
# migrations/env.py에서 from models import * 확인
```

### 문제: SQLite 락 오류
```bash
# 파일 모드 마이그레이션인 경우 timeout 증가
# config에서 timeout 설정 추가
# connections에서 idle timeout 감소
```

## 프로덕션 배포 체크리스트
- [ ] 로컬에서 마이그레이션 테스트
- [ ] 마이그레이션 파일이 git에 커밋됨
- [ ] models.py 변경사항 확인
- [ ] 백업 생성 (프로덕션 DB)
- [ ] 마이그레이션 실행 (docker-compose run --rm backend flask db upgrade)
- [ ] 데이터베이스 무결성 확인
- [ ] 애플리케이션 재시작

## 참고 자료
- Flask-Migrate 문서: https://flask-migrate.readthedocs.io/
- Alembic 문서: https://alembic.sqlalchemy.org/
- SQLAlchemy ORM: https://docs.sqlalchemy.org/

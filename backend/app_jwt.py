from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sqlalchemy import create_engine, text
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import os
from pathlib import Path
import uuid
import json
from email_adapter import get_email_adapter
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'super-secret-key')
app.config['EXPOSE_RESET_TOKEN_IN_RESPONSE'] = os.getenv('EXPOSE_RESET_TOKEN_IN_RESPONSE', 'false').lower() == 'true'
app.config['EMAIL_ADAPTER_TYPE'] = os.getenv('EMAIL_ADAPTER_TYPE', 'mock')

# ?대찓???대뙌??珥덇린??
email_adapter = get_email_adapter(app.config['EMAIL_ADAPTER_TYPE'])

# ===== Prometheus 硫뷀듃由??뺤쓽 =====
# HTTP ?붿껌 移댁슫??
http_requests_total = Counter(
    'edulinks_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# HTTP ?붿껌 吏???쒓컙
http_request_duration_seconds = Histogram(
    'edulinks_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# ?몄쬆 ?쒕룄/?깃났
auth_attempts_total = Counter(
    'edulinks_auth_attempts_total',
    'Total authentication attempts',
    ['type', 'result']
)

# 鍮꾨?踰덊샇 由ъ뀑 ?붿껌
password_reset_attempts = Counter(
    'edulinks_password_reset_attempts_total',
    'Total password reset attempts',
    ['result']
)

# ?쒖꽦 ?ъ슜???몄뀡
active_sessions = Gauge(
    'edulinks_active_sessions',
    'Number of active user sessions'
)

# ?곗씠?곕쿋?댁뒪 ?묒뾽 ?쒓컙
db_operation_duration = Histogram(
    'edulinks_db_operation_duration_seconds',
    'Database operation duration',
    ['operation']
)

# ?붿껌 ?꾪썑 泥섎━
@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        # 誘쇨컧??寃쎈줈 ?쒖쇅
        endpoint = request.endpoint or 'unknown'
        if endpoint not in ['metrics']:
            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)
            
            http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status=response.status_code
            ).inc()
    
    return response
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Use DATABASE_URL from environment or fallback to default
database_url = os.getenv('DATABASE_URL', 'sqlite:///./edulinks.db')
engine = create_engine(database_url, echo=False)

# DB init
with engine.connect() as conn:
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'instructor',
            organization TEXT,
            created_at TEXT
        )
    '''))
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS postings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            subject TEXT,
            region TEXT,
            rate INTEGER,
            created_at TEXT,
            owner_id INTEGER
        )
    '''))
    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            posting_id INTEGER,
            student_id INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )
    '''))

    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS tax_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            full_name TEXT,
            business_number TEXT,
            bank_name TEXT,
            bank_account_masked TEXT,
            consent_withholding INTEGER DEFAULT 1,
            provider TEXT DEFAULT 'mock-hometax-sam',
            created_at TEXT,
            updated_at TEXT
        )
    '''))

    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS tax_claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_code TEXT UNIQUE,
            user_id INTEGER,
            tax_year INTEGER,
            gross_income INTEGER DEFAULT 0,
            withholding_amount INTEGER DEFAULT 0,
            estimated_refund INTEGER DEFAULT 0,
            service_fee_rate REAL DEFAULT 0.22,
            service_fee_amount INTEGER DEFAULT 0,
            status TEXT DEFAULT 'draft',
            created_at TEXT,
            updated_at TEXT
        )
    '''))

    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS tax_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            claim_code TEXT,
            event_type TEXT,
            event_payload TEXT,
            created_at TEXT
        )
    '''))

    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS cms_charges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            charge_code TEXT UNIQUE,
            user_id INTEGER,
            claim_code TEXT,
            amount INTEGER,
            status TEXT DEFAULT 'requested',
            created_at TEXT,
            processed_at TEXT
        )
    '''))

    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS network_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            sponsor_user_id INTEGER,
            created_at TEXT,
            updated_at TEXT
        )
    '''))

    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS network_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_user_id INTEGER,
            base_price INTEGER,
            pv INTEGER,
            bv INTEGER,
            created_at TEXT
        )
    '''))

    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS network_bonus_allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER,
            beneficiary_user_id INTEGER,
            referral_level INTEGER,
            applied_rate REAL,
            amount_raw INTEGER,
            amount_paid INTEGER,
            scale_factor REAL,
            created_at TEXT
        )
    '''))

    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS network_bonus_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT,
            min_pv INTEGER,
            rate REAL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    '''))

    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS network_rule_audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_user_id INTEGER,
            rules_json TEXT,
            created_at TEXT
        )
    '''))

    rules_count_row = conn.execute(text('SELECT COUNT(*) AS count FROM network_bonus_rules')).mappings().first()
    if int(rules_count_row['count'] or 0) == 0:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            text('''
                INSERT INTO network_bonus_rules (label, min_pv, rate, is_active, created_at, updated_at)
                VALUES
                    ('L3', 10000000, 0.21, 1, :now, :now),
                    ('L2', 5000000, 0.06, 1, :now, :now),
                    ('L1', 200000, 0.03, 1, :now, :now)
            '''),
            {'now': now}
        )

    posting_cols = [row[1] for row in conn.execute(text('PRAGMA table_info(postings)')).fetchall()]
    if 'owner_id' not in posting_cols:
        conn.execute(text('ALTER TABLE postings ADD COLUMN owner_id INTEGER'))
    if 'created_at' not in posting_cols:
        conn.execute(text('ALTER TABLE postings ADD COLUMN created_at TEXT'))

    user_cols = [row[1] for row in conn.execute(text('PRAGMA table_info(users)')).fetchall()]
    if 'organization' not in user_cols:
        conn.execute(text('ALTER TABLE users ADD COLUMN organization TEXT'))
    if 'created_at' not in user_cols:
        conn.execute(text('ALTER TABLE users ADD COLUMN created_at TEXT'))

    app_cols = [row[1] for row in conn.execute(text('PRAGMA table_info(applications)')).fetchall()]
    if 'student_id' not in app_cols and 'instructor_id' in app_cols:
        conn.execute(text('ALTER TABLE applications ADD COLUMN student_id INTEGER'))
    if 'created_at' not in app_cols:
        conn.execute(text('ALTER TABLE applications ADD COLUMN created_at TEXT'))

# helper

def create_token(payload):
    return serializer.dumps(payload)


def verify_token(token):
    try:
        data = serializer.loads(token, max_age=60 * 60 * 24)
        return data
    except (BadSignature, SignatureExpired):
        return None


def looks_like_password_hash(value):
    if not isinstance(value, str):
        return False
    return value.startswith('scrypt:') or value.startswith('pbkdf2:')


def verify_password(stored_password, provided_password):
    if not isinstance(stored_password, str) or not isinstance(provided_password, str):
        return False, False

    if looks_like_password_hash(stored_password):
        try:
            return check_password_hash(stored_password, provided_password), False
        except ValueError:
            return False, False

    # Legacy plaintext support for backward compatibility.
    is_match = stored_password == provided_password
    return is_match, is_match


def validate_password_policy(password):
    if not isinstance(password, str):
        return 'password must be a string'

    if len(password) < 8:
        return 'password must be at least 8 characters'
    if len(password) > 128:
        return 'password must be at most 128 characters'
    if any(ch.isspace() for ch in password):
        return 'password must not contain whitespace'
    if not any(ch.isalpha() for ch in password):
        return 'password must include at least one letter'
    if not any(ch.isdigit() for ch in password):
        return 'password must include at least one number'

    return None


def mask_token(token):
    """
    留덉뒪??泥섎━???좏겙??諛섑솚?⑸땲??
    泥섏쓬 8?먯? 留덉?留?8?먮쭔 ?쒖떆?섍퀬 ?섎㉧吏??***濡??쒖떆?⑸땲??
    ?? 'abc12345***xyz67890'
    """
    if not isinstance(token, str) or len(token) < 16:
        return '***masked***'
    return f"{token[:8]}***{token[-8:]}"


def create_password_reset_token(user_id, email):
    return serializer.dumps({'type': 'password_reset', 'user_id': user_id, 'email': email}, salt='password-reset')


def verify_password_reset_token(token):
    try:
        data = serializer.loads(token, salt='password-reset', max_age=60 * 30)
    except (BadSignature, SignatureExpired):
        return None

    if not isinstance(data, dict):
        return None
    if data.get('type') != 'password_reset':
        return None
    return data


@app.route('/')
def root():
    frontend_dir = Path(__file__).resolve().parent.parent / 'frontend'
    index_file = frontend_dir / 'index.html'
    if index_file.exists():
        return send_from_directory(str(frontend_dir), 'index.html')
    return jsonify({'message': 'EDULINKS API is running'})


@app.route('/health')
def health():
    return jsonify({'message': 'EDULINKS API is running'})


@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'email/password required'}), 400

    email = str(data.get('email', '')).strip()
    password = str(data.get('password', ''))
    if not email or not password:
        return jsonify({'error': 'email/password required'}), 400

    policy_error = validate_password_policy(password)
    if policy_error:
        return jsonify({'error': policy_error}), 400

    hashed_password = generate_password_hash(password)

    with engine.begin() as conn:
        existing = conn.execute(text('SELECT id FROM users WHERE email = :email'), {'email': email}).fetchone()
        if existing:
            return jsonify({'error': 'Email already registered'}), 400
        conn.execute(text('INSERT INTO users (email, password, role, organization, created_at) VALUES (:email,:password,:role,:org,:created_at)'),
                     {'email': email, 'password': hashed_password, 'role': data.get('role', 'instructor'), 'org': data.get('organization', ''), 'created_at': datetime.now(timezone.utc).isoformat()})

    return jsonify({'message': 'registered'}), 201


@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'email/password required'}), 400

    email = str(data.get('email', '')).strip()
    password = str(data.get('password', ''))
    if not email or not password:
        return jsonify({'error': 'email/password required'}), 400

    with engine.connect() as conn:
        user = conn.execute(
            text('SELECT id,email,role,password FROM users WHERE email = :email'),
            {'email': email}
        ).mappings().first()

    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    is_valid, should_upgrade = verify_password(user['password'], password)
    if not is_valid:
        return jsonify({'error': 'Invalid credentials'}), 401

    if should_upgrade:
        with engine.begin() as conn:
            conn.execute(
                text('UPDATE users SET password = :password WHERE id = :id'),
                {'password': generate_password_hash(password), 'id': user['id']}
            )

    token = create_token({'user_id': user['id'], 'email': user['email'], 'role': user['role']})
    return jsonify({'access_token': token, 'token_type': 'bearer', 'user': {'id': user['id'], 'email': user['email'], 'role': user['role']}})


def get_current_user():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    token = auth.split(' ', 1)[1]
    return verify_token(token)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def get_instructor_tax_numbers(user_id, tax_year):
    params = {'owner_id': user_id, 'year': str(tax_year)}
    with engine.connect() as conn:
        row = conn.execute(
            text('''
                SELECT COALESCE(SUM(p.rate), 0) AS gross_income
                FROM applications a
                JOIN postings p ON p.id = a.posting_id
                WHERE p.owner_id = :owner_id
                  AND a.status = 'approved'
                  AND substr(COALESCE(a.created_at, ''), 1, 4) = :year
            '''),
            params
        ).mappings().first()

    gross_income = int(row['gross_income'] or 0)
    withholding_amount = int(round(gross_income * 0.033))
    estimated_refund = int(round(withholding_amount * 0.7))
    return gross_income, withholding_amount, estimated_refund


def log_tax_event(user_id, event_type, payload, claim_code=None):
    with engine.begin() as conn:
        conn.execute(
            text('''
                INSERT INTO tax_events (user_id, claim_code, event_type, event_payload, created_at)
                VALUES (:user_id, :claim_code, :event_type, :event_payload, :created_at)
            '''),
            {
                'user_id': user_id,
                'claim_code': claim_code,
                'event_type': event_type,
                'event_payload': payload,
                'created_at': now_iso()
            }
        )


def month_window_from_period(period):
    now = datetime.now(timezone.utc)
    if period:
        try:
            parsed = datetime.strptime(period + '-01', '%Y-%m-%d')
            month_start = parsed.strftime('%Y-%m-01')
            if parsed.month == 12:
                next_month = datetime(parsed.year + 1, 1, 1)
            else:
                next_month = datetime(parsed.year, parsed.month + 1, 1)
            month_end = next_month.strftime('%Y-%m-01')
            return month_start, month_end
        except ValueError:
            return None, None

    month_start = now.strftime('%Y-%m-01')
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)
    month_end = next_month.strftime('%Y-%m-01')
    return month_start, month_end


def ensure_default_bonus_rules():
    with engine.begin() as conn:
        row = conn.execute(text('SELECT COUNT(*) AS count FROM network_bonus_rules WHERE is_active = 1')).mappings().first()
        if int(row['count'] or 0) > 0:
            return

        now = now_iso()
        conn.execute(
            text('''
                INSERT INTO network_bonus_rules (label, min_pv, rate, is_active, created_at, updated_at)
                VALUES
                    ('L3', 10000000, 0.21, 1, :now, :now),
                    ('L2', 5000000, 0.06, 1, :now, :now),
                    ('L1', 200000, 0.03, 1, :now, :now)
            '''),
            {'now': now}
        )


def get_active_bonus_rules():
    ensure_default_bonus_rules()
    with engine.connect() as conn:
        rows = conn.execute(
            text('''
                SELECT id, label, min_pv, rate
                FROM network_bonus_rules
                WHERE is_active = 1
                ORDER BY min_pv DESC, id ASC
            ''')
        ).mappings().all()
    return [dict(row) for row in rows]


def pv_rank_rate(group_pv, rules=None):
    active_rules = rules if rules is not None else get_active_bonus_rules()
    for rule in active_rules:
        if int(group_pv) >= int(rule.get('min_pv') or 0):
            return float(rule.get('rate') or 0.0), rule
    return 0.0, None


def get_group_pv_for_month(user_id, month_start, month_end):
    with engine.connect() as conn:
        row = conn.execute(
            text('''
                SELECT COALESCE(SUM(pv), 0) AS total_pv
                FROM network_sales
                WHERE seller_user_id = :user_id
                  AND datetime(created_at) >= datetime(:month_start)
                  AND datetime(created_at) < datetime(:month_end)
            '''),
            {
                'user_id': user_id,
                'month_start': month_start,
                'month_end': month_end
            }
        ).mappings().first()
    return int(row['total_pv'] or 0)


def get_upline_chain(user_id, depth=3):
    chain = []
    current = user_id
    seen = set()

    with engine.connect() as conn:
        for _ in range(depth):
            row = conn.execute(
                text('SELECT sponsor_user_id FROM network_links WHERE user_id = :user_id'),
                {'user_id': current}
            ).mappings().first()
            if not row:
                break
            sponsor_id = row.get('sponsor_user_id')
            if not sponsor_id or sponsor_id in seen:
                break
            chain.append(sponsor_id)
            seen.add(sponsor_id)
            current = sponsor_id

    return chain


@app.route('/auth/me', methods=['GET'])
def auth_me():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    with engine.connect() as conn:
        row = conn.execute(text('SELECT id,email,role FROM users WHERE id = :id'), {'id': user['user_id']}).mappings().first()
        if not row:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'id': row['id'], 'email': row['email'], 'role': row['role']})


@app.route('/auth/password/change', methods=['POST'])
def auth_password_change():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    current_password = str(data.get('current_password', ''))
    new_password = str(data.get('new_password', ''))

    if not current_password or not new_password:
        return jsonify({'error': 'current_password and new_password are required'}), 400

    policy_error = validate_password_policy(new_password)
    if policy_error:
        return jsonify({'error': policy_error}), 400

    with engine.begin() as conn:
        row = conn.execute(
            text('SELECT id, email, password FROM users WHERE id = :id'),
            {'id': user['user_id']}
        ).mappings().first()

        if not row:
            return jsonify({'error': 'User not found'}), 404

        is_valid, _ = verify_password(row['password'], current_password)
        if not is_valid:
            return jsonify({'error': 'Current password is incorrect'}), 400

        conn.execute(
            text('UPDATE users SET password = :password WHERE id = :id'),
            {'password': generate_password_hash(new_password), 'id': row['id']}
        )

    return jsonify({'message': 'Password changed'})


@app.route('/auth/password/reset/request', methods=['POST'])
def auth_password_reset_request():
    data = request.get_json() or {}
    email = str(data.get('email', '')).strip()
    if not email:
        return jsonify({'error': 'email is required'}), 400

    reset_token = None
    with engine.connect() as conn:
        row = conn.execute(
            text('SELECT id, email FROM users WHERE email = :email'),
            {'email': email}
        ).mappings().first()
        if row:
            reset_token = create_password_reset_token(row['id'], row['email'])
            # ?대찓???대뙌?곕? ?ъ슜?섏뿬 ?좏겙 諛곗넚
            delivery_result = email_adapter.send_password_reset_token(
                recipient_email=row['email'],
                token=reset_token,
                user_id=row['id'],
                expiry_minutes=30
            )
            app.logger.info('password-reset-token-issued email=%s delivery_method=%s', row['email'], delivery_result.get('delivery_method', 'unknown'))

    response_payload = {
        'message': 'If the account exists, reset instructions have been generated',
        'delivery': 'mock-log'
    }
    if app.config.get('EXPOSE_RESET_TOKEN_IN_RESPONSE'):
        response_payload['reset_token'] = reset_token

    return jsonify(response_payload)


@app.route('/auth/password/reset/confirm', methods=['POST'])
def auth_password_reset_confirm():
    data = request.get_json() or {}
    token = str(data.get('token', '')).strip()
    new_password = str(data.get('new_password', ''))

    if not token or not new_password:
        return jsonify({'error': 'token and new_password are required'}), 400

    policy_error = validate_password_policy(new_password)
    if policy_error:
        return jsonify({'error': policy_error}), 400

    token_data = verify_password_reset_token(token)
    if not token_data:
        return jsonify({'error': 'Invalid or expired reset token'}), 400

    with engine.begin() as conn:
        row = conn.execute(
            text('SELECT id FROM users WHERE id = :id AND email = :email'),
            {'id': token_data['user_id'], 'email': token_data['email']}
        ).mappings().first()
        if not row:
            return jsonify({'error': 'User not found'}), 404

        conn.execute(
            text('UPDATE users SET password = :password WHERE id = :id'),
            {'password': generate_password_hash(new_password), 'id': row['id']}
        )

    return jsonify({'message': 'Password reset completed'})


@app.route('/postings', methods=['GET'])
def get_postings():
    subject = request.args.get('subject')
    region = request.args.get('region')
    min_rate = request.args.get('min_rate', type=int)
    owner_only = request.args.get('owner_only') == 'true'
    user = get_current_user()

    if owner_only and not user:
        return jsonify({'error': 'Unauthorized'}), 401

    clauses = []
    params = {}

    if subject:
        clauses.append('lower(subject) = lower(:subject)')
        params['subject'] = subject
    if region:
        clauses.append('region LIKE :region')
        params['region'] = f'%{region}%'
    if min_rate is not None:
        clauses.append('rate >= :min_rate')
        params['min_rate'] = min_rate
    if owner_only and user:
        clauses.append('owner_id = :owner_id')
        params['owner_id'] = user['user_id']

    where_sql = f" WHERE {' AND '.join(clauses)}" if clauses else ''
    query = text(
        'SELECT id, title, subject, region, rate, created_at, owner_id FROM postings'
        + where_sql
        + ' ORDER BY id DESC'
    )

    with engine.connect() as conn:
        result = conn.execute(query, params).mappings().all()
        return jsonify([dict(row) for row in result])


@app.route('/postings', methods=['POST'])
def create_posting():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # RBAC: Only instructors can create postings
    if user.get('role') != 'instructor':
        return jsonify({'error': 'Only instructors can create postings'}), 403

    data = request.get_json()
    for key in ('title', 'subject', 'region', 'rate'):
        if key not in data:
            return jsonify({'error': f'{key} required'}), 400

    with engine.begin() as conn:
        conn.execute(
            text('INSERT INTO postings (title, subject, region, rate, created_at, owner_id) VALUES (:title,:subject,:region,:rate,:created_at,:owner_id)'),
            {
                'title': data['title'],
                'subject': data['subject'],
                'region': data['region'],
                'rate': data['rate'],
                'created_at': datetime.now(timezone.utc).isoformat(),
                'owner_id': user['user_id']
            }
        )
        # Get last inserted id
        result = conn.execute(text('SELECT last_insert_rowid() as id'))
        posting_id = result.scalar()
    
    return jsonify({'message': 'Posting created', 'id': posting_id}), 201


@app.route('/postings/<int:posting_id>', methods=['GET'])
def get_posting_detail(posting_id):
    with engine.connect() as conn:
        row = conn.execute(
            text('SELECT id, title, subject, region, rate, created_at, owner_id FROM postings WHERE id = :id'),
            {'id': posting_id}
        ).mappings().first()
        if not row:
            return jsonify({'error': 'Posting not found'}), 404
        return jsonify(dict(row))


@app.route('/postings/<int:posting_id>', methods=['PUT'])
def update_posting(posting_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    with engine.begin() as conn:
        posting = conn.execute(
            text('SELECT id FROM postings WHERE id = :id AND owner_id = :owner_id'),
            {'id': posting_id, 'owner_id': user['user_id']}
        ).first()
        if not posting:
            return jsonify({'error': 'Posting not found or not owned'}), 404

        conn.execute(
            text('UPDATE postings SET title=:title, subject=:subject, region=:region, rate=:rate WHERE id=:id'),
            {
                'title': data.get('title', ''),
                'subject': data.get('subject', ''),
                'region': data.get('region', ''),
                'rate': data.get('rate', 0),
                'id': posting_id
            }
        )

    return jsonify({'message': 'Posting updated'})


@app.route('/postings/<int:posting_id>', methods=['DELETE'])
def delete_posting(posting_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    with engine.begin() as conn:
        result = conn.execute(
            text('DELETE FROM postings WHERE id = :id AND owner_id = :owner_id'),
            {'id': posting_id, 'owner_id': user['user_id']}
        )
        if result.rowcount == 0:
            return jsonify({'error': 'Posting not found or not owned'}), 404

    return jsonify({'message': 'Posting deleted'})


@app.route('/applications', methods=['POST'])
def apply_posting():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    if 'posting_id' not in data:
        return jsonify({'error': 'posting_id required'}), 400

    status = data.get('status', 'pending')
    with engine.begin() as conn:
        existing = conn.execute(
            text('SELECT id FROM applications WHERE posting_id = :posting_id AND student_id = :student_id'),
            {'posting_id': data['posting_id'], 'student_id': user['user_id']}
        ).first()
        if existing:
            return jsonify({'error': 'Already applied'}), 409

        conn.execute(
            text('INSERT INTO applications (posting_id, student_id, status, created_at) VALUES (:p,:s,:status,:c)'),
            {'p': data['posting_id'], 's': user['user_id'], 'status': status, 'c': datetime.now(timezone.utc).isoformat()}
        )
        # Get last inserted id
        result = conn.execute(text('SELECT last_insert_rowid() as id'))
        app_id = result.scalar()
    
    return jsonify({'message': 'Applied', 'id': app_id, 'status': status}), 201


@app.route('/applications', methods=['GET'])
def get_applications():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    status_filter = request.args.get('status', 'all').strip().lower()
    allowed_statuses = {'all', 'pending', 'approved', 'rejected'}
    if status_filter not in allowed_statuses:
        return jsonify({'error': 'Invalid status filter'}), 400

    search_query = request.args.get('q', '').strip().lower()
    sort_mode = request.args.get('sort', 'newest').strip().lower()
    allowed_sorts = {'newest', 'oldest', 'status'}
    if sort_mode not in allowed_sorts:
        return jsonify({'error': 'Invalid sort option'}), 400

    with engine.connect() as conn:
        if user.get('role') == 'instructor':
            query = '''
                SELECT
                    a.id,
                    a.posting_id,
                    p.title AS posting_title,
                    a.student_id,
                    u.email AS student_email,
                    u.organization AS student_organization,
                    a.status,
                    a.created_at
                FROM applications a
                JOIN postings p ON p.id = a.posting_id
                LEFT JOIN users u ON u.id = a.student_id
                WHERE p.owner_id = :owner_id
            '''
            params = {'owner_id': user['user_id']}
        else:
            query = '''
                SELECT
                    a.id,
                    a.posting_id,
                    p.title AS posting_title,
                    a.student_id,
                    u.email AS student_email,
                    u.organization AS student_organization,
                    a.status,
                    a.created_at
                FROM applications a
                JOIN postings p ON p.id = a.posting_id
                LEFT JOIN users u ON u.id = a.student_id
                WHERE a.student_id = :student_id
            '''
            params = {'student_id': user['user_id']}

        if status_filter != 'all':
            query += ' AND a.status = :status'
            params['status'] = status_filter

        if search_query:
            query += ' AND ('
            query += 'LOWER(p.title) LIKE :search_like'
            params['search_like'] = f"%{search_query}%"
            if user.get('role') == 'instructor':
                query += ' OR LOWER(COALESCE(u.email, \"\")) LIKE :search_like'
                query += ' OR LOWER(COALESCE(u.organization, \"\")) LIKE :search_like'
                if search_query.isdigit():
                    query += ' OR CAST(a.student_id AS TEXT) = :search_student_id'
                    params['search_student_id'] = search_query
            query += ')'

        if sort_mode == 'oldest':
            query += ' ORDER BY datetime(a.created_at) ASC, a.id ASC'
        elif sort_mode == 'status':
            query += '''
                ORDER BY CASE a.status
                    WHEN 'pending' THEN 0
                    WHEN 'approved' THEN 1
                    WHEN 'rejected' THEN 2
                    ELSE 3
                END ASC,
                datetime(a.created_at) DESC,
                a.id DESC
            '''
        else:
            query += ' ORDER BY datetime(a.created_at) DESC, a.id DESC'

        rows = conn.execute(text(query), params).mappings().all()
        return jsonify([dict(row) for row in rows])


@app.route('/applications/applicants/<int:student_id>/summary', methods=['GET'])
def get_applicant_summary(student_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    if user.get('role') != 'instructor':
        return jsonify({'error': 'Only instructors can view applicant summaries'}), 403

    with engine.connect() as conn:
        rows = conn.execute(
            text('''
                SELECT
                    a.id,
                    a.status,
                    a.created_at,
                    p.id AS posting_id,
                    p.title AS posting_title,
                    u.email AS student_email,
                    u.organization AS student_organization
                FROM applications a
                JOIN postings p ON p.id = a.posting_id
                LEFT JOIN users u ON u.id = a.student_id
                WHERE p.owner_id = :owner_id AND a.student_id = :student_id
                ORDER BY datetime(a.created_at) DESC, a.id DESC
            '''),
            {'owner_id': user['user_id'], 'student_id': student_id}
        ).mappings().all()

    if not rows:
        return jsonify({'error': 'Applicant not found in your postings'}), 404

    status_counts = {'pending': 0, 'approved': 0, 'rejected': 0}
    for row in rows:
        status = row['status']
        if status in status_counts:
            status_counts[status] += 1

    return jsonify({
        'student_id': student_id,
        'student_email': rows[0].get('student_email'),
        'student_organization': rows[0].get('student_organization') or '',
        'total_applications_to_you': len(rows),
        'status_counts': status_counts,
        'recent_applications': [
            {
                'application_id': row['id'],
                'posting_id': row['posting_id'],
                'posting_title': row['posting_title'],
                'status': row['status'],
                'created_at': row['created_at'],
            }
            for row in rows[:5]
        ],
    })


@app.route('/applications/<int:application_id>', methods=['PATCH'])
def update_application(application_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    if user.get('role') != 'instructor':
        return jsonify({'error': 'Only instructors can update applications'}), 403

    data = request.get_json() or {}
    status = data.get('status')
    if status not in ['approved', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400

    with engine.begin() as conn:
        row = conn.execute(
            text('''
                SELECT a.id
                FROM applications a
                JOIN postings p ON p.id = a.posting_id
                WHERE a.id = :application_id AND p.owner_id = :owner_id
            '''),
            {'application_id': application_id, 'owner_id': user['user_id']}
        ).first()
        if not row:
            return jsonify({'error': 'Application not found or not owned'}), 404

        conn.execute(
            text('UPDATE applications SET status = :status WHERE id = :application_id'),
            {'status': status, 'application_id': application_id}
        )

    return jsonify({'message': 'Application updated', 'status': status})


@app.route('/applications/<int:application_id>', methods=['DELETE'])
def cancel_application(application_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    if user.get('role') != 'student':
        return jsonify({'error': 'Only students can cancel applications'}), 403

    with engine.begin() as conn:
        row = conn.execute(
            text('SELECT id, status FROM applications WHERE id = :id AND student_id = :student_id'),
            {'id': application_id, 'student_id': user['user_id']}
        ).mappings().first()
        if not row:
            return jsonify({'error': 'Application not found'}), 404
        if row['status'] != 'pending':
            return jsonify({'error': 'Only pending applications can be cancelled'}), 400

        conn.execute(
            text('DELETE FROM applications WHERE id = :id AND student_id = :student_id'),
            {'id': application_id, 'student_id': user['user_id']}
        )

    return jsonify({'message': 'Application cancelled'})


@app.route('/dashboard/stats', methods=['GET'])
def dashboard_stats():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    with engine.connect() as conn:
        if user.get('role') == 'instructor':
            postings_count = conn.execute(
                text('SELECT COUNT(*) AS count FROM postings WHERE owner_id = :owner_id'),
                {'owner_id': user['user_id']}
            ).mappings().first()['count']

            status_rows = conn.execute(
                text('''
                    SELECT a.status, COUNT(*) AS count
                    FROM applications a
                    JOIN postings p ON p.id = a.posting_id
                    WHERE p.owner_id = :owner_id
                    GROUP BY a.status
                '''),
                {'owner_id': user['user_id']}
            ).mappings().all()

            status_counts = {'pending': 0, 'approved': 0, 'rejected': 0}
            for row in status_rows:
                status = row['status']
                if status in status_counts:
                    status_counts[status] = row['count']

            applications_total = sum(status_counts.values())
            return jsonify({
                'role': 'instructor',
                'postings_count': postings_count,
                'applications_total': applications_total,
                'pending_count': status_counts['pending'],
                'approved_count': status_counts['approved'],
                'rejected_count': status_counts['rejected']
            })

        status_rows = conn.execute(
            text('SELECT status, COUNT(*) AS count FROM applications WHERE student_id = :student_id GROUP BY status'),
            {'student_id': user['user_id']}
        ).mappings().all()

        status_counts = {'pending': 0, 'approved': 0, 'rejected': 0}
        for row in status_rows:
            status = row['status']
            if status in status_counts:
                status_counts[status] = row['count']

        applications_total = sum(status_counts.values())
        return jsonify({
            'role': 'student',
            'applications_total': applications_total,
            'pending_count': status_counts['pending'],
            'approved_count': status_counts['approved'],
            'rejected_count': status_counts['rejected']
        })


@app.route('/dashboard/activity', methods=['GET'])
def dashboard_activity():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    period = request.args.get('period', '7d')
    windows = {
        'today': '-1 day',
        '7d': '-7 days',
        '30d': '-30 days'
    }
    if period not in windows:
        return jsonify({'error': 'Invalid period'}), 400

    since_window = windows[period]

    with engine.connect() as conn:
        if user.get('role') == 'instructor':
            rows = conn.execute(
                text('''
                    SELECT * FROM (
                        SELECT
                            'posting_created' AS type,
                            p.id AS ref_id,
                            p.id AS posting_id,
                            p.title AS title,
                            NULL AS status,
                            p.created_at AS created_at
                        FROM postings p
                        WHERE p.owner_id = :owner_id
                          AND datetime(p.created_at) >= datetime('now', :since_window)

                        UNION ALL

                        SELECT
                            'application_received' AS type,
                            a.id AS ref_id,
                            a.posting_id AS posting_id,
                            p.title AS title,
                            a.status AS status,
                            a.created_at AS created_at
                        FROM applications a
                        JOIN postings p ON p.id = a.posting_id
                        WHERE p.owner_id = :owner_id
                          AND datetime(a.created_at) >= datetime('now', :since_window)
                    )
                    ORDER BY created_at DESC, ref_id DESC
                    LIMIT 5
                '''),
                {'owner_id': user['user_id'], 'since_window': since_window}
            ).mappings().all()
            return jsonify([dict(row) for row in rows])

        rows = conn.execute(
            text('''
                SELECT
                    'application_submitted' AS type,
                    a.id AS ref_id,
                    a.posting_id AS posting_id,
                    p.title AS title,
                    a.status AS status,
                    a.created_at AS created_at
                FROM applications a
                JOIN postings p ON p.id = a.posting_id
                WHERE a.student_id = :student_id
                  AND datetime(a.created_at) >= datetime('now', :since_window)
                ORDER BY a.created_at DESC, a.id DESC
                LIMIT 5
            '''),
            {'student_id': user['user_id'], 'since_window': since_window}
        ).mappings().all()
        return jsonify([dict(row) for row in rows])


@app.route('/api/tax/onboard', methods=['POST'])
def tax_onboard():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    full_name = str(data.get('full_name', '')).strip()
    business_number = str(data.get('business_number', '')).strip()
    bank_name = str(data.get('bank_name', '')).strip()
    bank_account = str(data.get('bank_account', '')).strip()
    consent = bool(data.get('consent_withholding', True))

    if not full_name or not bank_name or not bank_account:
        return jsonify({'error': 'full_name, bank_name, bank_account are required'}), 400

    masked_account = bank_account[-4:].rjust(len(bank_account), '*')

    with engine.begin() as conn:
        existing = conn.execute(
            text('SELECT id FROM tax_profiles WHERE user_id = :user_id'),
            {'user_id': user['user_id']}
        ).first()

        if existing:
            conn.execute(
                text('''
                    UPDATE tax_profiles
                    SET full_name = :full_name,
                        business_number = :business_number,
                        bank_name = :bank_name,
                        bank_account_masked = :bank_account_masked,
                        consent_withholding = :consent_withholding,
                        updated_at = :updated_at
                    WHERE user_id = :user_id
                '''),
                {
                    'user_id': user['user_id'],
                    'full_name': full_name,
                    'business_number': business_number,
                    'bank_name': bank_name,
                    'bank_account_masked': masked_account,
                    'consent_withholding': 1 if consent else 0,
                    'updated_at': now_iso()
                }
            )
        else:
            conn.execute(
                text('''
                    INSERT INTO tax_profiles (
                        user_id, full_name, business_number, bank_name, bank_account_masked,
                        consent_withholding, provider, created_at, updated_at
                    ) VALUES (
                        :user_id, :full_name, :business_number, :bank_name, :bank_account_masked,
                        :consent_withholding, 'mock-hometax-sam', :created_at, :updated_at
                    )
                '''),
                {
                    'user_id': user['user_id'],
                    'full_name': full_name,
                    'business_number': business_number,
                    'bank_name': bank_name,
                    'bank_account_masked': masked_account,
                    'consent_withholding': 1 if consent else 0,
                    'created_at': now_iso(),
                    'updated_at': now_iso()
                }
            )

    log_tax_event(user['user_id'], 'tax_onboarded', f'provider=mock-hometax-sam;consent={consent}')
    return jsonify({'message': 'Tax profile saved', 'provider': 'mock-hometax-sam'})


@app.route('/api/tax/estimate', methods=['GET'])
def tax_estimate():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    tax_year = request.args.get('year', type=int) or datetime.now(timezone.utc).year
    gross_income, withholding_amount, estimated_refund = get_instructor_tax_numbers(user['user_id'], tax_year)
    net_income = gross_income - withholding_amount

    log_tax_event(
        user['user_id'],
        'tax_estimated',
        f'year={tax_year};gross={gross_income};withholding={withholding_amount};refund={estimated_refund}'
    )

    return jsonify({
        'year': tax_year,
        'gross_income': gross_income,
        'withholding_amount': withholding_amount,
        'net_income': net_income,
        'estimated_refund': estimated_refund,
        'fee_rule': '20-25% post-refund CMS charge'
    })


@app.route('/api/tax/submit', methods=['POST'])
def tax_submit():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    tax_year = int(data.get('year') or datetime.now(timezone.utc).year)
    service_fee_rate = float(data.get('service_fee_rate', 0.22))

    if service_fee_rate < 0.2 or service_fee_rate > 0.25:
        return jsonify({'error': 'service_fee_rate must be between 0.2 and 0.25'}), 400

    gross_income, withholding_amount, estimated_refund = get_instructor_tax_numbers(user['user_id'], tax_year)
    service_fee_amount = int(round(estimated_refund * service_fee_rate))
    claim_code = f'TX-{tax_year}-{uuid.uuid4().hex[:8].upper()}'

    with engine.begin() as conn:
        conn.execute(
            text('''
                INSERT INTO tax_claims (
                    claim_code, user_id, tax_year, gross_income, withholding_amount,
                    estimated_refund, service_fee_rate, service_fee_amount,
                    status, created_at, updated_at
                ) VALUES (
                    :claim_code, :user_id, :tax_year, :gross_income, :withholding_amount,
                    :estimated_refund, :service_fee_rate, :service_fee_amount,
                    'submitted', :created_at, :updated_at
                )
            '''),
            {
                'claim_code': claim_code,
                'user_id': user['user_id'],
                'tax_year': tax_year,
                'gross_income': gross_income,
                'withholding_amount': withholding_amount,
                'estimated_refund': estimated_refund,
                'service_fee_rate': service_fee_rate,
                'service_fee_amount': service_fee_amount,
                'created_at': now_iso(),
                'updated_at': now_iso()
            }
        )

    log_tax_event(
        user['user_id'],
        'tax_submitted',
        f'year={tax_year};refund={estimated_refund};fee={service_fee_amount}',
        claim_code=claim_code
    )

    return jsonify({
        'submission_id': claim_code,
        'status': 'submitted',
        'estimated_refund': estimated_refund,
        'service_fee_amount': service_fee_amount
    }), 201


@app.route('/api/tax/status/<submission_id>', methods=['GET'])
def tax_status(submission_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    with engine.connect() as conn:
        claim = conn.execute(
            text('''
                SELECT claim_code, tax_year, gross_income, withholding_amount,
                       estimated_refund, service_fee_rate, service_fee_amount,
                       status, created_at, updated_at
                FROM tax_claims
                WHERE claim_code = :claim_code AND user_id = :user_id
            '''),
            {'claim_code': submission_id, 'user_id': user['user_id']}
        ).mappings().first()

        if not claim:
            return jsonify({'error': 'Tax submission not found'}), 404

    return jsonify(dict(claim))


@app.route('/api/tax/events', methods=['GET'])
def tax_events():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    limit = request.args.get('limit', type=int) or 20
    limit = max(1, min(limit, 100))
    event_type = (request.args.get('event_type') or '').strip()
    claim_code = (request.args.get('claim_code') or '').strip()

    clauses = ['user_id = :user_id']
    params = {'user_id': user['user_id'], 'limit': limit}

    if event_type:
        clauses.append('event_type = :event_type')
        params['event_type'] = event_type

    if claim_code:
        clauses.append('claim_code = :claim_code')
        params['claim_code'] = claim_code

    where_sql = ' AND '.join(clauses)

    with engine.connect() as conn:
        rows = conn.execute(
            text('''
                SELECT claim_code, event_type, event_payload, created_at
                FROM tax_events
                WHERE ''' + where_sql + '''
                ORDER BY id DESC
                LIMIT :limit
            '''),
            params
        ).mappings().all()

    return jsonify([dict(row) for row in rows])


@app.route('/api/tax/report/<int:year>', methods=['GET'])
def tax_report(year):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    gross_income, withholding_amount, estimated_refund = get_instructor_tax_numbers(user['user_id'], year)

    with engine.connect() as conn:
        claims = conn.execute(
            text('''
                SELECT claim_code, status, estimated_refund, service_fee_amount, created_at
                FROM tax_claims
                WHERE user_id = :user_id AND tax_year = :tax_year
                ORDER BY id DESC
            '''),
            {'user_id': user['user_id'], 'tax_year': year}
        ).mappings().all()

    return jsonify({
        'year': year,
        'gross_income': gross_income,
        'withholding_amount': withholding_amount,
        'net_income': gross_income - withholding_amount,
        'estimated_refund': estimated_refund,
        'claims': [dict(row) for row in claims]
    })


@app.route('/api/cms/charge', methods=['POST'])
def cms_charge():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    submission_id = data.get('submission_id')
    if not submission_id:
        return jsonify({'error': 'submission_id is required'}), 400

    with engine.begin() as conn:
        claim = conn.execute(
            text('''
                SELECT claim_code, service_fee_amount, status
                FROM tax_claims
                WHERE claim_code = :claim_code AND user_id = :user_id
            '''),
            {'claim_code': submission_id, 'user_id': user['user_id']}
        ).mappings().first()

        if not claim:
            return jsonify({'error': 'Tax submission not found'}), 404

        charge_code = f'CMS-{uuid.uuid4().hex[:10].upper()}'
        conn.execute(
            text('''
                INSERT INTO cms_charges (
                    charge_code, user_id, claim_code, amount, status, created_at, processed_at
                ) VALUES (
                    :charge_code, :user_id, :claim_code, :amount, 'processed', :created_at, :processed_at
                )
            '''),
            {
                'charge_code': charge_code,
                'user_id': user['user_id'],
                'claim_code': claim['claim_code'],
                'amount': int(claim['service_fee_amount'] or 0),
                'created_at': now_iso(),
                'processed_at': now_iso()
            }
        )

        conn.execute(
            text('UPDATE tax_claims SET status = :status, updated_at = :updated_at WHERE claim_code = :claim_code'),
            {'status': 'fee_charged', 'updated_at': now_iso(), 'claim_code': claim['claim_code']}
        )

    log_tax_event(
        user['user_id'],
        'cms_fee_charged',
        f'claim={submission_id};amount={int(claim["service_fee_amount"] or 0)}',
        claim_code=submission_id
    )

    return jsonify({
        'charge_code': charge_code,
        'submission_id': submission_id,
        'amount': int(claim['service_fee_amount'] or 0),
        'status': 'processed'
    }), 201


@app.route('/api/network/link', methods=['POST'])
def network_link():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    sponsor_user_id = data.get('sponsor_user_id')
    sponsor_email = (data.get('sponsor_email') or '').strip()

    with engine.begin() as conn:
        if sponsor_email and not sponsor_user_id:
            sponsor = conn.execute(
                text('SELECT id FROM users WHERE email = :email'),
                {'email': sponsor_email}
            ).mappings().first()
            if not sponsor:
                return jsonify({'error': 'Sponsor email not found'}), 404
            sponsor_user_id = sponsor['id']

        if not sponsor_user_id:
            return jsonify({'error': 'sponsor_user_id or sponsor_email is required'}), 400

        if int(sponsor_user_id) == int(user['user_id']):
            return jsonify({'error': 'Cannot sponsor yourself'}), 400

        existing = conn.execute(
            text('SELECT id FROM network_links WHERE user_id = :user_id'),
            {'user_id': user['user_id']}
        ).first()

        if existing:
            conn.execute(
                text('''
                    UPDATE network_links
                    SET sponsor_user_id = :sponsor_user_id,
                        updated_at = :updated_at
                    WHERE user_id = :user_id
                '''),
                {
                    'sponsor_user_id': sponsor_user_id,
                    'updated_at': now_iso(),
                    'user_id': user['user_id']
                }
            )
        else:
            conn.execute(
                text('''
                    INSERT INTO network_links (user_id, sponsor_user_id, created_at, updated_at)
                    VALUES (:user_id, :sponsor_user_id, :created_at, :updated_at)
                '''),
                {
                    'user_id': user['user_id'],
                    'sponsor_user_id': sponsor_user_id,
                    'created_at': now_iso(),
                    'updated_at': now_iso()
                }
            )

    return jsonify({'message': 'Sponsor link saved', 'sponsor_user_id': int(sponsor_user_id)})


@app.route('/api/network/sales', methods=['POST'])
def create_network_sale():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    base_price = int(data.get('base_price') or 0)
    pv = int(data.get('pv') or 0)
    bv = int(data.get('bv') or 0)
    if base_price <= 0:
        return jsonify({'error': 'base_price must be > 0'}), 400

    now = now_iso()
    month_start, month_end = month_window_from_period(None)

    with engine.begin() as conn:
        result = conn.execute(
            text('''
                INSERT INTO network_sales (seller_user_id, base_price, pv, bv, created_at)
                VALUES (:seller_user_id, :base_price, :pv, :bv, :created_at)
            '''),
            {
                'seller_user_id': user['user_id'],
                'base_price': base_price,
                'pv': pv,
                'bv': bv,
                'created_at': now
            }
        )
        sale_id = result.lastrowid

    chain = get_upline_chain(user['user_id'], depth=3)
    active_rules = get_active_bonus_rules()
    raw_allocations = []
    for idx, beneficiary_id in enumerate(chain, start=1):
        group_pv = get_group_pv_for_month(beneficiary_id, month_start, month_end)
        rate, matched_rule = pv_rank_rate(group_pv, rules=active_rules)
        if rate <= 0:
            continue
        amount_raw = int(round(base_price * rate))
        raw_allocations.append({
            'beneficiary_user_id': beneficiary_id,
            'referral_level': idx,
            'applied_rate': rate,
            'rule_label': matched_rule.get('label') if matched_rule else None,
            'rule_min_pv': matched_rule.get('min_pv') if matched_rule else None,
            'amount_raw': amount_raw,
            'group_pv': group_pv
        })

    gamma = float(base_price)
    c_raw = float(sum(item['amount_raw'] for item in raw_allocations))
    cap = gamma * 0.35
    scale_factor = 1.0 if c_raw <= cap or c_raw == 0 else cap / c_raw

    paid_allocations = []
    with engine.begin() as conn:
        for item in raw_allocations:
            amount_paid = int(round(item['amount_raw'] * scale_factor))
            conn.execute(
                text('''
                    INSERT INTO network_bonus_allocations (
                        sale_id, beneficiary_user_id, referral_level,
                        applied_rate, amount_raw, amount_paid, scale_factor, created_at
                    ) VALUES (
                        :sale_id, :beneficiary_user_id, :referral_level,
                        :applied_rate, :amount_raw, :amount_paid, :scale_factor, :created_at
                    )
                '''),
                {
                    'sale_id': sale_id,
                    'beneficiary_user_id': item['beneficiary_user_id'],
                    'referral_level': item['referral_level'],
                    'applied_rate': item['applied_rate'],
                    'amount_raw': item['amount_raw'],
                    'amount_paid': amount_paid,
                    'scale_factor': scale_factor,
                    'created_at': now
                }
            )

            paid_allocations.append({
                'beneficiary_user_id': item['beneficiary_user_id'],
                'referral_level': item['referral_level'],
                'applied_rate': item['applied_rate'],
                'rule_label': item.get('rule_label'),
                'rule_min_pv': item.get('rule_min_pv'),
                'group_pv': item['group_pv'],
                'amount_raw': item['amount_raw'],
                'amount_paid': amount_paid
            })

    c_paid = float(sum(item['amount_paid'] for item in paid_allocations))
    ratio = 0.0 if gamma <= 0 else c_paid / gamma

    return jsonify({
        'sale_id': sale_id,
        'gamma': gamma,
        'bonus_total_raw': c_raw,
        'bonus_total_paid': c_paid,
        'cap_35_percent': cap,
        'ratio': ratio,
        'capped': c_raw > cap,
        'scale_factor': scale_factor,
        'allocations': paid_allocations
    }), 201


@app.route('/api/network/compliance', methods=['GET'])
def network_compliance():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    period = (request.args.get('period') or '').strip()
    month_start, month_end = month_window_from_period(period)
    if not month_start or not month_end:
        return jsonify({'error': 'Invalid period format. Use YYYY-MM'}), 400

    with engine.connect() as conn:
        gamma_row = conn.execute(
            text('''
                SELECT COALESCE(SUM(base_price), 0) AS gamma
                FROM network_sales
                WHERE seller_user_id = :seller_user_id
                  AND datetime(created_at) >= datetime(:month_start)
                  AND datetime(created_at) < datetime(:month_end)
            '''),
            {
                'seller_user_id': user['user_id'],
                'month_start': month_start,
                'month_end': month_end
            }
        ).mappings().first()

        c_row = conn.execute(
            text('''
                SELECT COALESCE(SUM(nba.amount_paid), 0) AS c_total
                FROM network_bonus_allocations nba
                JOIN network_sales ns ON ns.id = nba.sale_id
                WHERE ns.seller_user_id = :seller_user_id
                  AND datetime(nba.created_at) >= datetime(:month_start)
                  AND datetime(nba.created_at) < datetime(:month_end)
            '''),
            {
                'seller_user_id': user['user_id'],
                'month_start': month_start,
                'month_end': month_end
            }
        ).mappings().first()

    gamma = float(gamma_row['gamma'] or 0)
    c_total = float(c_row['c_total'] or 0)
    ratio = 0.0 if gamma <= 0 else c_total / gamma

    return jsonify({
        'period': month_start[:7],
        'gamma': gamma,
        'c_total': c_total,
        'limit': gamma * 0.35,
        'ratio': ratio,
        'within_limit': ratio <= 0.35 if gamma > 0 else True
    })


@app.route('/api/network/bonuses', methods=['GET'])
def network_bonuses():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    period = (request.args.get('period') or '').strip()
    month_start, month_end = month_window_from_period(period)
    if not month_start or not month_end:
        return jsonify({'error': 'Invalid period format. Use YYYY-MM'}), 400

    with engine.connect() as conn:
        rows = conn.execute(
            text('''
                SELECT sale_id, referral_level, applied_rate, amount_paid, created_at
                FROM network_bonus_allocations
                WHERE beneficiary_user_id = :beneficiary_user_id
                  AND datetime(created_at) >= datetime(:month_start)
                  AND datetime(created_at) < datetime(:month_end)
                ORDER BY id DESC
                LIMIT 50
            '''),
            {
                'beneficiary_user_id': user['user_id'],
                'month_start': month_start,
                'month_end': month_end
            }
        ).mappings().all()

    return jsonify([dict(row) for row in rows])


def can_view_admin_insights(user):
    role = (user or {}).get('role', '')
    return role in ('admin', 'super_admin')


@app.route('/api/network/admin/summary', methods=['GET'])
def network_admin_summary():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not can_view_admin_insights(user):
        return jsonify({'error': 'Forbidden'}), 403

    period = (request.args.get('period') or '').strip()
    month_start, month_end = month_window_from_period(period)
    if not month_start or not month_end:
        return jsonify({'error': 'Invalid period format. Use YYYY-MM'}), 400

    with engine.connect() as conn:
        gamma_row = conn.execute(
            text('''
                SELECT COALESCE(SUM(base_price), 0) AS gamma
                FROM network_sales
                WHERE datetime(created_at) >= datetime(:month_start)
                  AND datetime(created_at) < datetime(:month_end)
            '''),
            {'month_start': month_start, 'month_end': month_end}
        ).mappings().first()

        c_row = conn.execute(
            text('''
                SELECT COALESCE(SUM(amount_paid), 0) AS c_total
                FROM network_bonus_allocations
                WHERE datetime(created_at) >= datetime(:month_start)
                  AND datetime(created_at) < datetime(:month_end)
            '''),
            {'month_start': month_start, 'month_end': month_end}
        ).mappings().first()

        seller_count_row = conn.execute(
            text('''
                SELECT COUNT(DISTINCT seller_user_id) AS sellers
                FROM network_sales
                WHERE datetime(created_at) >= datetime(:month_start)
                  AND datetime(created_at) < datetime(:month_end)
            '''),
            {'month_start': month_start, 'month_end': month_end}
        ).mappings().first()

        capped_row = conn.execute(
            text('''
                SELECT COUNT(DISTINCT sale_id) AS capped_sales
                FROM network_bonus_allocations
                WHERE datetime(created_at) >= datetime(:month_start)
                  AND datetime(created_at) < datetime(:month_end)
                  AND scale_factor < 0.9999
            '''),
            {'month_start': month_start, 'month_end': month_end}
        ).mappings().first()

    gamma = float(gamma_row['gamma'] or 0)
    c_total = float(c_row['c_total'] or 0)
    ratio = 0.0 if gamma <= 0 else c_total / gamma

    return jsonify({
        'period': month_start[:7],
        'gamma': gamma,
        'c_total': c_total,
        'limit': gamma * 0.35,
        'ratio': ratio,
        'within_limit': ratio <= 0.35 if gamma > 0 else True,
        'active_sellers': int(seller_count_row['sellers'] or 0),
        'capped_sales': int(capped_row['capped_sales'] or 0)
    })


@app.route('/api/network/admin/top-sponsors', methods=['GET'])
def network_admin_top_sponsors():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not can_view_admin_insights(user):
        return jsonify({'error': 'Forbidden'}), 403

    period = (request.args.get('period') or '').strip()
    limit = request.args.get('limit', type=int) or 10
    limit = max(1, min(limit, 50))
    month_start, month_end = month_window_from_period(period)
    if not month_start or not month_end:
        return jsonify({'error': 'Invalid period format. Use YYYY-MM'}), 400

    with engine.connect() as conn:
        rows = conn.execute(
            text('''
                SELECT
                    nba.beneficiary_user_id AS user_id,
                    u.email AS email,
                    COALESCE(SUM(nba.amount_paid), 0) AS total_paid,
                    COUNT(*) AS allocation_count,
                    COALESCE(AVG(nba.applied_rate), 0) AS avg_rate
                FROM network_bonus_allocations nba
                LEFT JOIN users u ON u.id = nba.beneficiary_user_id
                WHERE datetime(nba.created_at) >= datetime(:month_start)
                  AND datetime(nba.created_at) < datetime(:month_end)
                GROUP BY nba.beneficiary_user_id, u.email
                ORDER BY total_paid DESC
                LIMIT :limit
            '''),
            {
                'month_start': month_start,
                'month_end': month_end,
                'limit': limit
            }
        ).mappings().all()

    return jsonify([dict(row) for row in rows])


@app.route('/api/network/admin/sponsor-trend', methods=['GET'])
def network_admin_sponsor_trend():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not can_view_admin_insights(user):
        return jsonify({'error': 'Forbidden'}), 403

    sponsor_user_id = request.args.get('user_id', type=int)
    months = request.args.get('months', type=int) or 6
    months = max(1, min(months, 24))
    if not sponsor_user_id:
        return jsonify({'error': 'user_id is required'}), 400

    with engine.connect() as conn:
        rows = conn.execute(
            text('''
                SELECT
                    substr(created_at, 1, 7) AS month,
                    COALESCE(SUM(amount_paid), 0) AS total_paid,
                    COUNT(*) AS allocation_count,
                    COALESCE(AVG(applied_rate), 0) AS avg_rate
                FROM network_bonus_allocations
                WHERE beneficiary_user_id = :beneficiary_user_id
                GROUP BY substr(created_at, 1, 7)
                ORDER BY month DESC
                LIMIT :months
            '''),
            {'beneficiary_user_id': sponsor_user_id, 'months': months}
        ).mappings().all()

        sponsor = conn.execute(
            text('SELECT id, email FROM users WHERE id = :id'),
            {'id': sponsor_user_id}
        ).mappings().first()

    trend = [dict(row) for row in rows]
    trend.reverse()

    return jsonify({
        'user_id': sponsor_user_id,
        'email': (sponsor or {}).get('email'),
        'months': months,
        'trend': trend
    })


@app.route('/api/network/admin/rules', methods=['GET'])
def network_admin_rules_get():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not can_view_admin_insights(user):
        return jsonify({'error': 'Forbidden'}), 403

    rules = get_active_bonus_rules()
    return jsonify(rules)


@app.route('/api/network/admin/rules', methods=['PUT'])
def network_admin_rules_put():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not can_view_admin_insights(user):
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json() or {}
    rules = data.get('rules')
    if not isinstance(rules, list) or len(rules) == 0:
        return jsonify({'error': 'rules array is required'}), 400

    normalized = []
    for idx, rule in enumerate(rules, start=1):
        if not isinstance(rule, dict):
            return jsonify({'error': f'rule #{idx} must be an object'}), 400
        min_pv = int(rule.get('min_pv') or 0)
        rate = float(rule.get('rate') or 0)
        label = str(rule.get('label') or f'R{idx}').strip()
        if min_pv < 0:
            return jsonify({'error': f'rule #{idx} min_pv must be >= 0'}), 400
        if rate < 0 or rate > 0.35:
            return jsonify({'error': f'rule #{idx} rate must be between 0 and 0.35'}), 400
        normalized.append({'label': label[:24], 'min_pv': min_pv, 'rate': rate})

    normalized.sort(key=lambda x: x['min_pv'], reverse=True)
    now = now_iso()

    current_rules = get_active_bonus_rules()

    with engine.begin() as conn:
        conn.execute(text('UPDATE network_bonus_rules SET is_active = 0, updated_at = :updated_at'), {'updated_at': now})
        for rule in normalized:
            conn.execute(
                text('''
                    INSERT INTO network_bonus_rules (label, min_pv, rate, is_active, created_at, updated_at)
                    VALUES (:label, :min_pv, :rate, 1, :created_at, :updated_at)
                '''),
                {
                    'label': rule['label'],
                    'min_pv': rule['min_pv'],
                    'rate': rule['rate'],
                    'created_at': now,
                    'updated_at': now
                }
            )

        conn.execute(
            text('''
                INSERT INTO network_rule_audits (actor_user_id, rules_json, created_at)
                VALUES (:actor_user_id, :rules_json, :created_at)
            '''),
            {
                'actor_user_id': user['user_id'],
                'rules_json': json.dumps({'before': current_rules, 'after': normalized}, ensure_ascii=True),
                'created_at': now
            }
        )

    return jsonify({'message': 'Rules updated', 'rules': get_active_bonus_rules()})


@app.route('/api/network/admin/rules/audits', methods=['GET'])
def network_admin_rules_audits_get():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not can_view_admin_insights(user):
        return jsonify({'error': 'Forbidden'}), 403

    limit = request.args.get('limit', type=int) or 20
    limit = max(1, min(limit, 100))

    with engine.connect() as conn:
        rows = conn.execute(
            text('''
                SELECT a.id, a.actor_user_id, u.email AS actor_email, a.rules_json, a.created_at
                FROM network_rule_audits a
                LEFT JOIN users u ON u.id = a.actor_user_id
                ORDER BY a.id DESC
                LIMIT :limit
            '''),
            {'limit': limit}
        ).mappings().all()

    return jsonify([dict(row) for row in rows])


@app.route('/api/network/admin/rules/simulate', methods=['POST'])
def network_admin_rules_simulate():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not can_view_admin_insights(user):
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json() or {}
    rules = data.get('rules')
    period = (data.get('period') or '').strip()
    if not isinstance(rules, list) or len(rules) == 0:
        return jsonify({'error': 'rules array is required'}), 400

    month_start, month_end = month_window_from_period(period)
    if not month_start or not month_end:
        return jsonify({'error': 'Invalid period format. Use YYYY-MM'}), 400

    normalized_rules = []
    for idx, rule in enumerate(rules, start=1):
        if not isinstance(rule, dict):
            return jsonify({'error': f'rule #{idx} must be an object'}), 400
        min_pv = int(rule.get('min_pv') or 0)
        rate = float(rule.get('rate') or 0)
        label = str(rule.get('label') or f'R{idx}').strip()
        if min_pv < 0:
            return jsonify({'error': f'rule #{idx} min_pv must be >= 0'}), 400
        if rate < 0 or rate > 0.35:
            return jsonify({'error': f'rule #{idx} rate must be between 0 and 0.35'}), 400
        normalized_rules.append({'label': label[:24], 'min_pv': min_pv, 'rate': rate})

    normalized_rules.sort(key=lambda x: x['min_pv'], reverse=True)

    with engine.connect() as conn:
        sales = conn.execute(
            text('''
                SELECT id, seller_user_id, base_price, created_at
                FROM network_sales
                WHERE datetime(created_at) >= datetime(:month_start)
                  AND datetime(created_at) < datetime(:month_end)
                ORDER BY id ASC
            '''),
            {'month_start': month_start, 'month_end': month_end}
        ).mappings().all()

        current_c_row = conn.execute(
            text('''
                SELECT COALESCE(SUM(amount_paid), 0) AS c_total
                FROM network_bonus_allocations
                WHERE datetime(created_at) >= datetime(:month_start)
                  AND datetime(created_at) < datetime(:month_end)
            '''),
            {'month_start': month_start, 'month_end': month_end}
        ).mappings().first()

        current_sponsor_rows = conn.execute(
            text('''
                SELECT
                    nba.beneficiary_user_id AS user_id,
                    u.email AS email,
                    COALESCE(SUM(nba.amount_paid), 0) AS total_paid
                FROM network_bonus_allocations nba
                LEFT JOIN users u ON u.id = nba.beneficiary_user_id
                WHERE datetime(nba.created_at) >= datetime(:month_start)
                  AND datetime(nba.created_at) < datetime(:month_end)
                GROUP BY nba.beneficiary_user_id, u.email
            '''),
            {'month_start': month_start, 'month_end': month_end}
        ).mappings().all()

    simulated_gamma = 0.0
    simulated_c_total = 0.0
    simulated_capped_sales = 0
    simulated_by_user = {}
    current_by_user = {}
    email_by_user = {}

    for row in current_sponsor_rows:
        uid = int(row['user_id'])
        current_by_user[uid] = float(row['total_paid'] or 0)
        if row.get('email'):
            email_by_user[uid] = row['email']

    for sale in sales:
        base_price = float(sale.get('base_price') or 0)
        if base_price <= 0:
            continue
        simulated_gamma += base_price

        chain = get_upline_chain(int(sale['seller_user_id']), depth=3)
        raw_sum = 0.0
        sale_allocations = []
        for sponsor_id in chain:
            sponsor_pv = get_group_pv_for_month(int(sponsor_id), month_start, month_end)
            rate, _ = pv_rank_rate(sponsor_pv, rules=normalized_rules)
            if rate > 0:
                amount_raw = round(base_price * rate)
                raw_sum += amount_raw
                sale_allocations.append({'user_id': int(sponsor_id), 'amount_raw': float(amount_raw)})

        cap = base_price * 0.35
        scale_factor = 1.0 if raw_sum <= cap or raw_sum <= 0 else cap / raw_sum
        if raw_sum > cap and raw_sum > 0:
            simulated_capped_sales += 1

        sale_paid_total = 0.0
        for allocation in sale_allocations:
            paid = allocation['amount_raw'] * scale_factor
            sale_paid_total += paid
            uid = allocation['user_id']
            simulated_by_user[uid] = simulated_by_user.get(uid, 0.0) + paid

        simulated_c_total += sale_paid_total

    all_user_ids = sorted(set(list(current_by_user.keys()) + list(simulated_by_user.keys())))
    if all_user_ids:
        placeholders = ','.join([f':id{i}' for i in range(len(all_user_ids))])
        params = {f'id{i}': uid for i, uid in enumerate(all_user_ids)}
        with engine.connect() as conn:
            email_rows = conn.execute(
                text(f'SELECT id, email FROM users WHERE id IN ({placeholders})'),
                params
            ).mappings().all()
        for row in email_rows:
            if row.get('email'):
                email_by_user[int(row['id'])] = row['email']

    sponsor_deltas = []
    for uid in all_user_ids:
        current_paid = float(current_by_user.get(uid, 0.0))
        simulated_paid = float(simulated_by_user.get(uid, 0.0))
        sponsor_deltas.append({
            'user_id': uid,
            'email': email_by_user.get(uid),
            'current_paid': current_paid,
            'simulated_paid': simulated_paid,
            'delta_paid': simulated_paid - current_paid
        })

    sponsor_deltas.sort(key=lambda item: abs(item['delta_paid']), reverse=True)

    current_c_total = float(current_c_row['c_total'] or 0)
    simulated_ratio = 0.0 if simulated_gamma <= 0 else simulated_c_total / simulated_gamma
    current_ratio = 0.0 if simulated_gamma <= 0 else current_c_total / simulated_gamma

    return jsonify({
        'period': month_start[:7],
        'sales_count': len(sales),
        'gamma': simulated_gamma,
        'current_c_total': current_c_total,
        'current_ratio': current_ratio,
        'simulated_c_total': simulated_c_total,
        'simulated_ratio': simulated_ratio,
        'delta_c_total': simulated_c_total - current_c_total,
        'delta_ratio': simulated_ratio - current_ratio,
        'simulated_capped_sales': simulated_capped_sales,
        'within_limit': simulated_ratio <= 0.35 if simulated_gamma > 0 else True,
        'sponsor_deltas': sponsor_deltas[:10]
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)


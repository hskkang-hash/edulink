from flask import Flask, request, jsonify, send_from_directory, make_response
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
with engine.begin() as conn:
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
            status TEXT DEFAULT 'open',
            deadline TEXT,
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
    if 'status' not in posting_cols:
        conn.execute(text("ALTER TABLE postings ADD COLUMN status TEXT DEFAULT 'open'"))
    if 'deadline' not in posting_cols:
        conn.execute(text('ALTER TABLE postings ADD COLUMN deadline TEXT'))

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


    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS instructor_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            full_name TEXT,
            birth_date TEXT,
            phone TEXT,
            subjects TEXT,
            regions TEXT,
            available_hours TEXT,
            education_level TEXT,
            certifications TEXT,
            business_number TEXT,
            bank_name TEXT,
            bank_account_masked TEXT,
            background_check_consent INTEGER DEFAULT 0,
            child_abuse_consent INTEGER DEFAULT 0,
            withholding_consent INTEGER DEFAULT 0,
            id_doc_url TEXT,
            cert_doc_url TEXT,
            status TEXT DEFAULT 'pending',
            admin_note TEXT,
            reviewed_by INTEGER,
            reviewed_at TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    '''))

    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            posting_id INTEGER,
            instructor_id INTEGER,
            org_id INTEGER,
            scheduled_at TEXT,
            scheduled_duration_minutes INTEGER DEFAULT 60,
            checkin_at TEXT,
            checkin_lat REAL,
            checkin_lng REAL,
            completed_at TEXT,
            actual_duration_minutes INTEGER,
            status TEXT DEFAULT 'scheduled',
            journal_content TEXT,
            next_assignment TEXT,
            student_rating INTEGER,
            gross_amount INTEGER,
            withholding_amount INTEGER,
            net_amount INTEGER,
            created_at TEXT,
            updated_at TEXT
        )
    '''))

    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            reviewer_id INTEGER,
            instructor_id INTEGER,
            rating INTEGER,
            comment TEXT,
            reviewer_type TEXT DEFAULT 'institution',
            created_at TEXT
        )
    '''))

    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS sos_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER,
            title TEXT,
            subject TEXT,
            region TEXT,
            scheduled_at TEXT,
            duration_minutes INTEGER DEFAULT 60,
            rate INTEGER,
            status TEXT DEFAULT 'open',
            accepted_by INTEGER,
            accepted_at TEXT,
            created_at TEXT
        )
    '''))

    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            posting_id INTEGER,
            application_id INTEGER,
            institution_id INTEGER,
            instructor_id INTEGER,
            title TEXT,
            content TEXT,
            status TEXT DEFAULT 'draft',
            institution_signed_at TEXT,
            instructor_signed_at TEXT,
            expires_at TEXT,
            file_url TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    '''))

    conn.execute(text('''
        CREATE TABLE IF NOT EXISTS escrow_charges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            institution_id INTEGER,
            instructor_id INTEGER,
            amount INTEGER,
            status TEXT DEFAULT 'held',
            held_at TEXT,
            released_at TEXT,
            refunded_at TEXT,
            refund_reason TEXT,
            created_at TEXT
        )
    '''))

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


@app.route('/assets/<path:filename>')
def serve_assets(filename):
    assets_dir = Path(__file__).resolve().parent.parent / 'assets'
    return send_from_directory(str(assets_dir), filename)


def _serve_frontend_public_file(filename):
    frontend_dir = Path(__file__).resolve().parent.parent / 'frontend'
    target = frontend_dir / filename
    if not target.exists():
        return jsonify({'error': 'not found'}), 404
    return send_from_directory(str(frontend_dir), filename)


@app.route('/privacy.html')
def privacy_page():
    return _serve_frontend_public_file('privacy.html')


@app.route('/terms.html')
def terms_page():
    return _serve_frontend_public_file('terms.html')


@app.route('/contact.html')
def contact_page():
    return _serve_frontend_public_file('contact.html')


@app.route('/about.html')
def about_page():
    return _serve_frontend_public_file('about.html')


@app.route('/adsense-disclosure.html')
def adsense_disclosure_page():
    return _serve_frontend_public_file('adsense-disclosure.html')


@app.route('/robots.txt')
def robots_txt():
    return _serve_frontend_public_file('robots.txt')


@app.route('/sitemap.xml')
def sitemap_xml():
    return _serve_frontend_public_file('sitemap.xml')


@app.route('/ads.txt')
def ads_txt():
    return _serve_frontend_public_file('ads.txt')


@app.route('/content-hub.html')
def content_hub_page():
    return _serve_frontend_public_file('content-hub.html')


@app.route('/content/<path:filename>')
def content_pages(filename):
    frontend_content_dir = Path(__file__).resolve().parent.parent / 'frontend' / 'content'
    target = frontend_content_dir / filename
    if not target.exists():
        return jsonify({'error': 'not found'}), 404
    return send_from_directory(str(frontend_content_dir), filename)


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


def normalize_role(role):
    return str(role or 'instructor').strip().lower()


def has_role(user, *roles):
    normalized = normalize_role((user or {}).get('role'))
    if normalized in roles:
        return True
    if normalized == 'super_admin' and 'admin' in roles:
        return True
    return False


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def table_exists(conn, table_name):
    row = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type = 'table' AND name = :name"),
        {'name': table_name}
    ).first()
    return row is not None


def get_instructor_tax_numbers(user_id, tax_year):
    params = {'student_id': user_id, 'year': str(tax_year)}
    with engine.connect() as conn:
        row = conn.execute(
            text('''
                SELECT COALESCE(SUM(p.rate), 0) AS gross_income
                FROM applications a
                JOIN postings p ON p.id = a.posting_id
                WHERE a.student_id = :student_id
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
    sort_by = request.args.get('sort_by', 'newest').strip().lower()
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

    sort_sql = ' ORDER BY id DESC'
    if sort_by == 'rate_desc':
        sort_sql = ' ORDER BY rate DESC, id DESC'
    elif sort_by == 'deadline_soon':
        sort_sql = " ORDER BY CASE WHEN deadline IS NULL OR deadline = '' THEN 1 ELSE 0 END ASC, deadline ASC, id DESC"

    query = text(
        'SELECT id, title, subject, region, rate, status, deadline, created_at, owner_id FROM postings'
        + where_sql
        + sort_sql
    )

    with engine.connect() as conn:
        result = conn.execute(query, params).mappings().all()
        return jsonify([dict(row) for row in result])


@app.route('/postings/settlement-summary', methods=['GET'])
def get_postings_settlement_summary():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not has_role(user, 'institution'):
        return jsonify({'error': 'Only institutions can view settlement summary'}), 403

    month = (request.args.get('month') or '').strip()
    if not month:
        month = datetime.now().strftime('%Y-%m')
    if len(month) != 7 or month[4] != '-':
        return jsonify({'error': 'month must be YYYY-MM'}), 400

    export_format = (request.args.get('format') or 'json').strip().lower()

    with engine.connect() as conn:
        rows = conn.execute(
            text('''
                SELECT
                    s.instructor_id AS student_id,
                    COALESCE(u.email, '') AS instructor_email,
                    COUNT(CASE WHEN s.status = 'completed' THEN 1 END) AS approved_sessions,
                    COUNT(CASE WHEN s.status IN ('scheduled', 'in_progress') THEN 1 END) AS pending_sessions,
                    COALESCE(SUM(CASE WHEN s.status = 'completed' THEN s.gross_amount ELSE 0 END), 0) AS total_gross,
                    COALESCE(SUM(CASE WHEN s.status = 'completed' THEN s.withholding_amount ELSE 0 END), 0) AS total_withholding,
                    COALESCE(SUM(CASE WHEN s.status = 'completed' THEN s.net_amount ELSE 0 END), 0) AS total_payment
                FROM sessions s
                LEFT JOIN users u ON u.id = s.instructor_id
                WHERE s.org_id = :owner_id
                  AND strftime('%Y-%m', COALESCE(s.completed_at, s.scheduled_at, s.created_at)) = :month
                GROUP BY s.instructor_id, u.email
                ORDER BY total_payment DESC, approved_sessions DESC
            '''),
            {'owner_id': user['user_id'], 'month': month}
        ).mappings().all()

    total_settled = int(sum(int(row['total_payment'] or 0) for row in rows))
    approved_sessions = int(sum(int(row['approved_sessions'] or 0) for row in rows))
    pending_rows = int(sum(int(row['pending_sessions'] or 0) for row in rows))
    platform_fee = int(round(total_settled * 0.05))

    items = [
        {
            'student_id': row['student_id'],
            'instructor_email': row['instructor_email'] or f"#{row['student_id']}",
            'approved_sessions': int(row['approved_sessions'] or 0),
            'pending_sessions': int(row['pending_sessions'] or 0),
            'total_gross': int(row['total_gross'] or 0),
            'total_withholding': int(row['total_withholding'] or 0),
            'total_payment': int(row['total_payment'] or 0),
            'payout_status': 'paid' if int(row['pending_sessions'] or 0) == 0 and int(row['approved_sessions'] or 0) > 0 else 'pending'
        }
        for row in rows
    ]

    if export_format == 'csv':
        csv_lines = [
            'month,instructor_id,instructor_email,approved_sessions,pending_sessions,total_gross,total_withholding,total_payment,payout_status'
        ]
        for item in items:
            csv_lines.append(
                f"{month},{item['student_id']},\"{str(item['instructor_email']).replace('"', '""')}\",{item['approved_sessions']},{item['pending_sessions']},{item['total_gross']},{item['total_withholding']},{item['total_payment']},{item['payout_status']}"
            )
        response = make_response('\n'.join(csv_lines))
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=settlement_summary_{month}.csv'
        return response

    return jsonify({
        'month': month,
        'total_settled': total_settled,
        'platform_fee': platform_fee,
        'approved_sessions': approved_sessions,
        'pending_count': int(pending_rows or 0),
        'items': items
    })


@app.route('/district/institutions', methods=['GET'])
def get_district_institutions():
    """List institutions in the district with their statistics"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    if not has_role(user, 'district'):
        return jsonify({'error': 'Only district users can view institution list'}), 403

    with engine.connect() as conn:
        # Get all institutions (users with role 'institution' or 'student')
        institutions = conn.execute(
            text('''
                SELECT DISTINCT
                    u.id,
                    u.email,
                    u.organization,
                    COUNT(DISTINCT p.id) as postings_count,
                    COUNT(DISTINCT CASE WHEN a.status = 'approved' THEN a.id END) as approved_count,
                    SUM(CASE WHEN a.status = 'approved' THEN p.rate ELSE 0 END) as total_revenue
                FROM users u
                LEFT JOIN postings p ON p.owner_id = u.id
                LEFT JOIN applications a ON a.posting_id = p.id
                WHERE u.role IN ('institution', 'student')
                GROUP BY u.id, u.email, u.organization
                ORDER BY total_revenue DESC
            ''')
        ).mappings().all()

        return jsonify({
            'institutions': [
                {
                    'id': inst['id'],
                    'email': inst['email'],
                    'organization': inst['organization'] or f"Org #{inst['id']}",
                    'postings_count': int(inst['postings_count'] or 0),
                    'approved_count': int(inst['approved_count'] or 0),
                    'total_revenue': int(inst['total_revenue'] or 0)
                }
                for inst in institutions
            ],
            'total_institutions': len(institutions)
        })


@app.route('/district/regional-comparison', methods=['GET'])
def get_district_regional_comparison():
    """Get regional comparison data for district dashboard"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    if not has_role(user, 'district'):
        return jsonify({'error': 'Only district users can view regional data'}), 403

    with engine.connect() as conn:
        # Get posting statistics by region
        regions = conn.execute(
            text('''
                SELECT
                    p.region,
                    COUNT(DISTINCT p.id) as postings_count,
                    COUNT(DISTINCT a.id) as applications_count,
                    COUNT(DISTINCT CASE WHEN a.status = 'approved' THEN a.id END) as approved_count,
                    AVG(p.rate) as avg_rate
                FROM postings p
                LEFT JOIN applications a ON a.posting_id = p.id
                WHERE p.region IS NOT NULL AND p.region != ''
                GROUP BY p.region
                ORDER BY postings_count DESC
            ''')
        ).mappings().all()

        return jsonify({
            'regions': [
                {
                    'region': region['region'] or 'Unknown',
                    'postings_count': int(region['postings_count'] or 0),
                    'applications_count': int(region['applications_count'] or 0),
                    'approved_count': int(region['approved_count'] or 0),
                    'avg_rate': int(region['avg_rate'] or 0)
                }
                for region in regions
            ],
            'total_regions': len(regions)
        })


@app.route('/district/budget-summary', methods=['GET'])
def get_district_budget_summary():
    """Get budget usage summary for district dashboard"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    if not has_role(user, 'district'):
        return jsonify({'error': 'Only district users can view budget data'}), 403

    with engine.connect() as conn:
        # Get budget stats aggregated by institution
        budget_stats = conn.execute(
            text('''
                SELECT
                    u.id,
                    u.organization,
                    COUNT(DISTINCT p.id) as postings_count,
                    COUNT(DISTINCT CASE WHEN a.status = 'approved' THEN a.id END) as approved_sessions,
                    SUM(CASE WHEN a.status = 'approved' THEN p.rate ELSE 0 END) as total_spent
                FROM users u
                LEFT JOIN postings p ON p.owner_id = u.id
                LEFT JOIN applications a ON a.posting_id = p.id
                WHERE u.role IN ('institution', 'student')
                GROUP BY u.id, u.organization
                ORDER BY total_spent DESC
            ''')
        ).mappings().all()

        total_budget = sum(int(stat['total_spent'] or 0) for stat in budget_stats)
        total_postings = sum(int(stat['postings_count'] or 0) for stat in budget_stats)
        total_sessions = sum(int(stat['approved_sessions'] or 0) for stat in budget_stats)

        return jsonify({
            'summary': {
                'total_institutions': len(budget_stats),
                'total_postings': total_postings,
                'total_sessions': total_sessions,
                'total_budget_used': total_budget,
                'avg_per_institution': int(total_budget / len(budget_stats)) if budget_stats else 0
            },
            'institutions': [
                {
                    'organization': stat['organization'] or f"Org #{stat['id']}",
                    'postings_count': int(stat['postings_count'] or 0),
                    'approved_sessions': int(stat['approved_sessions'] or 0),
                    'total_spent': int(stat['total_spent'] or 0),
                    'budget_percentage': round((int(stat['total_spent'] or 0) / total_budget * 100), 1) if total_budget > 0 else 0
                }
                for stat in budget_stats
            ]
        })


@app.route('/admin/users', methods=['GET'])
def get_admin_users():
    """List all users for admin management"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    if not has_role(user, 'admin'):
        return jsonify({'error': 'Only admins can view user list'}), 403

    with engine.connect() as conn:
        users = conn.execute(
            text('''
                SELECT
                    u.id,
                    u.email,
                    u.role,
                    u.organization,
                    u.created_at,
                    COUNT(DISTINCT p.id) as postings_count,
                    COUNT(DISTINCT a.id) as applications_count
                FROM users u
                LEFT JOIN postings p ON p.owner_id = u.id
                LEFT JOIN applications a ON a.student_id = u.id
                GROUP BY u.id, u.email, u.role, u.organization, u.created_at
                ORDER BY u.created_at DESC
            ''')
        ).mappings().all()

        return jsonify({
            'users': [
                {
                    'id': usr['id'],
                    'email': usr['email'],
                    'role': usr['role'] or 'instructor',
                    'organization': usr['organization'],
                    'created_at': usr['created_at'],
                    'postings_count': int(usr['postings_count'] or 0),
                    'applications_count': int(usr['applications_count'] or 0)
                }
                for usr in users
            ],
            'total_users': len(users)
        })


@app.route('/admin/users/<int:user_id>/role', methods=['PATCH'])
def update_user_role(user_id):
    """Update user role for admin management"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    if not has_role(user, 'admin'):
        return jsonify({'error': 'Only admins can modify user roles'}), 403

    data = request.get_json() or {}
    new_role = data.get('role')

    if not new_role or new_role not in ['instructor', 'institution', 'district', 'admin', 'student', 'super_admin']:
        return jsonify({'error': 'Invalid role'}), 400

    with engine.begin() as conn:
        conn.execute(
            text('UPDATE users SET role = :role WHERE id = :user_id'),
            {'role': new_role, 'user_id': user_id}
        )

    log_tax_event(user['user_id'], 'admin_user_role_changed', f'target_user_id={user_id};new_role={new_role}')
    return jsonify({'message': f'User {user_id} role updated to {new_role}'})


@app.route('/admin/platform-summary', methods=['GET'])
def get_admin_platform_summary():
    """Get platform-wide summary for admin dashboard"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    if not has_role(user, 'admin'):
        return jsonify({'error': 'Only admins can view platform summary'}), 403

    with engine.connect() as conn:
        # Overall stats
        total_users = conn.execute(
            text('SELECT COUNT(*) as count FROM users')
        ).mappings().first()['count']

        total_postings = conn.execute(
            text('SELECT COUNT(*) as count FROM postings')
        ).mappings().first()['count']

        total_applications = conn.execute(
            text('SELECT COUNT(*) as count FROM applications')
        ).mappings().first()['count']

        application_status = conn.execute(
            text('''
                SELECT status, COUNT(*) as count
                FROM applications
                GROUP BY status
            ''')
        ).mappings().all()

        status_map = {row['status']: int(row['count']) for row in application_status}

        # User role breakdown
        role_breakdown = conn.execute(
            text('''
                SELECT role, COUNT(*) as count
                FROM users
                GROUP BY role
            ''')
        ).mappings().all()

        return jsonify({
            'platform': {
                'total_users': int(total_users),
                'total_postings': int(total_postings),
                'total_applications': int(total_applications),
                'applications_approved': int(status_map.get('approved', 0)),
                'applications_pending': int(status_map.get('pending', 0)),
                'applications_rejected': int(status_map.get('rejected', 0))
            },
            'role_breakdown': {
                'instructor': next((int(r['count']) for r in role_breakdown if r['role'] == 'instructor'), 0),
                'institution': next((int(r['count']) for r in role_breakdown if r['role'] in ['institution', 'student']), 0),
                'district': next((int(r['count']) for r in role_breakdown if r['role'] == 'district'), 0),
                'admin': next((int(r['count']) for r in role_breakdown if r['role'] in ['admin', 'super_admin']), 0)
            }
        })


@app.route('/postings', methods=['POST'])
def create_posting():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not (has_role(user, 'institution') or has_role(user, 'instructor')):
        return jsonify({'error': 'Only institutions can create postings'}), 403

    data = request.get_json()
    for key in ('title', 'subject', 'region', 'rate'):
        if key not in data:
            return jsonify({'error': f'{key} required'}), 400

    with engine.begin() as conn:
        conn.execute(
            text('INSERT INTO postings (title, subject, region, rate, status, deadline, created_at, owner_id) VALUES (:title,:subject,:region,:rate,:status,:deadline,:created_at,:owner_id)'),
            {
                'title': data['title'],
                'subject': data['subject'],
                'region': data['region'],
                'rate': data['rate'],
                'status': data.get('status', 'open'),
                'deadline': data.get('deadline'),
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
            text('SELECT id, title, subject, region, rate, status, deadline, created_at, owner_id FROM postings WHERE id = :id'),
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
            text('UPDATE postings SET title=:title, subject=:subject, region=:region, rate=:rate, status=:status, deadline=:deadline WHERE id=:id'),
            {
                'title': data.get('title', ''),
                'subject': data.get('subject', ''),
                'region': data.get('region', ''),
                'rate': data.get('rate', 0),
                'status': data.get('status', 'open'),
                'deadline': data.get('deadline'),
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

    applicant_role = normalize_role(user.get('role'))
    if applicant_role not in ('student', 'instructor'):
        return jsonify({'error': 'Only instructors can apply'}), 403

    data = request.get_json()
    if 'posting_id' not in data:
        return jsonify({'error': 'posting_id required'}), 400

    status = data.get('status', 'pending')
    with engine.begin() as conn:
        posting = conn.execute(
            text('SELECT id, status FROM postings WHERE id = :posting_id'),
            {'posting_id': data['posting_id']}
        ).mappings().first()
        if not posting:
            return jsonify({'error': 'Posting not found'}), 404
        if posting['status'] not in ('open', 'assigned'):
            return jsonify({'error': 'Posting is not open for applications'}), 409

        if applicant_role == 'instructor' and table_exists(conn, 'instructor_profiles'):
            profile = conn.execute(
                text('''
                    SELECT status, background_check_consent, child_abuse_consent
                    FROM instructor_profiles
                    WHERE user_id = :user_id
                '''),
                {'user_id': user['user_id']}
            ).mappings().first()
            if not profile:
                return jsonify({'error': 'Complete instructor onboarding before applying'}), 403
            if profile['status'] != 'approved':
                return jsonify({'error': 'Instructor profile approval is required before applying'}), 403
            if not profile['background_check_consent'] or not profile['child_abuse_consent']:
                return jsonify({'error': 'Background and child safety consents are required before applying'}), 403

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
    posting_id = request.args.get('posting_id', '').strip()
    if posting_id:
        try:
            posting_id = int(posting_id)
        except ValueError:
            return jsonify({'error': 'Invalid posting_id filter'}), 400

    sort_mode = request.args.get('sort', 'newest').strip().lower()
    allowed_sorts = {'newest', 'oldest', 'status'}
    if sort_mode not in allowed_sorts:
        return jsonify({'error': 'Invalid sort option'}), 400

    with engine.connect() as conn:
        owner_view = has_role(user, 'institution') or has_role(user, 'instructor')
        if owner_view:
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

        if posting_id:
            query += ' AND a.posting_id = :posting_id'
            params['posting_id'] = posting_id

        if search_query:
            query += ' AND ('
            query += 'LOWER(p.title) LIKE :search_like'
            params['search_like'] = f"%{search_query}%"
            if owner_view:
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

    if not (has_role(user, 'institution') or has_role(user, 'instructor')):
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

    if not (has_role(user, 'institution') or has_role(user, 'instructor')):
        return jsonify({'error': 'Only institutions can update applications'}), 403

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

        if status == 'approved':
            conn.execute(
                text('''
                    UPDATE postings
                    SET status = 'assigned'
                    WHERE id = (
                        SELECT posting_id FROM applications WHERE id = :application_id
                    )
                '''),
                {'application_id': application_id}
            )

    return jsonify({'message': 'Application updated', 'status': status})


@app.route('/applications/<int:application_id>', methods=['DELETE'])
def cancel_application(application_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    if not has_role(user, 'instructor'):
        return jsonify({'error': 'Only instructors can cancel applications'}), 403

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
        if has_role(user, 'institution'):
            postings_count = conn.execute(
                text('SELECT COUNT(*) AS count FROM postings WHERE owner_id = :owner_id'),
                {'owner_id': user['user_id']}
            ).mappings().first()['count']

            sessions_available = table_exists(conn, 'sessions')
            reviews_available = table_exists(conn, 'reviews')

            today_sessions_count = 0
            if sessions_available:
                today_sessions_count = conn.execute(
                    text('''
                        SELECT COUNT(*) AS count
                        FROM sessions
                        WHERE org_id = :owner_id
                          AND date(scheduled_at) = date('now')
                    '''),
                    {'owner_id': user['user_id']}
                ).mappings().first()['count']

            new_postings_count = conn.execute(
                text('''
                    SELECT COUNT(*) AS count
                    FROM postings
                    WHERE owner_id = :owner_id
                      AND datetime(created_at) >= datetime('now', '-7 days')
                '''),
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

            month_key = datetime.now().strftime('%Y-%m')
            month_sessions = {'total_sessions': 0, 'month_settlement_amount': 0}
            month_rating = {'avg_rating': 0}
            review_pending_count = 0
            today_sessions = []
            if sessions_available:
                month_sessions = conn.execute(
                    text('''
                        SELECT
                            COUNT(*) AS total_sessions,
                            COALESCE(SUM(CASE WHEN status = 'completed' THEN net_amount ELSE 0 END), 0) AS month_settlement_amount
                        FROM sessions
                        WHERE org_id = :owner_id
                          AND strftime('%Y-%m', COALESCE(completed_at, scheduled_at, created_at)) = :month_key
                    '''),
                    {'owner_id': user['user_id'], 'month_key': month_key}
                ).mappings().first() or month_sessions

                if reviews_available:
                    month_rating = conn.execute(
                        text('''
                            SELECT COALESCE(AVG(r.rating), 0) AS avg_rating
                            FROM reviews r
                            JOIN sessions s ON s.id = r.session_id
                            WHERE s.org_id = :owner_id
                              AND strftime('%Y-%m', COALESCE(s.completed_at, s.scheduled_at, s.created_at)) = :month_key
                        '''),
                        {'owner_id': user['user_id'], 'month_key': month_key}
                    ).mappings().first() or month_rating

                    review_pending_count = conn.execute(
                        text('''
                            SELECT COUNT(*) AS count
                            FROM sessions s
                            LEFT JOIN reviews r ON r.session_id = s.id
                            WHERE s.org_id = :owner_id
                              AND s.status = 'completed'
                              AND r.id IS NULL
                        '''),
                        {'owner_id': user['user_id']}
                    ).mappings().first()['count']

                today_sessions = conn.execute(
                    text('''
                        SELECT
                            s.id,
                            s.posting_id,
                            COALESCE(p.subject, '-') AS subject,
                            COALESCE(u.email, ('#' || s.instructor_id)) AS instructor_name,
                            s.status,
                            s.scheduled_duration_minutes,
                            s.actual_duration_minutes,
                            s.gross_amount,
                            s.net_amount,
                            s.scheduled_at
                        FROM sessions s
                        LEFT JOIN postings p ON p.id = s.posting_id
                        LEFT JOIN users u ON u.id = s.instructor_id
                        WHERE s.org_id = :owner_id
                        ORDER BY datetime(s.scheduled_at) DESC, s.id DESC
                        LIMIT 8
                    '''),
                    {'owner_id': user['user_id']}
                ).mappings().all()

            applications_total = sum(status_counts.values())
            return jsonify({
                'role': 'institution',
                'postings_count': postings_count,
                'applications_total': applications_total,
                'pending_count': status_counts['pending'],
                'approved_count': status_counts['approved'],
                'rejected_count': status_counts['rejected'],
                'today_sessions_count': int(today_sessions_count or 0),
                'new_postings_count': int(new_postings_count or 0),
                'settlement_pending_count': int(status_counts['approved'] or 0),
                'review_pending_count': int(review_pending_count or 0),
                'month_total_sessions': int((month_sessions or {}).get('total_sessions', 0) or 0),
                'month_avg_instructor_rating': float((month_rating or {}).get('avg_rating', 0) or 0),
                'month_settlement_amount': int((month_sessions or {}).get('month_settlement_amount', 0) or 0),
                'today_sessions': [dict(row) for row in today_sessions]
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

        if has_role(user, 'admin'):
            total_users = conn.execute(
                text('SELECT COUNT(*) AS count FROM users')
            ).mappings().first()['count']
            total_postings = conn.execute(
                text('SELECT COUNT(*) AS count FROM postings')
            ).mappings().first()['count']
            return jsonify({
                'role': 'admin',
                'applications_total': applications_total,
                'pending_count': status_counts['pending'],
                'approved_count': status_counts['approved'],
                'rejected_count': status_counts['rejected'],
                'postings_count': total_postings,
                'users_count': total_users
            })

        if has_role(user, 'instructor'):
            profiles_available = table_exists(conn, 'instructor_profiles')
            sessions_available = table_exists(conn, 'sessions')
            postings_available = table_exists(conn, 'postings')

            profile_row = None
            if profiles_available:
                profile_row = conn.execute(
                    text('''
                        SELECT status, reviewed_at
                        FROM instructor_profiles
                        WHERE user_id = :user_id
                    '''),
                    {'user_id': user['user_id']}
                ).mappings().first()

            session_summary = {
                'total_sessions': 0,
                'upcoming_sessions_count': 0,
                'completed_sessions_count': 0,
                'total_gross_amount': 0,
                'total_withholding_amount': 0,
                'total_net_amount': 0,
            }
            upcoming_sessions = []
            if sessions_available:
                session_summary = conn.execute(
                    text('''
                        SELECT
                            COUNT(*) AS total_sessions,
                            COALESCE(SUM(CASE WHEN status IN ('scheduled', 'in_progress') THEN 1 ELSE 0 END), 0) AS upcoming_sessions_count,
                            COALESCE(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END), 0) AS completed_sessions_count,
                            COALESCE(SUM(CASE WHEN status = 'completed' THEN gross_amount ELSE 0 END), 0) AS total_gross_amount,
                            COALESCE(SUM(CASE WHEN status = 'completed' THEN withholding_amount ELSE 0 END), 0) AS total_withholding_amount,
                            COALESCE(SUM(CASE WHEN status = 'completed' THEN net_amount ELSE 0 END), 0) AS total_net_amount
                        FROM sessions
                        WHERE instructor_id = :user_id
                    '''),
                    {'user_id': user['user_id']}
                ).mappings().first() or session_summary

                upcoming_sessions = conn.execute(
                    text('''
                        SELECT
                            s.id,
                            s.posting_id,
                            s.status,
                            s.scheduled_at,
                            s.scheduled_duration_minutes,
                            p.title,
                            p.subject,
                            COALESCE(u.organization, u.email, '') AS organization
                        FROM sessions s
                        LEFT JOIN postings p ON p.id = s.posting_id
                        LEFT JOIN users u ON u.id = s.org_id
                        WHERE s.instructor_id = :user_id
                          AND s.status IN ('scheduled', 'in_progress')
                        ORDER BY datetime(s.scheduled_at) ASC, s.id ASC
                        LIMIT 5
                    '''),
                    {'user_id': user['user_id']}
                ).mappings().all()

            postings_count = 0
            if postings_available:
                postings_count = conn.execute(
                    text('SELECT COUNT(*) AS count FROM postings WHERE owner_id = :owner_id'),
                    {'owner_id': user['user_id']}
                ).mappings().first()['count']

            return jsonify({
                'role': 'instructor',
                'applications_total': applications_total,
                'pending_count': status_counts['pending'],
                'approved_count': status_counts['approved'],
                'rejected_count': status_counts['rejected'],
                'postings_count': postings_count,
                'profile_status': profile_row['status'] if profile_row else 'not_submitted',
                'profile_reviewed_at': profile_row['reviewed_at'] if profile_row else None,
                'upcoming_sessions_count': session_summary['upcoming_sessions_count'],
                'completed_sessions_count': session_summary['completed_sessions_count'],
                'total_sessions': session_summary['total_sessions'],
                'income_summary': {
                    'gross_amount': session_summary['total_gross_amount'],
                    'withholding_amount': session_summary['total_withholding_amount'],
                    'net_amount': session_summary['total_net_amount'],
                },
                'upcoming_sessions': [dict(row) for row in upcoming_sessions],
            })

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
        if has_role(user, 'institution'):
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

        if has_role(user, 'instructor'):
            rows = conn.execute(
                text('''
                    SELECT * FROM (
                        SELECT
                            'session_scheduled' AS type,
                            s.id AS ref_id,
                            s.posting_id AS posting_id,
                            p.title AS title,
                            s.status AS status,
                            s.scheduled_at AS created_at
                        FROM sessions s
                        LEFT JOIN postings p ON p.id = s.posting_id
                        WHERE s.instructor_id = :user_id
                          AND s.status IN ('scheduled', 'in_progress')
                          AND datetime(s.scheduled_at) >= datetime('now', :since_window)

                        UNION ALL

                        SELECT
                            'session_completed' AS type,
                            s.id AS ref_id,
                            s.posting_id AS posting_id,
                            p.title AS title,
                            s.status AS status,
                            s.completed_at AS created_at
                        FROM sessions s
                        LEFT JOIN postings p ON p.id = s.posting_id
                        WHERE s.instructor_id = :user_id
                          AND s.status = 'completed'
                          AND s.completed_at IS NOT NULL
                          AND datetime(s.completed_at) >= datetime('now', :since_window)

                        UNION ALL

                        SELECT
                            'application_submitted' AS type,
                            a.id AS ref_id,
                            a.posting_id AS posting_id,
                            p.title AS title,
                            a.status AS status,
                            a.created_at AS created_at
                        FROM applications a
                        JOIN postings p ON p.id = a.posting_id
                        WHERE a.student_id = :user_id
                          AND datetime(a.created_at) >= datetime('now', :since_window)

                        UNION ALL

                        SELECT
                            CASE WHEN ip.reviewed_at IS NULL THEN 'profile_submitted' ELSE 'profile_reviewed' END AS type,
                            ip.id AS ref_id,
                            NULL AS posting_id,
                            COALESCE(ip.full_name, 'Instructor profile') AS title,
                            ip.status AS status,
                            COALESCE(ip.reviewed_at, ip.updated_at, ip.created_at) AS created_at
                        FROM instructor_profiles ip
                        WHERE ip.user_id = :user_id
                          AND datetime(COALESCE(ip.reviewed_at, ip.updated_at, ip.created_at)) >= datetime('now', :since_window)
                    )
                    ORDER BY datetime(created_at) DESC, ref_id DESC
                    LIMIT 7
                '''),
                {'user_id': user['user_id'], 'since_window': since_window}
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
# ===== 강사 프로필 온보딩 API =====

@app.route('/instructor/profile', methods=['POST'])
def create_instructor_profile():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not has_role(user, 'instructor'):
        return jsonify({'error': 'Instructor only'}), 403

    data = request.get_json() or {}
    required = ['full_name', 'phone', 'subjects', 'regions']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    if not data.get('background_check_consent') or not data.get('child_abuse_consent') or not data.get('withholding_consent'):
        return jsonify({'error': 'All consent fields are required'}), 400

    with engine.begin() as conn:
        existing = conn.execute(
            text('SELECT id FROM instructor_profiles WHERE user_id = :uid'),
            {'uid': user['user_id']}
        ).fetchone()
        if existing:
            return jsonify({'error': 'Profile already exists. Use PUT to update.'}), 409

        import json as _json
        subjects_str = _json.dumps(data.get('subjects', []) if isinstance(data.get('subjects'), list) else [data.get('subjects', '')])
        regions_str = _json.dumps(data.get('regions', []) if isinstance(data.get('regions'), list) else [data.get('regions', '')])
        now = now_iso()
        conn.execute(text('''
            INSERT INTO instructor_profiles
                (user_id, full_name, birth_date, phone, subjects, regions, available_hours,
                 education_level, certifications, business_number, bank_name, bank_account_masked,
                 background_check_consent, child_abuse_consent, withholding_consent,
                 id_doc_url, cert_doc_url, status, created_at, updated_at)
            VALUES
                (:uid, :full_name, :birth_date, :phone, :subjects, :regions, :available_hours,
                 :edu, :certs, :biz_no, :bank_name, :bank_masked,
                 :bg_consent, :child_consent, :wh_consent,
                 :id_doc, :cert_doc, 'pending', :created_at, :updated_at)
        '''), {
            'uid': user['user_id'],
            'full_name': data.get('full_name', '').strip(),
            'birth_date': data.get('birth_date', ''),
            'phone': data.get('phone', '').strip(),
            'subjects': subjects_str,
            'regions': regions_str,
            'available_hours': data.get('available_hours', ''),
            'edu': data.get('education_level', ''),
            'certs': data.get('certifications', ''),
            'biz_no': data.get('business_number', ''),
            'bank_name': data.get('bank_name', ''),
            'bank_masked': data.get('bank_account_masked', ''),
            'bg_consent': 1 if data.get('background_check_consent') else 0,
            'child_consent': 1 if data.get('child_abuse_consent') else 0,
            'wh_consent': 1 if data.get('withholding_consent') else 0,
            'id_doc': data.get('id_doc_url', ''),
            'cert_doc': data.get('cert_doc_url', ''),
            'created_at': now,
            'updated_at': now,
        })

    return jsonify({'message': 'Profile created. Pending admin review.', 'status': 'pending'}), 201


@app.route('/instructor/profile', methods=['GET'])
def get_instructor_profile():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    target_id = user['user_id']
    if has_role(user, 'admin', 'super_admin'):
        target_id_param = request.args.get('user_id', type=int)
        if target_id_param:
            target_id = target_id_param

    with engine.connect() as conn:
        row = conn.execute(
            text('SELECT * FROM instructor_profiles WHERE user_id = :uid'),
            {'uid': target_id}
        ).mappings().first()

    if not row:
        return jsonify({'error': 'Profile not found'}), 404
    return jsonify(dict(row))


@app.route('/instructor/profile', methods=['PUT'])
def update_instructor_profile():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not has_role(user, 'instructor'):
        return jsonify({'error': 'Instructor only'}), 403

    data = request.get_json() or {}
    import json as _json

    updatable = ['full_name', 'birth_date', 'phone', 'subjects', 'regions',
                 'available_hours', 'education_level', 'certifications',
                 'business_number', 'bank_name', 'bank_account_masked',
                 'background_check_consent', 'child_abuse_consent', 'withholding_consent',
                 'id_doc_url', 'cert_doc_url']

    set_parts = []
    params = {'uid': user['user_id'], 'updated_at': now_iso()}
    for field in updatable:
        if field not in data:
            continue
        val = data[field]
        if field in ('subjects', 'regions') and isinstance(val, list):
            val = _json.dumps(val)
        if field in ('background_check_consent', 'child_abuse_consent', 'withholding_consent'):
            val = 1 if val else 0
        set_parts.append(f'{field} = :{field}')
        params[field] = val

    if not set_parts:
        return jsonify({'error': 'No fields to update'}), 400

    set_parts.append('updated_at = :updated_at')
    # Re-set to pending when profile changes
    set_parts.append("status = 'pending'")

    with engine.begin() as conn:
        result = conn.execute(
            text(f'UPDATE instructor_profiles SET {", ".join(set_parts)} WHERE user_id = :uid'),
            params
        )
        if result.rowcount == 0:
            return jsonify({'error': 'Profile not found. Create it first via POST.'}), 404

    return jsonify({'message': 'Profile updated. Status reset to pending.', 'status': 'pending'})


@app.route('/instructor/profile/status', methods=['GET'])
def instructor_profile_status():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    with engine.connect() as conn:
        row = conn.execute(
            text('SELECT status, admin_note, reviewed_at FROM instructor_profiles WHERE user_id = :uid'),
            {'uid': user['user_id']}
        ).mappings().first()

    if not row:
        return jsonify({'status': 'not_submitted', 'admin_note': None, 'reviewed_at': None})
    return jsonify({'status': row['status'], 'admin_note': row['admin_note'], 'reviewed_at': row['reviewed_at']})


@app.route('/admin/profiles', methods=['GET'])
def admin_list_profiles():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not has_role(user, 'admin', 'super_admin'):
        return jsonify({'error': 'Forbidden'}), 403

    status_filter = request.args.get('status', 'pending')
    with engine.connect() as conn:
        rows = conn.execute(
            text('''
                SELECT ip.*, u.email
                FROM instructor_profiles ip
                JOIN users u ON u.id = ip.user_id
                WHERE ip.status = :status
                ORDER BY ip.created_at DESC
            '''),
            {'status': status_filter}
        ).mappings().all()
    return jsonify([dict(r) for r in rows])


@app.route('/admin/profiles/<int:profile_id>/review', methods=['PATCH'])
def admin_review_profile(profile_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not has_role(user, 'admin', 'super_admin'):
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json() or {}
    action = data.get('action', '').lower()
    if action not in ('approve', 'reject'):
        return jsonify({'error': 'action must be approve or reject'}), 400

    new_status = 'approved' if action == 'approve' else 'rejected'
    admin_note = str(data.get('admin_note', '')).strip()
    now = now_iso()

    with engine.begin() as conn:
        result = conn.execute(
            text('''
                UPDATE instructor_profiles
                SET status = :status, admin_note = :note, reviewed_by = :reviewer, reviewed_at = :reviewed_at
                WHERE id = :id
            '''),
            {'status': new_status, 'note': admin_note, 'reviewer': user['user_id'], 'reviewed_at': now, 'id': profile_id}
        )
        if result.rowcount == 0:
            return jsonify({'error': 'Profile not found'}), 404

    return jsonify({'message': f'Profile {new_status}', 'status': new_status, 'admin_note': admin_note})


# ===== 수업 세션 API =====

@app.route('/sessions', methods=['POST'])
def create_session():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not has_role(user, 'institution', 'admin', 'super_admin'):
        return jsonify({'error': 'Only institutions or admins can create sessions'}), 403

    data = request.get_json() or {}
    if not data.get('posting_id') or not data.get('instructor_id') or not data.get('scheduled_at'):
        return jsonify({'error': 'posting_id, instructor_id, scheduled_at are required'}), 400

    now = now_iso()
    with engine.begin() as conn:
        posting = conn.execute(
            text('SELECT id, rate, owner_id FROM postings WHERE id = :pid'),
            {'pid': data['posting_id']}
        ).mappings().first()
        if not posting:
            return jsonify({'error': 'Posting not found'}), 404
        if has_role(user, 'institution') and posting['owner_id'] != user['user_id']:
            return jsonify({'error': 'Posting not found or not owned'}), 404

        approved_application = conn.execute(
            text('''
                SELECT id
                FROM applications
                WHERE posting_id = :posting_id
                  AND student_id = :instructor_id
                  AND status = 'approved'
            '''),
            {'posting_id': data['posting_id'], 'instructor_id': data['instructor_id']}
        ).mappings().first()
        if not approved_application:
            return jsonify({'error': 'Approved application is required before creating a session'}), 409

        profile = conn.execute(
            text('''
                SELECT status, background_check_consent, child_abuse_consent
                FROM instructor_profiles
                WHERE user_id = :instructor_id
            '''),
            {'instructor_id': data['instructor_id']}
        ).mappings().first()
        if not profile or profile['status'] != 'approved':
            return jsonify({'error': 'Instructor profile must be approved before creating a session'}), 409
        if not profile['background_check_consent'] or not profile['child_abuse_consent']:
            return jsonify({'error': 'Instructor safety consents are incomplete'}), 409

        conn.execute(text('''
            INSERT INTO sessions
                (posting_id, instructor_id, org_id, scheduled_at, scheduled_duration_minutes,
                 status, gross_amount, withholding_amount, net_amount, created_at, updated_at)
            VALUES
                (:posting_id, :instructor_id, :org_id, :scheduled_at, :duration,
                 'scheduled', :gross, :wh, :net, :created_at, :updated_at)
        '''), {
            'posting_id': data['posting_id'],
            'instructor_id': data['instructor_id'],
            'org_id': user['user_id'],
            'scheduled_at': data['scheduled_at'],
            'duration': int(data.get('scheduled_duration_minutes', 60)),
            'gross': int(posting['rate'] or 0),
            'wh': int(round((posting['rate'] or 0) * 0.033)),
            'net': int(round((posting['rate'] or 0) * 0.967)),
            'created_at': now,
            'updated_at': now,
        })
        row_id = conn.execute(text('SELECT last_insert_rowid() AS id')).mappings().first()['id']

    with engine.connect() as conn:
        row = conn.execute(text('SELECT * FROM sessions WHERE id = :id'), {'id': row_id}).mappings().first()
    return jsonify(dict(row)), 201


@app.route('/sessions', methods=['GET'])
def list_sessions():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    role = normalize_role(user.get('role'))
    params = {}
    clauses = []

    if role == 'instructor':
        clauses.append('s.instructor_id = :uid')
        params['uid'] = user['user_id']
    elif role == 'institution':
        clauses.append('s.org_id = :uid')
        params['uid'] = user['user_id']
    # admin/district: no filter (all sessions)

    status_filter = request.args.get('status')
    if status_filter:
        clauses.append('s.status = :status')
        params['status'] = status_filter

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ''
    with engine.connect() as conn:
        rows = conn.execute(
            text(f'''
                SELECT
                    s.*,
                    COALESCE(p.title, '') AS title,
                    COALESCE(p.subject, '') AS subject,
                    COALESCE(u.email, ('#' || s.instructor_id)) AS instructor_name
                FROM sessions s
                LEFT JOIN postings p ON p.id = s.posting_id
                LEFT JOIN users u ON u.id = s.instructor_id
                {where}
                ORDER BY datetime(s.scheduled_at) DESC, s.id DESC
                LIMIT 100
            '''),
            params
        ).mappings().all()
    return jsonify([dict(r) for r in rows])


@app.route('/sessions/<int:session_id>', methods=['GET'])
def get_session(session_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    with engine.connect() as conn:
        row = conn.execute(
            text('SELECT * FROM sessions WHERE id = :id'),
            {'id': session_id}
        ).mappings().first()

    if not row:
        return jsonify({'error': 'Session not found'}), 404

    role = normalize_role(user.get('role'))
    if role == 'instructor' and row['instructor_id'] != user['user_id']:
        return jsonify({'error': 'Forbidden'}), 403
    if role == 'institution' and row['org_id'] != user['user_id']:
        return jsonify({'error': 'Forbidden'}), 403

    return jsonify(dict(row))


@app.route('/sessions/<int:session_id>/checkin', methods=['POST'])
def session_checkin(session_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not has_role(user, 'instructor'):
        return jsonify({'error': 'Instructor only'}), 403

    data = request.get_json() or {}
    lat = data.get('lat')
    lng = data.get('lng')
    if lat is None or lng is None:
        return jsonify({'error': 'lat and lng are required'}), 400

    try:
        lat = float(lat)
        lng = float(lng)
    except (ValueError, TypeError):
        return jsonify({'error': 'lat and lng must be numbers'}), 400

    now = now_iso()
    with engine.begin() as conn:
        row = conn.execute(
            text('SELECT id, status, instructor_id FROM sessions WHERE id = :id'),
            {'id': session_id}
        ).mappings().first()
        if not row:
            return jsonify({'error': 'Session not found'}), 404
        if row['instructor_id'] != user['user_id']:
            return jsonify({'error': 'Forbidden'}), 403
        if row['status'] not in ('scheduled',):
            return jsonify({'error': f"Cannot check in. Current status: {row['status']}"}), 409

        conn.execute(text('''
            UPDATE sessions
            SET checkin_at = :now, checkin_lat = :lat, checkin_lng = :lng,
                status = 'in_progress', updated_at = :now
            WHERE id = :id
        '''), {'now': now, 'lat': lat, 'lng': lng, 'id': session_id})

    return jsonify({'message': 'Checked in', 'status': 'in_progress', 'checkin_at': now})


@app.route('/sessions/<int:session_id>/complete', methods=['POST'])
def session_complete(session_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not has_role(user, 'instructor'):
        return jsonify({'error': 'Instructor only'}), 403

    data = request.get_json() or {}
    if not data.get('journal_content'):
        return jsonify({'error': 'journal_content is required'}), 400

    now = now_iso()
    with engine.begin() as conn:
        row = conn.execute(
            text('SELECT * FROM sessions WHERE id = :id'),
            {'id': session_id}
        ).mappings().first()
        if not row:
            return jsonify({'error': 'Session not found'}), 404
        if row['instructor_id'] != user['user_id']:
            return jsonify({'error': 'Forbidden'}), 403
        if row['status'] not in ('in_progress', 'scheduled'):
            return jsonify({'error': f"Cannot complete. Current status: {row['status']}"}), 409

        actual_minutes = int(data.get('actual_duration_minutes') or row['scheduled_duration_minutes'] or 60)
        scheduled = int(row['scheduled_duration_minutes'] or 60)
        gross_base = int(row['gross_amount'] or 0)
        # Adjust pay proportionally if time differs
        actual_gross = int(round(gross_base * (actual_minutes / scheduled))) if scheduled > 0 else gross_base
        wh = int(round(actual_gross * 0.033))
        net = actual_gross - wh

        conn.execute(text('''
            UPDATE sessions
            SET status = 'completed', completed_at = :now,
                actual_duration_minutes = :actual_min,
                journal_content = :journal,
                next_assignment = :next_assign,
                student_rating = :rating,
                gross_amount = :gross,
                withholding_amount = :wh,
                net_amount = :net,
                updated_at = :now
            WHERE id = :id
        '''), {
            'now': now,
            'actual_min': actual_minutes,
            'journal': str(data.get('journal_content', '')),
            'next_assign': str(data.get('next_assignment', '')),
            'rating': int(data.get('student_rating', 0)) if data.get('student_rating') else None,
            'gross': actual_gross,
            'wh': wh,
            'net': net,
            'id': session_id,
        })

    return jsonify({
        'message': 'Session completed',
        'status': 'completed',
        'actual_duration_minutes': actual_minutes,
        'gross_amount': actual_gross,
        'withholding_amount': wh,
        'net_amount': net,
        'completed_at': now,
    })


@app.route('/sessions/<int:session_id>', methods=['PATCH'])
def adjust_session(session_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not has_role(user, 'institution'):
        return jsonify({'error': 'Institution only'}), 403

    data = request.get_json() or {}
    if 'actual_duration_minutes' not in data:
        return jsonify({'error': 'actual_duration_minutes is required'}), 400

    try:
        actual_minutes = int(data.get('actual_duration_minutes'))
    except (TypeError, ValueError):
        return jsonify({'error': 'actual_duration_minutes must be integer'}), 400

    if actual_minutes <= 0:
        return jsonify({'error': 'actual_duration_minutes must be positive'}), 400

    requested_status = str(data.get('status', '')).strip().lower() if data.get('status') else ''
    if requested_status and requested_status not in ('scheduled', 'in_progress', 'completed'):
        return jsonify({'error': 'Invalid status'}), 400

    now = now_iso()
    with engine.begin() as conn:
        row = conn.execute(
            text('''
                SELECT s.*, p.rate AS posting_rate
                FROM sessions s
                LEFT JOIN postings p ON p.id = s.posting_id
                WHERE s.id = :id AND s.org_id = :org_id
            '''),
            {'id': session_id, 'org_id': user['user_id']}
        ).mappings().first()

        if not row:
            return jsonify({'error': 'Session not found'}), 404

        scheduled = int(row['scheduled_duration_minutes'] or 60)
        if scheduled <= 0:
            scheduled = 60

        base_gross = int(row['gross_amount'] or 0)
        if base_gross <= 0:
            rate = int(row['posting_rate'] or 0)
            base_gross = rate * scheduled

        hourly_rate = base_gross / scheduled if scheduled > 0 else 0
        adjusted_gross = int(round(hourly_rate * actual_minutes))
        adjusted_wh = int(round(adjusted_gross * 0.033))
        adjusted_net = adjusted_gross - adjusted_wh
        next_status = requested_status or row['status']

        conn.execute(
            text('''
                UPDATE sessions
                SET actual_duration_minutes = :actual_min,
                    gross_amount = :gross,
                    withholding_amount = :wh,
                    net_amount = :net,
                    status = :status,
                    updated_at = :updated_at
                WHERE id = :id AND org_id = :org_id
            '''),
            {
                'actual_min': actual_minutes,
                'gross': adjusted_gross,
                'wh': adjusted_wh,
                'net': adjusted_net,
                'status': next_status,
                'updated_at': now,
                'id': session_id,
                'org_id': user['user_id']
            }
        )

    return jsonify({
        'message': 'Session adjusted',
        'id': session_id,
        'status': next_status,
        'actual_duration_minutes': actual_minutes,
        'gross_amount': adjusted_gross,
        'withholding_amount': adjusted_wh,
        'net_amount': adjusted_net
    })


# ===== 리뷰/평점 API =====

@app.route('/reviews', methods=['POST'])
def create_review():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not has_role(user, 'institution'):
        return jsonify({'error': 'Only institutions can write reviews'}), 403

    data = request.get_json() or {}
    if not data.get('instructor_id') or not data.get('rating'):
        return jsonify({'error': 'instructor_id and rating are required'}), 400

    rating = int(data.get('rating', 0))
    if not (1 <= rating <= 5):
        return jsonify({'error': 'rating must be between 1 and 5'}), 400

    now = now_iso()
    with engine.begin() as conn:
        conn.execute(text('''
            INSERT INTO reviews (session_id, reviewer_id, instructor_id, rating, comment, reviewer_type, created_at)
            VALUES (:session_id, :reviewer_id, :instructor_id, :rating, :comment, 'institution', :created_at)
        '''), {
            'session_id': data.get('session_id'),
            'reviewer_id': user['user_id'],
            'instructor_id': int(data['instructor_id']),
            'rating': rating,
            'comment': str(data.get('comment', '')).strip(),
            'created_at': now,
        })
        row_id = conn.execute(text('SELECT last_insert_rowid() AS id')).mappings().first()['id']

    return jsonify({'message': 'Review created', 'id': row_id}), 201


@app.route('/reviews', methods=['GET'])
def list_reviews():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    instructor_id = request.args.get('instructor_id', type=int)
    session_id = request.args.get('session_id', type=int)

    clauses = []
    params = {}
    if instructor_id:
        clauses.append('instructor_id = :instructor_id')
        params['instructor_id'] = instructor_id
    if session_id:
        clauses.append('session_id = :session_id')
        params['session_id'] = session_id

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ''
    with engine.connect() as conn:
        rows = conn.execute(
            text(f'SELECT * FROM reviews{where} ORDER BY created_at DESC LIMIT 50'),
            params
        ).mappings().all()

    return jsonify([dict(r) for r in rows])


@app.route('/reviews/instructor/<int:instructor_id>/summary', methods=['GET'])
def instructor_review_summary(instructor_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    with engine.connect() as conn:
        row = conn.execute(
            text('''
                SELECT
                    COUNT(*) AS count,
                    ROUND(AVG(rating), 2) AS avg_rating,
                    SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END) AS five_star,
                    SUM(CASE WHEN rating = 4 THEN 1 ELSE 0 END) AS four_star,
                    SUM(CASE WHEN rating = 3 THEN 1 ELSE 0 END) AS three_star,
                    SUM(CASE WHEN rating = 2 THEN 1 ELSE 0 END) AS two_star,
                    SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) AS one_star
                FROM reviews WHERE instructor_id = :iid
            '''),
            {'iid': instructor_id}
        ).mappings().first()

    return jsonify(dict(row))


# ===== SOS 긴급 매칭 API =====

@app.route('/sos', methods=['POST'])
def create_sos():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not has_role(user, 'institution'):
        return jsonify({'error': 'Only institutions can create SOS alerts'}), 403

    data = request.get_json() or {}
    required = ['title', 'subject', 'region', 'scheduled_at', 'rate']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

    now = now_iso()
    with engine.begin() as conn:
        conn.execute(text('''
            INSERT INTO sos_alerts (org_id, title, subject, region, scheduled_at, duration_minutes, rate, status, created_at)
            VALUES (:org_id, :title, :subject, :region, :scheduled_at, :duration_minutes, :rate, 'open', :created_at)
        '''), {
            'org_id': user['user_id'],
            'title': str(data['title']).strip(),
            'subject': str(data['subject']).strip(),
            'region': str(data['region']).strip(),
            'scheduled_at': str(data['scheduled_at']).strip(),
            'duration_minutes': int(data.get('duration_minutes', 60)),
            'rate': int(data['rate']),
            'created_at': now,
        })
        row_id = conn.execute(text('SELECT last_insert_rowid() AS id')).mappings().first()['id']

    return jsonify({'message': 'SOS alert created', 'id': row_id}), 201


@app.route('/sos', methods=['GET'])
def list_sos():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    with engine.connect() as conn:
        if has_role(user, 'institution'):
            rows = conn.execute(text(
                'SELECT * FROM sos_alerts WHERE org_id = :uid ORDER BY created_at DESC LIMIT 50'
            ), {'uid': user['user_id']}).mappings().all()
        elif normalize_role(user.get('role', '')) == 'instructor':
            rows = conn.execute(text(
                "SELECT * FROM sos_alerts WHERE status = 'open' ORDER BY created_at DESC LIMIT 50"
            )).mappings().all()
        else:
            rows = conn.execute(text(
                'SELECT * FROM sos_alerts ORDER BY created_at DESC LIMIT 50'
            )).mappings().all()

    return jsonify([dict(r) for r in rows])


@app.route('/sos/available', methods=['GET'])
def list_sos_available():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT * FROM sos_alerts WHERE status = 'open' ORDER BY created_at DESC LIMIT 50"
        )).mappings().all()

    return jsonify([dict(r) for r in rows])


@app.route('/sos/<int:sos_id>/accept', methods=['POST'])
def accept_sos(sos_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if normalize_role(user.get('role', '')) != 'instructor':
        return jsonify({'error': 'Only instructors can accept SOS alerts'}), 403

    now = now_iso()
    with engine.begin() as conn:
        row = conn.execute(text('SELECT * FROM sos_alerts WHERE id = :id'), {'id': sos_id}).mappings().first()
        if not row:
            return jsonify({'error': 'SOS alert not found'}), 404
        if row['status'] != 'open':
            return jsonify({'error': 'SOS alert is no longer open'}), 409
        conn.execute(text('''
            UPDATE sos_alerts SET status = 'accepted', accepted_by = :uid, accepted_at = :now
            WHERE id = :id
        '''), {'uid': user['user_id'], 'now': now, 'id': sos_id})

    return jsonify({'message': 'SOS accepted', 'id': sos_id})


# ===== 전자계약 API =====

@app.route('/contracts', methods=['POST'])
def create_contract():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not has_role(user, 'institution'):
        return jsonify({'error': 'Only institutions can create contracts'}), 403

    data = request.get_json() or {}
    if not data.get('instructor_id') or not data.get('title'):
        return jsonify({'error': 'instructor_id and title are required'}), 400

    now = now_iso()
    with engine.begin() as conn:
        conn.execute(text('''
            INSERT INTO contracts (posting_id, application_id, institution_id, instructor_id, title, content, status, created_at, updated_at)
            VALUES (:posting_id, :application_id, :institution_id, :instructor_id, :title, :content, 'draft', :created_at, :updated_at)
        '''), {
            'posting_id': data.get('posting_id'),
            'application_id': data.get('application_id'),
            'institution_id': user['user_id'],
            'instructor_id': int(data['instructor_id']),
            'title': str(data['title']).strip(),
            'content': str(data.get('content', '')).strip(),
            'created_at': now,
            'updated_at': now,
        })
        row_id = conn.execute(text('SELECT last_insert_rowid() AS id')).mappings().first()['id']

    return jsonify({'message': 'Contract created', 'id': row_id}), 201


@app.route('/contracts', methods=['GET'])
def list_contracts():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    role = normalize_role(user.get('role', ''))

    with engine.connect() as conn:
        if has_role(user, 'institution'):
            rows = conn.execute(text(
                'SELECT * FROM contracts WHERE institution_id = :uid ORDER BY created_at DESC LIMIT 50'
            ), {'uid': user['user_id']}).mappings().all()
        elif role == 'instructor':
            rows = conn.execute(text(
                'SELECT * FROM contracts WHERE instructor_id = :uid ORDER BY created_at DESC LIMIT 50'
            ), {'uid': user['user_id']}).mappings().all()
        else:
            rows = conn.execute(text(
                'SELECT * FROM contracts ORDER BY created_at DESC LIMIT 50'
            )).mappings().all()

    return jsonify([dict(r) for r in rows])


@app.route('/contracts/<int:contract_id>/sign', methods=['PATCH'])
def sign_contract(contract_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    role = normalize_role(user.get('role', ''))

    now = now_iso()
    with engine.begin() as conn:
        row = conn.execute(text('SELECT * FROM contracts WHERE id = :id'), {'id': contract_id}).mappings().first()
        if not row:
            return jsonify({'error': 'Contract not found'}), 404
        if row['status'] == 'cancelled':
            return jsonify({'error': 'Contract is cancelled'}), 409

        if has_role(user, 'institution') and row['institution_id'] == user['user_id']:
            conn.execute(text(
                'UPDATE contracts SET institution_signed_at = :now, updated_at = :now WHERE id = :id'
            ), {'now': now, 'id': contract_id})
        elif role == 'instructor' and row['instructor_id'] == user['user_id']:
            conn.execute(text(
                'UPDATE contracts SET instructor_signed_at = :now, updated_at = :now WHERE id = :id'
            ), {'now': now, 'id': contract_id})
        else:
            return jsonify({'error': 'Not authorized to sign this contract'}), 403

        updated = conn.execute(text('SELECT * FROM contracts WHERE id = :id'), {'id': contract_id}).mappings().first()
        if updated['institution_signed_at'] and updated['instructor_signed_at']:
            conn.execute(text(
                "UPDATE contracts SET status = 'signed', updated_at = :now WHERE id = :id"
            ), {'now': now, 'id': contract_id})

    return jsonify({'message': 'Contract signed', 'id': contract_id})


@app.route('/contracts/<int:contract_id>', methods=['GET'])
def get_contract(contract_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    role = normalize_role(user.get('role', ''))

    with engine.connect() as conn:
        row = conn.execute(text('SELECT * FROM contracts WHERE id = :id'), {'id': contract_id}).mappings().first()
    if not row:
        return jsonify({'error': 'Contract not found'}), 404

    row_dict = dict(row)
    if not has_role(user, 'institution', 'admin', 'super_admin') and row_dict.get('instructor_id') != user['user_id']:
        return jsonify({'error': 'Forbidden'}), 403

    return jsonify(row_dict)


# ===== 에스크로 결제 API =====

@app.route('/escrow/charges', methods=['POST'])
def create_escrow_charge():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not has_role(user, 'institution'):
        return jsonify({'error': 'Only institutions can create escrow charges'}), 403

    data = request.get_json() or {}
    if not data.get('session_id') or not data.get('amount'):
        return jsonify({'error': 'session_id and amount are required'}), 400

    amount = int(data['amount'])
    if amount <= 0:
        return jsonify({'error': 'amount must be positive'}), 400

    now = now_iso()
    with engine.begin() as conn:
        conn.execute(text('''
            INSERT INTO escrow_charges (session_id, institution_id, instructor_id, amount, status, held_at, created_at)
            VALUES (:session_id, :institution_id, :instructor_id, :amount, 'held', :now, :now)
        '''), {
            'session_id': int(data['session_id']),
            'institution_id': user['user_id'],
            'instructor_id': data.get('instructor_id'),
            'amount': amount,
            'now': now,
        })
        row_id = conn.execute(text('SELECT last_insert_rowid() AS id')).mappings().first()['id']

    return jsonify({'message': 'Escrow charge created', 'id': row_id, 'status': 'held'}), 201


@app.route('/escrow/charges', methods=['GET'])
def list_escrow_charges():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    role = normalize_role(user.get('role', ''))

    with engine.connect() as conn:
        if has_role(user, 'institution'):
            rows = conn.execute(text(
                'SELECT * FROM escrow_charges WHERE institution_id = :uid ORDER BY created_at DESC LIMIT 50'
            ), {'uid': user['user_id']}).mappings().all()
        elif role == 'instructor':
            rows = conn.execute(text(
                'SELECT * FROM escrow_charges WHERE instructor_id = :uid ORDER BY created_at DESC LIMIT 50'
            ), {'uid': user['user_id']}).mappings().all()
        else:
            rows = conn.execute(text(
                'SELECT * FROM escrow_charges ORDER BY created_at DESC LIMIT 50'
            )).mappings().all()

    return jsonify([dict(r) for r in rows])


@app.route('/escrow/charges/<int:charge_id>/release', methods=['PATCH'])
def release_escrow_charge(charge_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not has_role(user, 'institution', 'admin', 'super_admin'):
        return jsonify({'error': 'Forbidden'}), 403

    now = now_iso()
    with engine.begin() as conn:
        row = conn.execute(text('SELECT * FROM escrow_charges WHERE id = :id'), {'id': charge_id}).mappings().first()
        if not row:
            return jsonify({'error': 'Charge not found'}), 404
        if row['status'] != 'held':
            return jsonify({'error': f'Cannot release charge with status: {row["status"]}'}), 409
        if has_role(user, 'institution') and row['institution_id'] != user['user_id']:
            return jsonify({'error': 'Forbidden'}), 403
        conn.execute(text(
            "UPDATE escrow_charges SET status = 'released', released_at = :now WHERE id = :id"
        ), {'now': now, 'id': charge_id})

    return jsonify({'message': 'Charge released', 'id': charge_id, 'status': 'released'})


@app.route('/escrow/charges/<int:charge_id>/refund', methods=['PATCH'])
def refund_escrow_charge(charge_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if not has_role(user, 'institution', 'admin', 'super_admin'):
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json() or {}
    reason = str(data.get('reason', '')).strip()

    now = now_iso()
    with engine.begin() as conn:
        row = conn.execute(text('SELECT * FROM escrow_charges WHERE id = :id'), {'id': charge_id}).mappings().first()
        if not row:
            return jsonify({'error': 'Charge not found'}), 404
        if row['status'] != 'held':
            return jsonify({'error': f'Cannot refund charge with status: {row["status"]}'}), 409
        if has_role(user, 'institution') and row['institution_id'] != user['user_id']:
            return jsonify({'error': 'Forbidden'}), 403
        conn.execute(text(
            "UPDATE escrow_charges SET status = 'refunded', refunded_at = :now, refund_reason = :reason WHERE id = :id"
        ), {'now': now, 'reason': reason, 'id': charge_id})

    return jsonify({'message': 'Charge refunded', 'id': charge_id, 'status': 'refunded'})


if __name__ == '__main__':
    import os

    port = int(os.getenv('PORT', '8000'))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)


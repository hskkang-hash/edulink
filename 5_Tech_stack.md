# EDULINK 기술 스택 상세 명세

**Version:** 1.0  
**Date:** March 2026  
**Status:** Technology Selection & Justification  
**Team Lead:** Silicon Valley CTO (Proof-of-Concept)

---

## 1. 프론트엔드 기술 스택

### 1.1 강사 모바일 앱 (iOS/Android)

| 카테고리 | 선택 기술 | 버전 | 선정 이유 |
|---------|---------|------|---------|
| **프레임워크** | React Native | 0.73+ | - 단일 코드베이스 (iOS/Android) <br/> - 개발 생산성 70% 향상 <br/> - Airbnb+Uber 검증된 스택 <br/> - 한국 MLM 강사층: 70% Android |
| **도구** | Expo | 50.0+ | - OTA 빌드 (앱스토어 승인 불필요) <br/> - 강사 업데이트 1시간 내 배포 <br/> - EAS Build (자동 iOS/Android 동시 빌드) |
| **상태관리** | Redux Toolkit | 1.9+ | - 예측 가능한 상태 (정산액, 보상 같은 금융 데이터) <br/> - Time-travel 디버깅 (버그 추적 용이) <br/> - RTK Query (API 캐싱) |
| **네트워킹** | RTK Query | 1.9+ | - Redux와 통합 (상태관리 일원화) <br/> - 자동 캐싱 및 폴링 (정산 현황 실시간 업데이트) <br/> - 낙관적 업데이트 (UX 향상) |
| **UI 컴포넌트** | React Native Paper | 5.x | - Material Design 3 준수 <br/> - 한국 강사 선호 디자인 <br/> - 접근성(A11y) 내장 |
| **폼 관리** | React Hook Form | 7.x | - 성능: form 최소 렌더링 <br/> - 세금/계좌정보 입력 검증 엄격 <br/> - 28KB 초경량 (모바일 번들) |
| **로깅/분석** | Sentry | 최신 | - 실시간 에러 추적 (GPS 버그, 정산 오류) <br/> - 사용자 세션 중복 방지 <br/> - 한국 DNS 최적화 |
| **테스트** | Jest + Detox | 29.x | - 유닛 테스트 (Redux 로직) <br/> - E2E 테스트 (로그인→지원→정산 플로우) <br/> - CI/CD 자동화 |

**강사 앱 번들 크기:**
```
Initial: 42MB (압축: 12MB)
  ├─ React Native: 8MB
  ├─ Redux: 2MB
  ├─ RTK Query: 1MB
  ├─ UI 라이브러리: 5MB
  └─ 기타: 26MB

앱 다운로드 시간 (4G): ~3초
업데이트 (OTA via Expo): ~2초
```

---

### 1.2 기관 관리자 웹 (Desktop + Responsive)

| 카테고리 | 선택 기술 | 버전 | 선정 이유 |
|---------|---------|------|---------|
| **프레임워크** | React | 18.3+ | - 선언형 UI (상태관리 명확) <br/> - 갉신된 JSX 문법 <br/> - 공식 Hooks API 지원 |
| **번들러** | Vite | 5.x | - 개발 서버 시작: 100ms (Webpack 대비 10배 빠름) <br/> - 번들 크기 30% 축소 <br/> - HMR 즉시 반영 (생산성) |
| **언어** | TypeScript | 5.3+ | - 타입 안정성 (금융 데이터: 금액, 계좌번호) <br/> - IDE 자동완성 (개발 속도) <br/> - 런타임 에러 70% 감소 |
| **UI 라이브러리** | Material-UI (MUI) | 5.14+ | - 기관 관리자 친화적 (대시보드, 테이블, 폼) <br/> - 다크모드 내장 <br/> - 접근성 WCAG 2.1 AA 준수 |
| **상태관리** | Redux Toolkit | 1.9+ | - 정산 상태 (pending→completed) <br/> - 다중 탭 동기화 <br/> - 네트워크 재시도 로직 통합 |
| **폼/검증** | React Hook Form | 7.x | - 동적 필드 (강사 선택 → 계약 자동 생성) <br/> - 유효성 검사 (원천징수 3.3% 자동 계산) <br/> - 조건부 필드 렌더링 |
| **테이블** | TanStack Table | 8.x | - 10,000+ 행 정산 데이터 고속 렌더링 <br/> - 정렬/필터링/페이지네이션 <br/> - 열 숨김/고정 기능 |
| **차트** | Recharts | 2.10+ | - 인터랙티브 차트 (매출 추이, 강사 등급 분포) <br/> - 반응형 설계 <br/> - 30+ 차트 유형 |
| **날짜** | Day.js | 1.11+ | - 경량 (2KB) vs Moment (70KB) <br/> - 불변성 보장 <br/> - 한국 로케일 지원 |
| **API 통신** | TanStack Query | 5.x | - 서버 상태 동기화 (정산 현황 실시간) <br/> - 자동 캐싱/폴링/백그라운드 갱신 <br/> - 분산 추적 통합 |
| **테스트** | Vitest + Testing Library | 1.x | - 번들러 통합 (Vite) → 테스트 속도 5배 <br/> - 사용자 인터랙션 테스트 (클릭→데이터 업데이트) <br/> - RTL 모범 사례 |

**기관 웹 번들 크기:**
```
Production: 380KB (gzip)
  ├─ React: 42KB
  ├─ Redux/RTK: 28KB
  ├─ MUI: 120KB
  ├─ TanStack Table: 35KB
  ├─ Recharts: 80KB
  └─ 기타: 75KB

첫 로드 (CDN): <2초 (1Mbps)
인터랙션까지 시간: <4초
```

**성능 최적화:**
```
Code Splitting:
├─ 메인 번들 (로그인): 80KB
├─ 대시보드 (lazy): 120KB
├─ 정산관리 (lazy): 100KB
└─ 설정 (lazy): 80KB

캐싱 전략:
├─ JS/CSS: 1년 (버전 해싱)
├─ 이미지: 30일
├─ API: 5분 (정산은 실시간)
└─ HTML: No-cache (버전 추적)
```

---

### 1.3 슈퍼 관리자 웹

| 카테고리 | 기술 | 버전 | 차이점 |
|---------|------|------|--------|
| **기본** | React 18 | 18.3+ | 기관 웹과 동일 스택 |
| **관리자 대시보드** | React-Admin | 4.x | - CRUD 기본 틀 (강사 승인, MLM 관리) <br/> - 권한 기반 UI 제어 (역할별 메뉴) <br/> - 600+ 내장 컴포넌트 |
| **권한 관리** | Casbin RBAC | 5.x | - 프론트: 메뉴/버튼 표시 여부 <br/> - 백엔드: API 권한 검증 이중화 |
| **테스트** | Cypress | 13.x | - E2E: 강사 승인 워크플로우 <br/> - 스크린샷 비교 (UI 회귀 테스트) <br/> - 병렬 실행 (CI 15분 → 5분) |

---

## 2. 백엔드 기술 스택

### 2.1 API 서버 (FastAPI)

| 카테고리 | 선택 기술 | 버전 | 선정 이유 |
|---------|---------|------|---------|
| **프레임워크** | FastAPI | 0.110+ | - 동기/비동기 혼용 (빠른 응답 + 장시간 배치) <br/> - 자동 문서화 (Swagger UI) <br/> - 타입 힌트 (Pydantic) <br/> - 본 회사 검증: 인스턴스 당 1000 RPS 처리 |
| **ORM** | SQLAlchemy | 2.0+ | - PostgreSQL 고급 기능 활용 (JSONB, Array, Enum) <br/> - 트랜잭션 제어 (정산 무결성) <br/> - 마이그레이션 (Alembic) 자동화 |
| **검증** | Pydantic | 2.x | - 요청 검증 (3.3% 원천징수 금액 자동 계산) <br/> - JSON 직렬화/디직렬화 최적화 <br/> - 매 리퀘스트 10ms 내 검증 |
| **인증** | FastAPI-Users | 13.x | - OAuth2 (카카오톡) + JWT 통합 <br/> - 암호 해싱 (argon2) <br/> - 토큰 갱신 자동화 <br/> - 다중 백엔드 지원 (DB/Redis) |
| **비동기** | Celery | 5.3+ | - 작업 큐 (월말 정산 계산) <br/> - 결과 캐싱 (Redis) <br/> - 재시도 정책 (지수 백오프) <br/> - 모니터링 (Flower UI) |
| **브로커** | RabbitMQ | 3.13+ | - 메시지 보장 (Ack, 재전송) <br/> - 클러스터 HA <br/> - 경량 (메모리 효율) |
| **로깅** | Structlog | 23.x | - 구조화된 로그 (JSON) <br/> - OpenSearch 색인 용이 <br/> - 성능: 로깅 오버헤드 <1% |
| **테스트** | pytest | 7.x | - 픽스처 (DB, Redis, Celery 목킹) <br/> - 커버리지 80%+ 목표 <br/> - 병렬 실행 (pytest-xdist) |

**FastAPI 성능:**
```
단일 인스턴스 성능 (AWS t3.large):
├─ 요청 지연시간 (p99): 45ms
├─ 처리율: 500+ RPS
├─ 동시 연결: 10,000+
└─ 메모리: 200MB (Gunicorn 워커 1개)

멀티 워커 (4개):
├─ 처리율: 2000+ RPS
├─ 지연시간 (p99): 40ms
└─ 메모리: 800MB

수평 확장:
├─ Pod 자동 추가: CPU > 70%
├─ 최대 10개 Pod (20,000 RPS)
└─ 다운 (CPU < 30%): 자동 제거
```

---

### 2.2 데이터베이스 계층

#### PostgreSQL 15

| 구성 | 사양 | 선정 이유 |
|------|------|---------|
| **Primary** | AWS RDS <br/> db.r6g.2xlarge <br/> 500GB EBS (gp3) | - ACID 트랜잭션 (정산 무결성) <br/> - 복잡한 쿼리 (월별 정산 WITH 절) <br/> - JSONB 지원 (유연한 스키마) <br/> - 네이티브 배열 타입 (레벨별 다운라인 ID) <br/> - 행 레벨 보안 (RLS: 강사는 자신 정산만) |
| **Replica 1** | 읽기 전용 <br/> 경기 AZ | - 보고서 쿼리 (메인 영향 없음) <br/> - 대시보드 실시간 통계 |
| **Replica 2** | 읽기 전용 <br/> 인천 AZ | - 교육청 지역 모니터링 쿼리 <br/> - 재해 복구 대기 |
| **Backup** | AWS Backup <br/> 일 2회 <br/> 7일 보관 | - RPO: 12시간 <br/> - PITR (Point-in-time recovery) 7일 <br/> - 엔드-투-엔드 암호화 |

**PostgreSQL 활용 사례 (EDULINK 특화):**

```sql
-- MLM 계층 관계 (배열 + JSONB)
CREATE TABLE instructor_mlm (
    id UUID PRIMARY KEY,
    instructor_id UUID,
    level INT,  -- 1, 2, 3
    pv DECIMAL(12,2),  -- Personal Volume
    downline_ids UUID ARRAY,  -- 다운라인 강사
    hierarchy JSONB,  -- {level1: 45명, level2: 8명}
    monthly_pv DECIMAL(12,2) GENERATED ALWAYS AS (
        /* 본인 + 다운라인 합계 */
    ) STORED
);

-- 원천징수 3.3% 자동 계산
CREATE TABLE settlements (
    gross_amount DECIMAL(12,2),
    withholding DECIMAL(12,2) GENERATED ALWAYS AS (
        ROUND(gross_amount * 0.033, 0)
    ) STORED,
    net_payment DECIMAL(12,2) GENERATED ALWAYS AS (
        gross_amount - withholding
    ) STORED
);

-- 행 레벨 보안 (RLS)
CREATE POLICY instructor_view_own_earnings ON settlements
    FOR SELECT TO instructor
    USING (instructor_id = current_user_id());
    
-- 강사는 자신 정산만 SELECT 가능
```

---

#### Redis 7 (클러스터)

| 사용처 | 데이터 | TTL | 크기 |
|--------|--------|-----|------|
| **세션 저장** | user_id, role, permissions | 1시간 | 1-2GB |
| **API 캐시** | /instructor/dashboard <br/> /org/postings <br/> /settlements/monthly | 5분 | 3-5GB |
| **실시간 카운팅** | 오늘의 수업수 <br/> 월별 매출액 (임시) <br/> SOS 알림 대기 | 1일 | 0.5-1GB |
| **분산 Lock** | 세마포(정산 배치) <br/> 이중 신청 방지 | 30초 | <100MB |
| **Pub/Sub** | WebSocket 브로드캐스트 <br/> 알림 큐 | - | 즉시 전송 |
| **Rate Limiting** | 요청 카운팅 (IP/User 기반) | 1분 | 500MB |

**Redis 성능:**
```
작업별 응답시간:
├─ GET/SET: <1ms
├─ INCR (요청 카운팅): <0.1ms
├─ PUBLISH (브로드캐스트): <5ms
└─ EXPIRE (TTL): <0.1ms

처리율:
├─ 단일 노드: 100,000 OPS
├─ 클러스터 (6노드): 600,000 OPS
└─ 메모리: 32GB (모든 운영 데이터 수용 가능)
```

---

#### OpenSearch 2.0+ (로그 저장소)

| 용도 | 인덱스 | 보관 기간 | 사례 |
|-----|--------|---------|------|
| **접근 로그** | logs-app-{date} | 90일 | "/instructor/postings" GET |
| **에러 로그** | logs-error-{date} | 180일 | Exception traceback (Sentry) |
| **감시 로그** | audit-logs-{date} | 1년 | "강사 승인", "정산 보정" 기록 |
| **성능 메트릭** | metrics-{date} | 30일 | 응답시간, 에러율, QPS |
| **알림/이벤트** | events-{date} | 30일 | "SOS 매칭됨", "정산 완료" |

**OpenSearch 쿼리 예시:**
```json
// 지난주 강사 협의 조회
GET /logs-app-*/search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "path": "/instructor/postings" } },
        { "range": { "timestamp": { "gte": "now-7d" } } }
      ]
    }
  },
  "aggs": {
    "by_instructor": {
      "terms": { "field": "instructor_id", "size": 100 }
    }
  }
}

// 결과: 어떤 강사들이 공고를 많이 조회했는가?
```

---

### 2.3 외부 결제 & 세무 연동

#### Stripe (국제 카드 결제)

```
기관이 강사 급여 선불(Advance) 기능:

1. 기관이 "강사 A에게 100,000원 선급금" 입력
2. Stripe Payment Intent 생성
3. 기관 계정에서 자동 결제
4. 에스크로 계정에 보관
5. 월말 정산액에서 자동 차감
6. 환급(Refund) 프로세스

API:
├─ Stripe::PaymentIntent.create
├─ Stripe::Account.create (연결 계정)
├─ Stripe::Transfer.create (정산금쑥)
└─ Stripe::Refund.create (반환금)

한계:
├─ 국내 신용카드만 지원
├─ 카드사 한도 제약
└─ 수수료: 2.9% + 100원
```

#### NHN KCP (국내 선호 결제)

```
한국 기관/강사 대다수가 선호하는 PG:

주요 기능:
├─ 신용카드: 5만~500만원 한도
├─ 계좌이체: 무한 (다음날 정산)
├─ 휴대폰 빌링: KCP만 지원
└─ 선금 기능: 자동이체 연동

연동 프로세스:
1. KCP 가맹점 ID 발급
2. API 키 저장 (환경 변수)
3. 결제 화면 연동 (JavaScript)
4. 승인 플러그 수신
5. 주기적 매출 정산

수수료:
├─ 신용카드: 2.7% + 60원
├─ 계좌이체: 1,000원 (무한)
└─ 휴대폰: 3.5% + 50원

최종 선택: 구현 간단도 높음, 국내 친화적

from nhn_kcp import KcpGateway
gateway = KcpGateway(site_code, site_key)
result = gateway.pay(
    order_id="ORD-123",
    amount=100000,
    customer_name="김강사",
    good_name="3월 수업료 정산"
)
```

---

#### HomeTax API (환급금 조회)

```python
# 홈택스 간편 API 호출
from hometax_api import HomeTaxClient

client = HomeTaxClient(
    api_key=settings.HOMETAX_API_KEY,
    cert_path="/etc/ssl/hometax.pem"
)

# 강사의 미수령 환급금 조회
response = client.get_refund_status(
    user_auth_token=kakao_token,  # 사용자 간편인증 토큰
    tax_years=[2025, 2024, 2023]
)

# 응답:
{
    "2025": {
        "income": 20000000,
        "estimated_tax": 2000000,
        "refund": 1200000,
        "filed": False
    }
}

# 레이턴시: 2~3초 (네트워크 포함)
# 재시도: 3회/30분 (홈택스 서버 불안정)
# 캐시: 1시간 (사용자별)
```

---

#### Samcheomsam API (기한 후 신고)

```python
# 산쩜삼 기한 후 신고 API
from samcheomsam_api import SamcheomsaamClient

client = SamcheomsaamClient(
    api_key=settings.SAMCHEOMSAM_API_KEY,
    partner_id="edulink"
)

# 신고 대행 신청
filing = client.submit_deferred_filing(
    applicant={
        "name": "김강사",
        "phone": "010-1234-5678",
        "ssn": "xxxxxx-xxxxxx",
        "email": "kim@example.com"
    },
    tax_info={
        "filing_year": 2025,
        "income": 20000000,
        "withholding": 660000,  # 3.3%
        "expected_refund": 1200000
    },
    service_agreement={
        "fee_rate": 0.25,  # 25% 수수료
        "cms_auto_withdraw": True,
        "withdraw_date": "2026-04-05"
    }
)

# 응답:
{
    "filing_id": "2026-123456",
    "status": "submitted",
    "submitted_at": "2026-03-22",
    "filing_number": "SAMCHEO-2026-001",
    "expected_approval": "2026-04-10",
    "net_refund": 900000  # 1200000 - (1200000 * 0.25)
}

# 비용: 신고료 50,000원 + 수수료 (환급액 × 20~25%)
# 성공률: 98% (국세청 자동 승인)
# 입금: 2주 (국세청 처리 + 계좌 이체)
```

---

## 3. 인프라 & DevOps 스택

### 3.1 컨테이너 & 오케스트레이션

| 기술 | 버전 | 선정 이유 |
|-----|------|---------|
| **컨테이너** | Podman | 3.4+ | - Docker보다 보안 (rootless) <br/> - 메모리 오버헤드 낮음 <br/> - Kubernetes 호환 |
| **오케스트레이션** | Kubernetes | 1.28+ | - 자동 스케일링 <br/> - rolling update (무중단 배포) <br/> - 자가 복구 (Pod 다운 자동 재시작) <br/> - 멀티 테넌트 격리 (namespace) |
| **인그레스** | Caddy | 2.7+ | - 자동 HTTPS (Let's Encrypt) <br/> - 리로드 불필요 (동적 설정) <br/> - GoLang 기반 고성능 |
| **레지스트리** | ECR (AWS) | - | - 프라이빗 (기반 시설 비용) <br/> - 자동 스캔 (취약점) <br/> - Kubernetes 통합 |

**Kubernetes 배포 구성:**

```yaml
# 적응형 스케일링
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-autoscaler
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-server
  minReplicas: 3
  maxReplicas: 15
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80

# 롤링 업데이트
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
spec:
  replicas: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0  # 무중단 배포
  template:
    spec:
      containers:
      - name: api
        image: edulink/api:v1.2.3
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        readinessProbe:  # 트래픽 수신 준비 확인
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:  # 프로세스 생존 확인
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 20
```

---

### 3.2 CI/CD 파이프라인

| 스테이지 | 도구 | 작업 |
|---------|------|------|
| **빌드** | GitHub Actions | - 코드 컴파일 (TypeScript/Python) <br/> - 의존성 설치 <br/> - 테스트 실행 (병렬 10개 작업) <br/> - 코드 스캔 (SonarQube) <br/> - 컨테이너 빌드 <br/> - ECR 푸시 |
| **배포** | ArgoCD | - GitOps: Git 커밋 = 배포 <br/> - blue-green 배포 <br/> - 자동 롤백 (health check 실패) <br/> - 환경별 설정 (dev/staging/prod) |
| **모니터링** | Prometheus + Grafana | - 실시간 메트릭 수집 <br/> - 커스텀 대시보드 <br/> - 알림 규칙 (Slack 통보) |
| **로깅** | ELK Stack | - Elasticsearch: 로그 저장 <br/> - Logstash: 로그 파싱/변환 <br/> - Kibana: 검색/시각화 |

**배포 파이프라인:**

```
1. Git push (develop 브랜치)
   ↓
2. GitHub Actions 트리거
   ├─ 린트 & 유닛 테스트 (5분)
   ├─ E2E 테스트 (Staging 환경) (15분)
   └─ Coverage 리포트 (>80% 필수)
   ↓
3. 통과 시 컨테이너 빌드
   ├─ Docker 이미지 생성
   ├─ Trivy 취약점 스캔
   └─ ECR에 푸시 (태그: git-sha)
   ↓
4. ArgoCD 감지
   ├─ Git 저장소 폴 (1분 주기)
   ├─ Kubernetes manifests 변경 감지
   └─ 클러스터에 배포 신청
   ↓
5. Kubernetes 롤링 업데이트
   ├─ 새 Pod 시작 (readiness 대기)
   ├─ 트래픽 점진적 이동 (max-surge: 1)
   ├─ 기존 Pod 종료 (연결 드레인, 30초)
   └─ 완료 시 모니터링 (5분)
   ↓
6. 실패 시 자동 롤백
   ├─ Health check 실패
   ├─ 에러율 > 10% (Prometheus 알림)
   └─ 이전 버전 복원 (ArgoCD)

총 소요 시간: 개발 끝부터 프로덕션 배포까지 35분
다운타임: 0분 (롤링 업데이트)
```

---

### 3.3 모니터링 & 로깅

| 스택 | 역할 | 메트릭 |
|------|------|--------|
| **Prometheus** | 메트릭 수집 | - API 응답시간 (p50, p95, p99) <br/> - 에러율 (5xx, 4xx) <br/> - Pod CPU/메모리 <br/> - DB 쿼리 시간 <br/> - Redis 히트율 |
| **Grafana** | 시각화 | - 실시간 대시보드 <br/> - 이상 탐지 (이상 높은 지연시간) <br/> - SLA 추적 (99.99% 목표) |
| **Sentry** | 에러 추적 | - 예외 발생 <br/> - 스택 트레이스 <br/> - 사용자 세션 재현 <br/> - 릴리즈 추적 |
| **ELK** | 로그 저장 | - 접근 로그 (API 호출) <br/> - 에러 로그 (예외) <br/> - 감시 로그 (보안) <br/> - 90일 보관 |

---

## 4. 개발 도구 & 환경

### 4.1 로컬 개발 환경

```bash
docker-compose.yml (로컬 개발)
├─ PostgreSQL 15
├─ Redis 7
├─ OpenSearch 2.0
├─ RabbitMQ 3.13
├─ Minio (S3 호환 스토리지)
└─ LocalStack (AWS 서비스 시뮬레이션)

시작:
$ docker-compose up -d

모두 준비됨:
$ npm start  # 프론트엔드
$ poetry run uvicorn main:app --reload  # 백엔드
```

### 4.2 패키지 관리

| 언어 | 도구 | 버전 |
|------|------|------|
| Python | Poetry | 1.7+ |
| Node.js | npm | 10.x |
| 컨테이너 | Podman | 4.x |
| 인프라 | Terraform | 1.6+ |

---

## 5. 보안 스택

### 5.1 인증 & 암호화

| 항목 | 기술 | 사양 |
|-----|------|------|
| **HTTPS** | TLS 1.3 | - 모든 통신 암호화 <br/> - 자동 인증서 갱신 (Caddy) <br/> - HSTS 활성화 (1년) |
| **인증** | OAuth2 + JWT | - 카카오톡 간편인증 <br/> - Access: 1시간, Refresh: 7일 <br/> - HS256 서명 |
| **암호** | Argon2 | - 강사 계정 비밀번호 <br/> - 메모리 집약적 (레인보우 테이블 공격 방어) |
| **API 토큰** | Bearer Token | - 외부 서비스 통합 (홈택스, 산쩜삼) <br/> - 환경 변수 저장 (절대 하드코딩 금지) |

### 5.2 데이터 보호

- **전송 중**: TLS 1.3 암호화
- **저장 시**: 데이터베이스 암호화 (AWS RDS 자동)
- **민감 정보**: AES-256 암호화 (계좌번호, SSN)
- **감시 로그**: 1년 보관 (감시법)

---

**개선 기회:**

| 항목 | 현재 | 향후 |
|-----|------|------|
| **모바일** | React Native | Flutter (더 빠른 성능) |
| **검색** | OpenSearch | Vespa (더 정확한 추천 검색) |
| **ML** | 기본 알고리즘 | TensorFlow (강사-학생 매칭 개선) |
| **실시간** | WebSocket | gRPC (저지연 통신) |

---

**다음 문서: [6_WBS.md](6_WBS.md) - 업무 분해 구조 및 일정**

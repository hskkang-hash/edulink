# EDULINK 시스템 아키텍처

**Version:** 1.0  
**Date:** March 2026  
**Status:** MVP Architecture Design

---

## 1. 전체 아키텍처 개요

### 1.1 4-Tier 멀티 플랫폼 구조

```
┌──────────────────────────────────────────────────────────────────┐
│                        사용자 계층                                 │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │  강사 모바일앱   │  │  기관 관리자 웹   │  │ 관리자/교육청 웹 │ │
│  │ (Mobile-First)  │  │ (Desktop-First)  │  │ (Desktop-Only)  │ │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘ │
└────────────────────────────────────────────────────────────────▲─
                                                                  │
                    HTTPS / WebSocket / REST API
                                                                  │
┌──────────────────────────────────────────────────────────────────┐
│                    API 게이트웨이 + 로드밸런싱                     │
│                  (Caddy / Nginx Reverse Proxy)                  │
│  • JWT 토큰 검증                                                │
│  • CORS 헤더 관리                                               │
│  • Rate Limiting                                               │
│  • SSL/TLS 종료                                                │
└────────────────────────────────────────────────────────────────▲─
                                                                  │
┌──────────────────────────────────────────────────────────────────┐
│                  백엔드 서비스 계층 (FastAPI)                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────┐ │
│  │   인증 & 권한   │  │  매칭 서비스   │  │  정산 서비스   │  │세무 & 환급│ │
│  │   (FastAPI   │  │  (Matching)  │  │ (Settlement) │  │서비스   │ │
│  │    Users)    │  │              │  │              │  │(Tax)   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────┘ │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────┐ │
│  │  보상 관리   │  │ 보고서 생성   │  │ 설정 관리    │  │분석 & ML │ │
│  │   (MLM)     │  │(Report Studio)│  │(Settings)   │  │(Analytics)
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────┘ │
│                                                                  │
└────────────────────────────────────────────────────────────────▲─
             │                          │                         │
             │                          │                         │
             ▼                          ▼                         ▼
    ┌──────────────┐          ┌──────────────┐        ┌────────────────┐
    │ PostgreSQL   │          │ Redis Cache  │        │  OpenSearch    │
    │   (주 DB)    │          │ (세션/캐시)  │        │(로그/분석 DB)   │
    └──────────────┘          └──────────────┘        └────────────────┘
```

### 1.2 컴포넌트별 책임 분담

| 계층 | 컴포넌트 | 책임 | 기술 |
|------|---------|------|------|
| **프론트엔드** | 강사 앱 | 모바일 최적화, 실시간 알림 | React Native |
| | 기관 웹 | 강사 관리, 정산, 계약 | React 18 |
| | 관리자 웹 | MLM 관리, 컴플라이언스 | React 18 |
| **API 게이트웨이** | Reverse Proxy | 인증, 라우팅, 보안 | Caddy |
| **백엔드** | 인증 서비스 | 로그인, JWT, OAuth2 | FastAPI Users |
| | 매칭 서비스 | SOS 알림, 양방향 예약 | FastAPI |
| | 정산 서비스 | 자동 정산, 3.3% 원천징수 | FastAPI |
| | 세무 서비스 | 환급금 조회, 신고 | FastAPI |
| | 보상 관리 | 다단계 보상, 35% 규제 | FastAPI |
| **데이터베이스** | PostgreSQL | 설정, 사용자, 거래 기록 | PostgreSQL 15 |
| | Redis | 세션, 캐시, 큐 | Redis 7 |
| | OpenSearch | 로그, 메트릭, 분석 | OpenSearch 2.0+ |
| **외부 연동** | 홈택스/삼쩜삼 | 세망 신고, 환급 조회 | REST API |
| | PG 게이트웨이 | 에스크로 결제 | Stripe/NHN KCP |

---

## 2. 서비스 계층 아키텍처

### 2.1 마이크로서비스 설계

```
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Main Application                  │
├─────────────────────────────────────────────────────────────┤
│                     Core Services                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │  Auth Service       │  │  User Service       │          │
│  │  ─────────────────  │  │  ─────────────────  │          │
│  │ • FastAPI Users     │  │ • CRUD              │          │
│  │ • JWT Management    │  │ • Profile Mgmt      │          │
│  │ • OAuth2            │  │ • Preference        │          │
│  └─────────────────────┘  └─────────────────────┘          │
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │  Matching Service   │  │  Settlement Service │          │
│  │  ─────────────────  │  │  ─────────────────  │          │
│  │ • Posting CRUD      │  │ • Auto Settlement   │          │
│  │ • SOS Matching      │  │ • Withholding Tax   │          │
│  │ • On-Demand Booking │  │ • Payment History   │          │
│  │ • Application Mgmt  │  │ • Refund Logic      │          │
│  └─────────────────────┘  └─────────────────────┘          │
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │  Tax Service        │  │  MLM Service        │          │
│  │  ─────────────────  │  │  ─────────────────  │          │
│  │ • HomeTax API       │  │ • Compensation Calc │          │
│  │ • Samcheomsam API   │  │ • Leadership Bonus  │          │
│  │ • Refund Query      │  │ • 35% Compliance    │          │
│  │ • Deferred Filing   │  │ • Rule Engine       │          │
│  │ • CMS Auto Charge   │  │ • Version Control   │          │
│  └─────────────────────┘  └─────────────────────┘          │
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │  Report Service     │  │  Admin Service      │          │
│  │  ─────────────────  │  │  ─────────────────  │          │
│  │ • Report Studio     │  │ • RBAC              │          │
│  │ • Template Mgmt     │  │ • Menu Config       │          │
│  │ • PDF/DOCX/PPTX Gen │  │ • Theme Mgmt        │          │
│  │ • PDF Generation    │  │ • System Config     │          │
│  │ • NLG Summary       │  │ • Audit Logging     │          │
│  └─────────────────────┘  └─────────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 서비스 간 통신

| 서비스 A | 서비스 B | 통신 방식 | 데이터 |
|---------|---------|---------|--------|
| Matching | Settlement | Direct Call | 수업료, 강사ID |
| Settlement | Tax | Background Task | 정산액, 세무ID |
| Tax | 외부 API | REST Call | 신고 데이터 |
| MLM | Settlement | Direct Call | 보상 계산용 PV |
| Report | All Services | Query | 분석 데이터 |

---

## 3. 데이터 계층 아키텍처

### 3.1 PostgreSQL 스키마 (관계형 데이터)

```
사용자 및 권한
├── users (기본정보)
├── user_roles (역할 할당)
├── user_permissions (세분화 권한)
├── user_preferences (사용자 설정)
└── api_tokens (API 토큰)

강사 & 기관 정보
├── instructors (강사 프로필)
├── instructor_qualifications (자격증)
├── instructor_background_check (배경조회)
├── organizations (기관/학교)
├── organization_contacts (담당자)
└── organization_contracts (계약)

매칭 & 수업
├── postings (공고)
├── applications (지원)
├── sessions (수업 정보)
├── attendance (출석 기록)
└── session_logs (수업 일지)

정산 & 결제
├── transactions (거래 기록)
├── settlements (정산 내역)
├── payment_receipts (영수증)
├── refunds (환불 기록)
└── escrow_accounts (에스크로)

세무 & 환급
├── tax_profiles (세무 프로필)
├── tax_records (소득 기록)
├── tax_refunds (환급 기록)
├── tax_submissions (신고 현황)
└── withholding_logs (원천징수 기록)

MLM & 보상
├── compensation_records (보상 기록)
├── mlm_rules (보상 규칙)
├── mlm_levels (강사 레벨)
├── leadership_bonuses (리더십 보너스)
└── compliance_audit_logs (감사 로그)

관리 & 설정
├── menu_configurations (메뉴 설정)
├── theme_settings (테마 설정)
├── system_configurations (시스템 설정)
├── report_templates (보고서 템플릿)
└── audit_logs (감시 로그)
```

### 3.2 Redis (캐시 & 세션 저장소)

```
세션 데이터
├── session:{sessionId} → 사용자 정보
├── user:{userId}:preferences → 사용자 설정
└── user:{userId}:permissions → 권한 캐시

API 캐시
├── instructor:{instructorId}:profile → 강사 프로필
├── organization:{orgId}:stats → 기관 통계
├── compensation:rules:{version} → 보상 규칙
└── report:template:{templateId} → 보고서 템플릿

실시간 데이터
├── live:sessions → 진행 중인 수업
├── live:sos:alerts → SOS 알림 큐
├── live:notifications:{userId} → 개인 알림
└── rate_limit:{userId}:{endpoint} → Rate Limiting

ML/AI 캐시
├── ml:models:{modelId} → 모델 메타데이터
├── ml:predictions:cache → 예측 결과 캐시
└── ml:feature:importance → 피처 중요도
```

### 3.3 OpenSearch (로그 & 분석 데이터)

```
로그 인덱스
├── logs-matching-* → 매칭 관련 로그
├── logs-settlement-* → 정산 관련 로그
├── logs-tax-* → 세무 관련 로그
├── logs-mlm-* → 보상 관련 로그
└── logs-system-* → 시스템 로그

분석 인덱스
├── analytics-sessions-* → 수업 통계
├── analytics-transactions-* → 거래 분석
├── analytics-performance-* → 성능 지표
└── analytics-user-behavior-* → 사용자 행동

알림 # 이벤트
├── alerts-anomaly → 이상 탐지 알림
├── alerts-threshold → 임계치 초과 알림
└── events-audit → 감사 이벤트
```

---

## 4. 아키텍처 패턴

### 4.1 요청-응답 흐름

```
1. 클라이언트 요청
   Client → Caddy (HTTPS) → FastAPI

2. 인증 검증
   FastAPI → JWT 검증 → FastAPI Users 확인

3. 권한 확인
   FastAPI → RBAC 체크 → 권한 데이터베이스

4. 비즈니스 로직
   Service Layer → PostgreSQL + Redis

5. 응답 생성
   FastAPI → JSON Response → Client

6. 캐시 업데이트
   Service → Redis 캐시 갱신
```

### 4.2 비동기 작업 흐름 (Celery)

```
1. 트리거 이벤트
   예: 수업 완료 → 자동 정산 작업 생성

2. 작업 큐 저장
   Celery → Redis Queue

3. Worker 처리
   Celery Worker → 백그라운드 실행

4. 데이터 저장
   Worker → PostgreSQL + OpenSearch

5. 알림 발송
   Worker → 사용자 서비스 (이메일, SMS, 푸시)

6. 결과 캐시
   Worker → Redis 결과 저장
```

### 4.3 실시간 통신 (WebSocket)

```
1. 연결 수립
   Client → WebSocket Connection (Caddy Pass-through)

2. 이벤트 구독
   Client → {"subscribe": "sos_alerts"}

3. 서버 푸시
   FastAPI → WebSocket Event (SOS, 정산 완료 등)

4. 클라이언트 수신
   Client → 리얼타임 UI 업데이트

5. 연결 종료
   Client → Disconnect
```

---

## 5. 배포 아키텍처

### 5.1 개발 환경

```
Developer Machine
├── Frontend (localhost:3000)
│   ├── Vite Dev Server
│   ├── Hot Module Reload
│   └── TypeScript Compilation
├── Backend (localhost:8000)
│   ├── Uvicorn Dev Server
│   ├── Auto-reload
│   └── Debug Mode
└── Services
    ├── PostgreSQL (localhost:5432)
    ├── Redis (localhost:6379)
    └── OpenSearch (localhost:9200)
```

### 5.2 프로덕션 환경

```
Production Cluster
├── Load Balancer (Caddy)
│   ├── Port 80 → 443 Redirect
│   ├── SSL/TLS Termination
│   └── Static File Serving
├── Backend Replicas (3x Gunicorn + Uvicorn)
│   ├── Auto-scaling
│   ├── Health Checks
│   └── Rolling Deployment
├── Databases
│   ├── PostgreSQL (Primary + Replicas)
│   ├── Redis (Cluster Mode)
│   └── OpenSearch (Multi-node)
└── External Services
    ├── PG Gateway (Stripe/NHN KCP)
    ├── HomeTax API
    ├── Samcheomsam API
    └── Email/SMS Service
```

### 5.3 컨테이너 배포

```
Container Orchestration (Podman)
├── Frontend Container
│   ├── Node.js + React Build
│   ├── Port 3000
│   └── Volume: /app/build
├── Backend Container
│   ├── Python + FastAPI
│   ├── Port 8000
│   └── Volume: /app/logs
├── PostgreSQL Container
│   ├── Persistent Volume
│   └── Backup Strategy
├── Redis Container
│   ├── Memory Optimized
│   └── Persistence: AOF
└── OpenSearch Container
    ├── Memory Optimized
    └── Persistent Volume
```

---

## 6. 보안 아키텍처

### 6.1 인증 계층

```
┌──────────────────────────────┐
│   클라이언트 (로그인)         │
└──────────────┬───────────────┘
              │
              ▼
    ┌─────────────────────┐
    │ FastAPI Users       │
    │ • Email/Password    │
    │ • OAuth2 (카카오톡)  │
    │ • JWT 토큰          │
    └─────────────────────┘
              │
              ▼
    ┌─────────────────────┐
    │ Redis Session Store │
    │ (Refresh Token)     │
    └─────────────────────┘
              │
              ▼
    ┌─────────────────────┐
    │ Protected Route     │
    │ → RBAC 권한 검증    │
    └─────────────────────┘
```

### 6.2 데이터 암호화

| 데이터 | 암호화 방식 | 키 관리 |
|--------|-----------|--------|
| 전송 중 | HTTPS TLS 1.3 | Let's Encrypt |
| 저장소 | AES-256 (민감 정보) | .env 환경변수 |
| 패스워드 | bcrypt + salt | Passlib |
| API Key | 해시 저장 | 환경변수 |

### 6.3 API 보안

```
각 요청:
├── 1. HTTPS 전송
├── 2. JWT 토큰 검증
├── 3. RBAC 권한 확인
├── 4. Rate Limiting
├── 5. CORS 검증
├── 6. SQL Injection 방지 (ORM)
├── 7. 감시 로깅
└── 8. 응답 반환
```

---

## 7. 확장성 & 성능

### 7.1 캐싱 전략

```
1단계: 브라우저 캐시
   ├── 정적 자산 (JS, CSS, 이미지): 1주일
   └── API 응답: 5분

2단계: Redis 캐시
   ├── 강사 프로필: 24시간
   ├── 기관 통계: 1시간
   ├── 보상 규칙: 7일
   └── 세션: 30일

3단계: 데이터베이스 인덱싱
   ├── 자주 조회되는 필드 인덱싱
   ├── 복합 인덱스 (user_id + created_at)
   └── Full-text 인덱싱 (검색)
```

### 7.2 데이터베이스 최적화

```
PostgreSQL
├── Read Replicas (3개)
│   ├── 읽기 쿼리 분산
│   └── 고가용성
├── Connection Pooling
│   └── pgBouncer
├── Sharding (향후)
│   └── 사용자 ID 기준
└── 인덱싱 전략
    └── B-tree, Hash, GiST

OpenSearch
├── Index Rotation (일일)
├── Shard 최적화
├── 압축 활성화
└── Warm/Cold Tier 유지
```

### 7.3 수평 확장

```
Stateless 설계
├── 서버 간 세션 공유: Redis
├── 파일 공유: S3/Minio
└── 메시지 큐: Redis Pub/Sub

로드 밸런싱
├── Caddy (Round-robin)
├── 헬스 체크
└── Sticky Session (선택)

자동 스케일링
├── CPU > 80% → 인스턴스 추가
├── 메모리 > 85% → 인스턴스 추가
└── 최대 10개 인스턴스 제한
```

---

## 8. 모니터링 & 로깅

### 8.1 로그 수집

```
Application Logs
└── Structured Logging (JSON)
    ├── Timestamp
    ├── Log Level
    ├── Service Name
    ├── User ID
    ├── Request ID
    ├── Message
    └── Stack Trace (에러 시)
        │
        ▼
    OpenSearch
    ├── 실시간 분석
    ├── 알림 생성
    └── 감사 추적
```

### 8.2 성능 모니터링

```
메트릭 수집 (Prometheus)
├── 응답 시간 (p50, p95, p99)
├── 처리량 (RPS)
├── 에러율
├── 데이터베이스 쿼리 시간
└── 캐시 히트율

시각화 (Grafana)
├── 대시보드
├── 알림
└── SLA 추적
```

### 8.3 에러 추적

```
Sentry Integration
├── 실시간 에러 알림
├── 스택 트레이스
├── 발생 빈도
├── 영향받는 사용자 수
└── 자동 그룹화
```

---

**다음 문서: [2_Functions.md](2_Functions.md)**

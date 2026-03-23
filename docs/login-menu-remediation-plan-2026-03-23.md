# Login/Menu 개선 플랜 (2026-03-23)

## 1) 목표
- 로그인/권한/메뉴 노출 규칙을 역할 모델과 1:1로 일치시킨다.
- UI에서 역할을 임의 변환하지 않고, 서버 권한 정책을 그대로 반영한다.
- 메뉴 접근/화면 접근의 일관성과 예측 가능성을 확보한다.

## 2) 현재 문제점 요약

### P0 (즉시 수정)
1. 프런트 역할 정규화가 실제 권한 모델을 왜곡함
- 위치: frontend/index.html
- 증상:
  - student를 institution으로 변환
  - super_admin을 district로 변환
- 영향:
  - 메뉴/라벨/조건 분기에서 잘못된 역할로 동작
  - institution 전용 UI 분기로 student가 진입 가능

2. super_admin 메뉴 접근 매트릭스 누락
- 위치: frontend/index.html
- 증상:
  - ROLE_NAV_LABELS에 super_admin 키 없음
- 영향:
  - super_admin 네비게이션 라벨이 fallback 경로로 흔들림

3. 로그인 폼 기본 계정/비밀번호가 하드코딩됨
- 위치: frontend/index.html
- 영향:
  - 데모/운영 환경 혼동
  - 보안/UX 측면에서 잘못된 기본 행동 유도

### P1 (단기 수정)
4. 역할 매핑 규칙이 메뉴/카드/관리자 사용자 표시에 재사용되어 의미가 뒤섞임
- 위치: frontend/index.html
- 영향:
  - 관리자 사용자 목록에서 실제 역할이 축약/변환되어 표시
  - 운영 중 역할 추적과 감사 가독성 저하

5. 로그인 토큰 저장 방식이 localStorage 단일 방식
- 위치: frontend/index.html
- 영향:
  - XSS 시 토큰 탈취 위험이 상대적으로 큼

### P2 (중기 개선)
6. 토큰 만료 정책이 프런트 UX와 명시적으로 동기화되지 않음
- 위치: backend/app_jwt.py, frontend/index.html
- 영향:
  - 만료 시점/재로그인 시점 사용자 경험 불명확

## 3) 개선 원칙
- 역할 값은 서버 원본을 그대로 사용한다. (no implicit remap)
- 메뉴 노출과 API 호출 가드는 같은 역할 매트릭스에서 파생한다.
- 데모용 역할(화면 설계 프리뷰)과 실제 인증 역할을 분리한다.

## 4) 실행 계획

### Phase A. 역할 모델 정합화 (P0)
1. normalizeRole에서 cross-role 변환 제거
- student -> institution, super_admin -> district 매핑 삭제
- 알 수 없는 값만 안전 기본값 처리

2. ROLE_NAV_LABELS에 super_admin 명시 추가
- admin과 동일 또는 별도 라벨 정책 확정

3. isRole/getAllowedScreens/getDefaultScreen 호출 경로 점검
- 권한 판정은 실제 role 기준으로만 동작하도록 통일

완료 기준
- student 로그인 시 institution 전용 메뉴/액션이 노출되지 않음
- super_admin 로그인 시 admin 급 화면 접근과 라벨이 일관됨

### Phase B. 로그인/메뉴 UX 정리 (P0~P1)
1. 로그인 입력 기본값 제거
- 이메일/비밀번호 value 하드코딩 삭제

2. 메뉴 접근 실패 UX 표준화
- 허용되지 않은 화면 이동 시 기본 화면으로 이동 + 상태 메시지 표시

3. 관리자 사용자 목록의 역할 표시를 원본 role 기준으로 표시
- 표시용 별칭은 배지로 추가 가능, 원본 값은 유지

완료 기준
- 첫 진입에서 민감 정보/기본 계정이 자동 주입되지 않음
- 역할 변경/권한 확인 시 표시 역할과 서버 역할이 불일치하지 않음

### Phase C. 인증 보안 강화 (P1~P2)
1. 토큰 저장 전략 검토
- 단기: localStorage 유지 시 CSP/입력 살균 점검
- 중기: HttpOnly Secure SameSite 쿠키 방식 전환 설계

2. 만료/세션 UX 정비
- 401 수신 시 공통 처리(세션 만료 메시지, 재로그인 유도)
- 만료 시간 정책(백엔드 24h) 문서화

완료 기준
- 세션 만료 흐름이 모든 보호 API에서 동일하게 처리됨

## 5) 테스트 계획

### 백엔드
- auth/login, auth/me, 역할별 보호 API(401/403/200) 회귀 유지
- super_admin 권한 경계 테스트 강화

### 프런트
- 역할별 메뉴 스냅샷 테스트
  - instructor, student, institution, district, admin, super_admin
- 역할별 화면 전환 테스트
  - 허용 screen만 노출/이동 가능
- 로그인 폼 기본값 부재 테스트

### E2E
- 역할별 로그인 후 노출 메뉴와 실제 API 권한 결과 일치 확인

## 6) 권장 작업 순서 (1주)
- Day 1: Phase A 코드 수정 + 단위 검증
- Day 2: Phase B 코드 수정 + 수동 회귀
- Day 3: 테스트 추가(역할/메뉴 스냅샷)
- Day 4: 세션 만료 UX 통합
- Day 5: 운영 점검 및 문서 업데이트

## 7) 롤백 전략
- 역할 정합화 커밋을 기능 플래그 또는 단일 커밋으로 분리
- 문제 발생 시 메뉴 노출 로직만 빠르게 이전 안정 버전으로 롤백

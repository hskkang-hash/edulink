# EduLink 10시간 개발 스프린트 - 자동화 실행 추적

**시작 시간:** 2026-03-22 (이 문서 작성 시)  
**목표:** 10시간 동안 하이브리드 자동화 (로컬 개발 + GitHub Actions 배포)

---

## 🎯 실행 모드

### 로컬 개발 (당신의 역할)
```powershell
# 기본: 모든 단계 실행 (테스트→커밋→푸시)
.\dev-sprint.ps1

# 특정 단계만 실행
.\dev-sprint.ps1 -phase test      # 테스트만
.\dev-sprint.ps1 -phase code      # 코드 검사만
.\dev-sprint.ps1 -phase commit    # 커밋만
.\dev-sprint.ps1 -phase push      # 푸시만

# 에러 무시하고 계속 진행 (위험)
.\dev-sprint.ps1 -noStop
```

### GitHub Actions (자동 배포)
- **트리거:** main 브랜치에 푸시 시 자동 시작
- **워크플로우:** `.github/workflows/auto-deploy-on-main-push.yml`
- **단계:**
  1. 테스트 검증 (Python 3.11)
  2. Docker 이미지 빌드
  3. GHCR에 자동 푸시
  4. 결과 리포트

---

## 📋 체크리스트 (10시간 분할)

### 시간 1-2: 기반 정리 (✅ 진행 중)
- [x] dev-sprint.ps1 스크립트 작성
- [x] GitHub Actions 워크플로우 추가
- [x] 진행 상태 추적 문서 작성
- [ ] 초기 테스트 실행 및 검증

**완료 기준:** 로컬 스크립트 1회 성공 실행

---

### 시간 2-4: 코어 기능 개발
- [ ] 실행 엔트리포인트 단일화 (app.py vs app_jwt.py)
- [ ] API 계약 문서 최신화
- [ ] 프론트-백엔드 통신 경로 검증

**완료 기준:** API 스펙 문서 갱신 + 테스트 20개 통과

---

### 시간 4-6: 통합 테스트 확장
- [ ] 사용자 플로우 테스트 작성 (회원가입→로그인→공고→지원→승인)
- [ ] 권한 실패 테스트 케이스 추가
- [ ] 세무/네트워크 API 통합 테스트

**완료 기준:** 백엔드 테스트 35개+ 통과

---

### 시간 6-8: 배포 안정화
- [ ] 스테이징 시크릿 점검 (STAGING_HOST, STAGING_USER 등)
- [ ] Docker compose 테스트
- [ ] 헬스체크 및 메트릭 엔드포인트 검증

**완료 기준:** 로컬 docker-compose up -d 성공

---

### 시간 8-10: 릴리즈 준비
- [ ] 릴리즈 노트 작성 (v0.2.0)
- [ ] 배포 체크리스트 문서화
- [ ] 태그 + 최종 커밋 푸시

**완료 기준:** git tag v0.2.0 + GitHub Release 생성

---

## 🚀 지금 시작하는 방법

### Step 1: 초기 검증 (지금)
```powershell
cd "c:\Users\hskka\OneDrive\바탕 화면\EduLink"
.\dev-sprint.ps1 -phase test
```

### Step 2: 첫 자동화 커밋 (5분 후)
```powershell
.\dev-sprint.ps1 -phase all
```

### Step 3: GitHub Actions 모니터링
https://github.com/hskkang-hash/edulink/actions

---

## 📊 진행 상태 (실시간 업데이트)

| 단계 | 상태 | 진행률 | 로그 |
|------|------|--------|------|
| 기반 정리 | 🟡 진행중 | 75% | dev-sprint-*.log |
| 코어 개발 | ⬜ 대기 | 0% | - |
| 통합 테스트 | ⬜ 대기 | 0% | - |
| 배포 안정화 | ⬜ 대기 | 0% | - |
| 릴리즈 준비 | ⬜ 대기 | 0% | - |

---

## ⚙️ 스크립트 기능

### dev-sprint.ps1
- **자동 테스트:** pytest 실행 및 결과 로깅
- **코드 검사:** Python 문법 검증
- **자동 커밋:** 변경사항 감지 → git add → git commit
- **자동 푸시:** origin/main으로 푸시 (GitHub Actions 트리거)
- **에러 처리:** 단계별 성공/실패 로깅

### auto-deploy-on-main-push.yml
- **테스트 검증:** pytest 실행 (실패 시 다음 단계 스킵)
- **Docker 빌드:** Dockerfile로 이미지 생성
- **GHCR 배포:** ghcr.io에 자동 푸시
- **결과 리포트:** GitHub Actions summary에 자동 기록

---

## 🔄 반복 사이클 (권장 패턴)

```
반복당 약 15~20분:
1. 로컬 코드 수정 (개발자 또는 Agent)
2. .\dev-sprint.ps1 실행 (테스트 → 커밋 → 푸시)
3. GitHub Actions 자동 실행 (병렬)
4. 결과 확인 + 다음 코드 수정
5. 반복...
```

---

## 📝 로그 위치

- **로컬:** `dev-sprint-YYYYMMDD-HHMMSS.log`
- **GitHub:** https://github.com/hskkang-hash/edulink/actions

---

## ⚠️ 주의사항

1. **스크립트 실행 전 커밋**
   - 로컬 변경사항이 있으면 자동 커밋됨
   - 의도하지 않은 코드 포함 가능성

2. **GitHub Actions 실패 시**
   - 1단계 실패 → 2,3단계 스킵 (자동)
   - 로그 확인: Actions 탭 → 실패한 워크플로우

3. **수동 개입 필요한 경우**
   - 센서티브한 환경변수 추가
   - 데이터베이스 마이그레이션
   - 배포 전 승인

---

**다음: 아래 Step 1 실행하고 결과 보고해주세요!**

# GuardianX 2.0 Product Requirements Document (PRD)

## 1. 개요 (Overview)
GuardianX 2.0은 기존 드론 관제 시스템에서 상용화 및 수익 창출을 목적으로 하는 **Autonomous Drone Operations Platform (Drone Cloud OS)**으로 업그레이드하기 위한 프로젝트입니다.
단순한 제어 시스템을 넘어, 다양한 기종의 드론(DJI, PX4, Custom)을 클라우드 환경에서 통합 관리하고 AI 기반 영상 분석, 자동 미션 수행, 이벤트 탐지 등을 수행하는 B2B/B2G 대상 엔터프라이즈 플랫폼입니다.

---

## 2. 제품 비전 (Product Vision)
`Drone Hardware -> Drone OS -> AI Analytics -> Industry Applications`
GuardianX는 글로벌 상용화를 목표로, 산업 현장과 공공 안전의 무인 자율 비행 운영체제(Drone Cloud Platform)가 되는 것을 지향합니다.

---

## 3. 포지셔닝 및 타겟 시장 (Target Market)
### 3.1 주요 시장 (Primary Target)
* **공공 기관 및 정부**: 재난 방재, 스마트 시티, 치안 및 국경 감시
* **인프라 모니터링**: 교량, 도로, 산업 단지 등 대형 인프라 점검

### 3.2 2차 시장 (Secondary Target)
* 물류 (Drone Delivery)
* 에너지 (발전소 등 주요 시설 감시)
* 보안 (사유지 및 군사 구역 순찰)

---

## 4. 비즈니스 모델 (Business & Revenue)
GuardianX 2.0은 SaaS 기반의 비즈니스 모델(B2B/B2G)을 채택합니다.

* **SaaS Subscription**:
    * **Basic ($5,000/month)**: 드론 편대 기본 관리 기능 제공 (Drone fleet management)
    * **Professional ($15,000/month)**: AI 기반 탐지 모듈 및 분석 기능 추가
* **Enterprise License**:
    * **Enterprise ($500k/year)**: On-Premise 또는 Dedicated Cloud 배포, 커스텀 연동 지원
* **추가 수익원**: AI Analytics API, Drone Dock 인프라 구축, 통합 Data Platform 제공

---

## 5. 파트너십 및 GTM 전략 (Partnership & Marketing)
### 파트너십
* **하드웨어 및 인프라**: DJI, Skydio, Parrot, 통신사(SKT/KT), 클라우드(AWS/NVIDIA).
* **SI 파트너**: Samsung SDS, LG CNS, Accenture 등 엔터프라이즈 레벨 SI 업체 협업.

### Go-to-Market
* 스마트 시티, 보안 산업 컨퍼런스, 글로벌 드론 행사(Demo Projects) 등을 활용한 실증 사업 참여.

---

## 6. 핵심 요구 기능 (Core Features)

### 6.1 Fleet Management (드론 통합 관리)
* **드론 등록 및 관리**: 멀티 브랜드 드론 통합 등록 및 제어
* **상태 모니터링 (Health Monitoring)**: 배터리, 통신 상태, 기체 에러 실시간 추적
* **Firmware 및 Flight Log**: 펌웨어 원격 업데이트, 비행 이력 관리 및 저장

### 6.2 Mission Control (미션 수행 관리)
* **미션 타입 지원**: 순찰(Patrol), 점검(Inspection), 배송(Delivery), 커스텀(Custom) 등.
* **주요 기능**: 웨이포인트(Waypoint) 생성 및 자동 계획, 비행 스케줄링(Mission Scheduling), 실시간 작전 모니터링.

### 6.3 Live Drone Operations (실시간 비행 관제)
* **Live Video Streaming**: 초저지연 실시간 비디오 스트리밍
* **Telemetry Monitoring**: 고도, 속도, 위치, 센서 데이터 모니터링
* **Drone Control**: 필요 시 원격 조종(Teleoperation) 개입 기능

### 6.4 AI Event Detection (AI 탐지 엔진)
* **탐지 대상**: 인물, 차량 식별(Person/Vehicle Detection)
* **이상 징후**: 화재 및 연기 탐지(Smoke/Wildfire Detection), 기타 이상 행동 상황 인식.

### 6.5 Data Platform & Reporting
* **데이터 관리**: 비행 텔레메트리, AI 탐지 결과 이벤트, 영상 로그 통합 저장
* **보고서 자동화**: 일일 운영 보고(Daily Report), 인시던트 보고, 인스펙션 보고 생성 및 Export 기능 (PDF, PPT, DOC)

---

## 7. 로드맵 및 향후 버전 방향 (Roadmap)
* **Phase 1 (6개월)**: 멀티 드론 통합 관리 및 관제 기능(Drone OS/Fleet Management) 상용화
* **Phase 2 (12개월)**: AI 이벤트 예측 엔진, Anomaly 추론 고도화
* **Phase 3 (24개월)**: 드론 스테이션(Drone Dock) 통합 기반 100% 무인 순찰 및 자동 물류 배송 완성을 통한 `Global Drone Operations Platform` 진입

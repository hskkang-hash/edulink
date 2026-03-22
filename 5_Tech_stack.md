# EDULINKS 湲곗닠 ?ㅽ깮 ?곸꽭 紐낆꽭

**Version:** 1.0  
**Date:** March 2026  
**Status:** Technology Selection & Justification  
**Team Lead:** Silicon Valley CTO (Proof-of-Concept)

---

## 1. ?꾨줎?몄뿏??湲곗닠 ?ㅽ깮

### 1.1 媛뺤궗 紐⑤컮????(iOS/Android)

| 移댄뀒怨좊━ | ?좏깮 湲곗닠 | 踰꾩쟾 | ?좎젙 ?댁쑀 |
|---------|---------|------|---------|
| **?꾨젅?꾩썙??* | React Native | 0.73+ | - ?⑥씪 肄붾뱶踰좎씠??(iOS/Android) <br/> - 媛쒕컻 ?앹궛??70% ?μ긽 <br/> - Airbnb+Uber 寃利앸맂 ?ㅽ깮 <br/> - ?쒓뎅 MLM 媛뺤궗痢? 70% Android |
| **?꾧뎄** | Expo | 50.0+ | - OTA 鍮뚮뱶 (?깆뒪?좎뼱 ?뱀씤 遺덊븘?? <br/> - 媛뺤궗 ?낅뜲?댄듃 1?쒓컙 ??諛고룷 <br/> - EAS Build (?먮룞 iOS/Android ?숈떆 鍮뚮뱶) |
| **?곹깭愿由?* | Redux Toolkit | 1.9+ | - ?덉륫 媛?ν븳 ?곹깭 (?뺤궛?? 蹂댁긽 媛숈? 湲덉쑖 ?곗씠?? <br/> - Time-travel ?붾쾭源?(踰꾧렇 異붿쟻 ?⑹씠) <br/> - RTK Query (API 罹먯떛) |
| **?ㅽ듃?뚰궧** | RTK Query | 1.9+ | - Redux? ?듯빀 (?곹깭愿由??쇱썝?? <br/> - ?먮룞 罹먯떛 諛??대쭅 (?뺤궛 ?꾪솴 ?ㅼ떆媛??낅뜲?댄듃) <br/> - ?숆????낅뜲?댄듃 (UX ?μ긽) |
| **UI 而댄룷?뚰듃** | React Native Paper | 5.x | - Material Design 3 以??<br/> - ?쒓뎅 媛뺤궗 ?좏샇 ?붿옄??<br/> - ?묎렐??A11y) ?댁옣 |
| **??愿由?* | React Hook Form | 7.x | - ?깅뒫: form 理쒖냼 ?뚮뜑留?<br/> - ?멸툑/怨꾩쥖?뺣낫 ?낅젰 寃利??꾧꺽 <br/> - 28KB 珥덇꼍??(紐⑤컮??踰덈뱾) |
| **濡쒓퉭/遺꾩꽍** | Sentry | 理쒖떊 | - ?ㅼ떆媛??먮윭 異붿쟻 (GPS 踰꾧렇, ?뺤궛 ?ㅻ쪟) <br/> - ?ъ슜???몄뀡 以묐났 諛⑹? <br/> - ?쒓뎅 DNS 理쒖쟻??|
| **?뚯뒪??* | Jest + Detox | 29.x | - ?좊떅 ?뚯뒪??(Redux 濡쒖쭅) <br/> - E2E ?뚯뒪??(濡쒓렇?멤넂吏?먥넂?뺤궛 ?뚮줈?? <br/> - CI/CD ?먮룞??|

**媛뺤궗 ??踰덈뱾 ?ш린:**
```
Initial: 42MB (?뺤텞: 12MB)
  ?쒋? React Native: 8MB
  ?쒋? Redux: 2MB
  ?쒋? RTK Query: 1MB
  ?쒋? UI ?쇱씠釉뚮윭由? 5MB
  ?붴? 湲고?: 26MB

???ㅼ슫濡쒕뱶 ?쒓컙 (4G): ~3珥?
?낅뜲?댄듃 (OTA via Expo): ~2珥?
```

**痢≪젙 湲곗? (紐⑤컮???깅뒫 ?섏튂):**
- ???湲곌린: 以묎툒 Android (理쒓렐 2~3????異쒖떆, ??κ났媛??ъ쑀 2GB ?댁긽)
- ?ㅽ듃?뚰겕: ?덉젙?곸씤 4G (?ㅽ슚 ???룺 ??20Mbps, RTT 40~60ms)
- 痢≪젙 吏?? ?섎룄沅?湲곗?, CDN 罹먯떆 ?곸쨷 ?곹깭
- ?ㅼ슫濡쒕뱶 ?쒓컙: ?깆뒪?좎뼱 ?ㅼ튂 ?쒖옉遺??泥??ㅽ뻾 媛???쒖젏源뚯?
- OTA ?쒓컙: Expo Updates 諛고룷 ?????ъ떆???쒖젏??踰덈뱾 諛섏쁺 ?꾨즺源뚯?
- 鍮꾧퀬: ?ㅼ젣 ?쒓컙? 湲곌린 ?깅뒫/?듭떊???쇱옟??諛깃렇?쇱슫?????곹깭???곕씪 ?щ씪吏????덉쓬

---

### 1.2 湲곌? 愿由ъ옄 ??(Desktop + Responsive)

| 移댄뀒怨좊━ | ?좏깮 湲곗닠 | 踰꾩쟾 | ?좎젙 ?댁쑀 |
|---------|---------|------|---------|
| **?꾨젅?꾩썙??* | React | 18.3+ | - ?좎뼵??UI (?곹깭愿由?紐낇솗) <br/> - 媛됱떊??JSX 臾몃쾿 <br/> - 怨듭떇 Hooks API 吏??|
| **踰덈뱾??* | Vite | 5.x | - 媛쒕컻 ?쒕쾭 ?쒖옉: 100ms (Webpack ?鍮?10諛?鍮좊쫫) <br/> - 踰덈뱾 ?ш린 30% 異뺤냼 <br/> - HMR 利됱떆 諛섏쁺 (?앹궛?? |
| **?몄뼱** | TypeScript | 5.3+ | - ????덉젙??(湲덉쑖 ?곗씠?? 湲덉븸, 怨꾩쥖踰덊샇) <br/> - IDE ?먮룞?꾩꽦 (媛쒕컻 ?띾룄) <br/> - ?고????먮윭 70% 媛먯냼 |
| **UI ?쇱씠釉뚮윭由?* | Material-UI (MUI) | 5.14+ | - 湲곌? 愿由ъ옄 移쒗솕??(??쒕낫?? ?뚯씠釉? ?? <br/> - ?ㅽ겕紐⑤뱶 ?댁옣 <br/> - ?묎렐??WCAG 2.1 AA 以??|
| **?곹깭愿由?* | Redux Toolkit | 1.9+ | - ?뺤궛 ?곹깭 (pending?뭖ompleted) <br/> - ?ㅼ쨷 ???숆린??<br/> - ?ㅽ듃?뚰겕 ?ъ떆??濡쒖쭅 ?듯빀 |
| **??寃利?* | React Hook Form | 7.x | - ?숈쟻 ?꾨뱶 (媛뺤궗 ?좏깮 ??怨꾩빟 ?먮룞 ?앹꽦) <br/> - ?좏슚??寃??(?먯쿇吏뺤닔 3.3% ?먮룞 怨꾩궛) <br/> - 議곌굔遺 ?꾨뱶 ?뚮뜑留?|
| **?뚯씠釉?* | TanStack Table | 8.x | - 10,000+ ???뺤궛 ?곗씠??怨좎냽 ?뚮뜑留?<br/> - ?뺣젹/?꾪꽣留??섏씠吏?ㅼ씠??<br/> - ???④?/怨좎젙 湲곕뒫 |
| **李⑦듃** | Recharts | 2.10+ | - ?명꽣?숉떚釉?李⑦듃 (留ㅼ텧 異붿씠, 媛뺤궗 ?깃툒 遺꾪룷) <br/> - 諛섏쓳???ㅺ퀎 <br/> - 30+ 李⑦듃 ?좏삎 |
| **?좎쭨** | Day.js | 1.11+ | - 寃쎈웾 (2KB) vs Moment (70KB) <br/> - 遺덈???蹂댁옣 <br/> - ?쒓뎅 濡쒖???吏??|
| **API ?듭떊** | TanStack Query | 5.x | - ?쒕쾭 ?곹깭 ?숆린??(?뺤궛 ?꾪솴 ?ㅼ떆媛? <br/> - ?먮룞 罹먯떛/?대쭅/諛깃렇?쇱슫??媛깆떊 <br/> - 遺꾩궛 異붿쟻 ?듯빀 |
| **?뚯뒪??* | Vitest + Testing Library | 1.x | - 踰덈뱾???듯빀 (Vite) ???뚯뒪???띾룄 5諛?<br/> - ?ъ슜???명꽣?숈뀡 ?뚯뒪??(?대┃?믩뜲?댄꽣 ?낅뜲?댄듃) <br/> - RTL 紐⑤쾾 ?щ? |

**湲곌? ??踰덈뱾 ?ш린:**
```
Production: 380KB (gzip)
  ?쒋? React: 42KB
  ?쒋? Redux/RTK: 28KB
  ?쒋? MUI: 120KB
  ?쒋? TanStack Table: 35KB
  ?쒋? Recharts: 80KB
  ?붴? 湲고?: 75KB

泥?濡쒕뱶 (CDN): <2珥?(1Mbps)
?명꽣?숈뀡源뚯? ?쒓컙: <4珥?
```

**痢≪젙 湲곗? (湲곌? ???깅뒫 ?섏튂):**
- 釉뚮씪?곗?: 理쒖떊 Chrome 湲곗? (?뺤옣 ?꾨줈洹몃옩 理쒖냼?? ?쒗겕由?紐⑤뱶 湲곗?)
- ?붾컮?댁뒪: ?щТ???명듃遺곴툒 (4肄붿뼱 CPU, 8GB RAM ?댁긽)
- ?ㅽ듃?뚰겕: 1Mbps ???룺, RTT 80~120ms, ?⑦궥 ?먯떎瑜?1% 誘몃쭔
- 泥?濡쒕뱶: URL 吏꾩엯遺??二쇱슂 ?붾㈃ Skeleton/?듭떖 ?띿뒪?멸? ?쒖떆?섎뒗 ?쒖젏源뚯?
- ?명꽣?숈뀡源뚯? ?쒓컙: 泥??붾㈃ ?쒖떆 ??二쇱슂 踰꾪듉 ?대┃/?뚯씠釉??꾪꽣 諛섏쓳 媛???쒖젏源뚯?
- 罹먯떆 議곌굔: 泥?濡쒕뱶??cold cache 湲곗?, ?щ갑臾??깅뒫? JS/CSS 罹먯떆 ?꾨왂(?댁떆 ?뚯씪) ?곸슜
- 鍮꾧퀬: ?ㅼ젣 ?섏튂??釉뚮씪?곗? ??遺?? CDN edge 嫄곕━, ?ㅼ떆媛?API ?묐떟 吏?곗뿉 ?곕씪 蹂??媛??

**?깅뒫 理쒖쟻??**
```
Code Splitting:
?쒋? 硫붿씤 踰덈뱾 (濡쒓렇??: 80KB
?쒋? ??쒕낫??(lazy): 120KB
?쒋? ?뺤궛愿由?(lazy): 100KB
?붴? ?ㅼ젙 (lazy): 80KB

罹먯떛 ?꾨왂:
?쒋? JS/CSS: 1??(踰꾩쟾 ?댁떛)
?쒋? ?대?吏: 30??
?쒋? API: 5遺?(?뺤궛? ?ㅼ떆媛?
?붴? HTML: No-cache (踰꾩쟾 異붿쟻)
```

---

### 1.3 ?덊띁 愿由ъ옄 ??

| 移댄뀒怨좊━ | 湲곗닠 | 踰꾩쟾 | 李⑥씠??|
|---------|------|------|--------|
| **湲곕낯** | React 18 | 18.3+ | 湲곌? ?밴낵 ?숈씪 ?ㅽ깮 |
| **愿由ъ옄 ??쒕낫??* | React-Admin | 4.x | - CRUD 湲곕낯 ? (媛뺤궗 ?뱀씤, MLM 愿由? <br/> - 沅뚰븳 湲곕컲 UI ?쒖뼱 (??븷蹂?硫붾돱) <br/> - 600+ ?댁옣 而댄룷?뚰듃 |
| **沅뚰븳 愿由?* | Casbin RBAC | 5.x | - ?꾨줎?? 硫붾돱/踰꾪듉 ?쒖떆 ?щ? <br/> - 諛깆뿏?? API 沅뚰븳 寃利??댁쨷??|
| **?뚯뒪??* | Cypress | 13.x | - E2E: 媛뺤궗 ?뱀씤 ?뚰겕?뚮줈??<br/> - ?ㅽ겕由곗꺑 鍮꾧탳 (UI ?뚭? ?뚯뒪?? <br/> - 蹂묐젹 ?ㅽ뻾 (CI 15遺???5遺? |

---

## 2. 諛깆뿏??湲곗닠 ?ㅽ깮

### 2.1 API ?쒕쾭 (FastAPI)

| 移댄뀒怨좊━ | ?좏깮 湲곗닠 | 踰꾩쟾 | ?좎젙 ?댁쑀 |
|---------|---------|------|---------|
| **?꾨젅?꾩썙??* | FastAPI | 0.110+ | - ?숆린/鍮꾨룞湲??쇱슜 (鍮좊Ⅸ ?묐떟 + ?μ떆媛?諛곗튂) <br/> - ?먮룞 臾몄꽌??(Swagger UI) <br/> - ????뚰듃 (Pydantic) <br/> - 蹂??뚯궗 寃利? ?몄뒪?댁뒪 ??1000 RPS 泥섎━ |
| **ORM** | SQLAlchemy | 2.0+ | - PostgreSQL 怨좉툒 湲곕뒫 ?쒖슜 (JSONB, Array, Enum) <br/> - ?몃옖??뀡 ?쒖뼱 (?뺤궛 臾닿껐?? <br/> - 留덉씠洹몃젅?댁뀡 (Alembic) ?먮룞??|
| **寃利?* | Pydantic | 2.x | - ?붿껌 寃利?(3.3% ?먯쿇吏뺤닔 湲덉븸 ?먮룞 怨꾩궛) <br/> - JSON 吏곷젹???붿쭅?ы솕 理쒖쟻??<br/> - 留?由ы섏뒪??10ms ??寃利?|
| **?몄쬆** | FastAPI-Users | 13.x | - OAuth2 (移댁뭅?ㅽ넚) + JWT ?듯빀 <br/> - ?뷀샇 ?댁떛 (argon2) <br/> - ?좏겙 媛깆떊 ?먮룞??<br/> - ?ㅼ쨷 諛깆뿏??吏??(DB/Redis) |
| **鍮꾨룞湲?* | Celery | 5.3+ | - ?묒뾽 ??(?붾쭚 ?뺤궛 怨꾩궛) <br/> - 寃곌낵 罹먯떛 (Redis) <br/> - ?ъ떆???뺤콉 (吏??諛깆삤?? <br/> - 紐⑤땲?곕쭅 (Flower UI) |
| **釉뚮줈而?* | RabbitMQ | 3.13+ | - 硫붿떆吏 蹂댁옣 (Ack, ?ъ쟾?? <br/> - ?대윭?ㅽ꽣 HA <br/> - 寃쎈웾 (硫붾え由??⑥쑉) |
| **濡쒓퉭** | Structlog | 23.x | - 援ъ“?붾맂 濡쒓렇 (JSON) <br/> - OpenSearch ?됱씤 ?⑹씠 <br/> - ?깅뒫: 濡쒓퉭 ?ㅻ쾭?ㅻ뱶 <1% |
| **?뚯뒪??* | pytest | 7.x | - ?쎌뒪泥?(DB, Redis, Celery 紐⑺궧) <br/> - 而ㅻ쾭由ъ? 80%+ 紐⑺몴 <br/> - 蹂묐젹 ?ㅽ뻾 (pytest-xdist) |

**FastAPI ?깅뒫:**
```
?⑥씪 ?몄뒪?댁뒪 ?깅뒫 (AWS t3.large):
?쒋? ?붿껌 吏?곗떆媛?(p99): 45ms
?쒋? 泥섎━?? 500+ RPS
?쒋? ?숈떆 ?곌껐: 10,000+
?붴? 硫붾え由? 200MB (Gunicorn ?뚯빱 1媛?

硫???뚯빱 (4媛?:
?쒋? 泥섎━?? 2000+ RPS
?쒋? 吏?곗떆媛?(p99): 40ms
?붴? 硫붾え由? 800MB

?섑룊 ?뺤옣:
?쒋? Pod ?먮룞 異붽?: CPU > 70%
?쒋? 理쒕? 10媛?Pod (20,000 RPS)
?붴? ?ㅼ슫 (CPU < 30%): ?먮룞 ?쒓굅
```

**痢≪젙 湲곗? (FastAPI ?깅뒫 ?섏튂):**
- 遺???꾧뎄: k6 湲곗? (?쇳빀 ?쒕굹由ъ삤: read 70%, write 20%, auth/湲고? 10%)
- ?곗씠??議곌굔: ?섑뵆 ?곗씠??100留?嫄?湲곗?, 二쇱슂 ?몃뜳???곸슜 ?꾨즺 ?곹깭
- ?뚯빱 援ъ꽦: Gunicorn + Uvicorn Worker, ?뚯빱??理쒕? ?숈떆 ?붿껌 1,000 湲곗?
- 吏?곗떆媛?p99): 5遺??댁긽 ?덉젙 援ш컙?먯꽌 吏묎퀎 (?뚮컢??1遺??쒖쇅)
- 泥섎━??RPS): ?먮윭??1% 誘몃쭔???좎??섎뒗 理쒕? ?덉젙 泥섎━??湲곗?
- 硫붾え由? ?좏뵆由ъ??댁뀡 ?꾨줈?몄뒪 RSS + ?고????ㅻ쾭?ㅻ뱶 ?ы븿 ?됯퇏媛?
- ?섑룊 ?뺤옣: HPA scale-out/in ??10遺?愿李?援ш컙 ?됯퇏媛?湲곗?
- 鍮꾧퀬: ?ㅼ젣 ?댁쁺媛믪? 荑쇰━ 蹂듭옟?? 罹먯떆 ?곸쨷瑜? ?몃? API 吏?곗뿉 ?곕씪 ?щ씪吏????덉쓬

---

### 2.2 ?곗씠?곕쿋?댁뒪 怨꾩링

#### PostgreSQL 15

| 援ъ꽦 | ?ъ뼇 | ?좎젙 ?댁쑀 |
|------|------|---------|
| **Primary** | AWS RDS <br/> db.r6g.2xlarge <br/> 500GB EBS (gp3) | - ACID ?몃옖??뀡 (?뺤궛 臾닿껐?? <br/> - 蹂듭옟??荑쇰━ (?붾퀎 ?뺤궛 WITH ?? <br/> - JSONB 吏??(?좎뿰???ㅽ궎留? <br/> - ?ㅼ씠?곕툕 諛곗뿴 ???(?덈꺼蹂??ㅼ슫?쇱씤 ID) <br/> - ???덈꺼 蹂댁븞 (RLS: 媛뺤궗???먯떊 ?뺤궛留? |
| **Replica 1** | ?쎄린 ?꾩슜 <br/> 寃쎄린 AZ | - 蹂닿퀬??荑쇰━ (硫붿씤 ?곹뼢 ?놁쓬) <br/> - ??쒕낫???ㅼ떆媛??듦퀎 |
| **Replica 2** | ?쎄린 ?꾩슜 <br/> ?몄쿇 AZ | - 援먯쑁泥?吏??紐⑤땲?곕쭅 荑쇰━ <br/> - ?ы빐 蹂듦뎄 ?湲?|
| **Backup** | AWS Backup <br/> ??2??<br/> 7??蹂닿? | - RPO: 12?쒓컙 <br/> - PITR (Point-in-time recovery) 7??<br/> - ?붾뱶-???붾뱶 ?뷀샇??|

**PostgreSQL ?쒖슜 ?щ? (EDULINKS ?뱁솕):**

```sql
-- MLM 怨꾩링 愿怨?(諛곗뿴 + JSONB)
CREATE TABLE instructor_mlm (
    id UUID PRIMARY KEY,
    instructor_id UUID,
    level INT,  -- 1, 2, 3
    pv DECIMAL(12,2),  -- Personal Volume
    downline_ids UUID ARRAY,  -- ?ㅼ슫?쇱씤 媛뺤궗
    hierarchy JSONB,  -- {level1: 45紐? level2: 8紐?
    monthly_pv DECIMAL(12,2) GENERATED ALWAYS AS (
        /* 蹂몄씤 + ?ㅼ슫?쇱씤 ?⑷퀎 */
    ) STORED
);

-- ?먯쿇吏뺤닔 3.3% ?먮룞 怨꾩궛
CREATE TABLE settlements (
    gross_amount DECIMAL(12,2),
    withholding DECIMAL(12,2) GENERATED ALWAYS AS (
        ROUND(gross_amount * 0.033, 0)
    ) STORED,
    net_payment DECIMAL(12,2) GENERATED ALWAYS AS (
        gross_amount - withholding
    ) STORED
);

-- ???덈꺼 蹂댁븞 (RLS)
CREATE POLICY instructor_view_own_earnings ON settlements
    FOR SELECT TO instructor
    USING (instructor_id = current_user_id());
    
-- 媛뺤궗???먯떊 ?뺤궛留?SELECT 媛??
```

---

#### Redis 7 (?대윭?ㅽ꽣)

| ?ъ슜泥?| ?곗씠??| TTL | ?ш린 |
|--------|--------|-----|------|
| **?몄뀡 ???* | user_id, role, permissions | 1?쒓컙 | 1-2GB |
| **API 罹먯떆** | /instructor/dashboard <br/> /org/postings <br/> /settlements/monthly | 5遺?| 3-5GB |
| **?ㅼ떆媛?移댁슫??* | ?ㅻ뒛???섏뾽??<br/> ?붾퀎 留ㅼ텧??(?꾩떆) <br/> SOS ?뚮┝ ?湲?| 1??| 0.5-1GB |
| **遺꾩궛 Lock** | ?몃쭏???뺤궛 諛곗튂) <br/> ?댁쨷 ?좎껌 諛⑹? | 30珥?| <100MB |
| **Pub/Sub** | WebSocket 釉뚮줈?쒖틦?ㅽ듃 <br/> ?뚮┝ ??| - | 利됱떆 ?꾩넚 |
| **Rate Limiting** | ?붿껌 移댁슫??(IP/User 湲곕컲) | 1遺?| 500MB |

**Redis ?깅뒫:**
```
?묒뾽蹂??묐떟?쒓컙:
?쒋? GET/SET: <1ms
?쒋? INCR (?붿껌 移댁슫??: <0.1ms
?쒋? PUBLISH (釉뚮줈?쒖틦?ㅽ듃): <5ms
?붴? EXPIRE (TTL): <0.1ms

泥섎━??
?쒋? ?⑥씪 ?몃뱶: 100,000 OPS
?쒋? ?대윭?ㅽ꽣 (6?몃뱶): 600,000 OPS
?붴? 硫붾え由? 32GB (紐⑤뱺 ?댁쁺 ?곗씠???섏슜 媛??
```

**Measurement Criteria (Redis Performance):**
- Load tool: `redis-benchmark` and k6 mixed scenario (cache hit 60%, write/update 25%, pub/sub 10%, rate-limit INCR 5%)
- Dataset condition: keyspace pre-warmed to 70% of expected production cardinality; TTL distribution includes 1m/5m/1h buckets
- Latency metric: p99 over a stable 5-minute window after 2-minute warm-up
- Throughput metric: max sustainable OPS with error rate under 0.5% and no timeout spikes
- Cluster setup: 6-node cluster, replication enabled, persistence mode (`AOF everysec`) fixed during tests
- Resource baseline: dedicated Redis nodes with CPU below 75% and memory fragmentation ratio below 1.5
- Note: cross-AZ traffic and eviction policy (`allkeys-lru` vs `volatile-ttl`) can materially change p99 and OPS

---

#### OpenSearch 2.0+ (濡쒓렇 ??μ냼)

| ?⑸룄 | ?몃뜳??| 蹂닿? 湲곌컙 | ?щ? |
|-----|--------|---------|------|
| **?묎렐 濡쒓렇** | logs-app-{date} | 90??| "/instructor/postings" GET |
| **?먮윭 濡쒓렇** | logs-error-{date} | 180??| Exception traceback (Sentry) |
| **媛먯떆 濡쒓렇** | audit-logs-{date} | 1??| "媛뺤궗 ?뱀씤", "?뺤궛 蹂댁젙" 湲곕줉 |
| **?깅뒫 硫뷀듃由?* | metrics-{date} | 30??| ?묐떟?쒓컙, ?먮윭?? QPS |
| **?뚮┝/?대깽??* | events-{date} | 30??| "SOS 留ㅼ묶??, "?뺤궛 ?꾨즺" |

**OpenSearch 荑쇰━ ?덉떆:**
```json
// 吏?쒖＜ 媛뺤궗 ?묒쓽 議고쉶
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

// 寃곌낵: ?대뼡 媛뺤궗?ㅼ씠 怨듦퀬瑜?留롮씠 議고쉶?덈뒗媛?
```

**OpenSearch Performance:**
```
Indexing throughput:
- Sustained ingest: 30,000 docs/sec (6 data nodes)

Search latency:
- Aggregation query p95: <300ms
- Term/filter query p95: <120ms

Retention and storage:
- 90-day hot+warm policy with rollover at 50GB/shard
```

**Measurement Criteria (OpenSearch Performance):**
- Load tool: OpenSearch Benchmark with replayed production-like logs and dashboard query traces
- Workload mix: ingest 70%, dashboard search 20%, audit search 10%
- Data condition: 90-day index set with realistic field cardinality (instructor_id, org_id, status, timestamp)
- Latency metric: p95/p99 measured for 10 minutes after shard allocation and cache warm-up complete
- Throughput metric: docs/sec and query/sec captured with reject count, timeout count, and GC pause time
- Cluster control: shard count/replica count fixed; refresh interval and ILM rollover policy fixed during benchmark
- Note: mapping explosion, oversized shards, and cold tier spillover can degrade search latency significantly

---

### 2.3 ?몃? 寃곗젣 & ?몃Т ?곕룞

#### Stripe (援?젣 移대뱶 寃곗젣)

```
湲곌???媛뺤궗 湲됱뿬 ?좊텋(Advance) 湲곕뒫:

1. 湲곌???"媛뺤궗 A?먭쾶 100,000???좉툒湲? ?낅젰
2. Stripe Payment Intent ?앹꽦
3. 湲곌? 怨꾩젙?먯꽌 ?먮룞 寃곗젣
4. ?먯뒪?щ줈 怨꾩젙??蹂닿?
5. ?붾쭚 ?뺤궛?≪뿉???먮룞 李④컧
6. ?섍툒(Refund) ?꾨줈?몄뒪

API:
?쒋? Stripe::PaymentIntent.create
?쒋? Stripe::Account.create (?곌껐 怨꾩젙)
?쒋? Stripe::Transfer.create (?뺤궛湲덉뫁)
?붴? Stripe::Refund.create (諛섑솚湲?

?쒓퀎:
?쒋? 援?궡 ?좎슜移대뱶留?吏??
?쒋? 移대뱶???쒕룄 ?쒖빟
?붴? ?섏닔猷? 2.9% + 100??
```

#### NHN KCP (援?궡 ?좏샇 寃곗젣)

```
?쒓뎅 湲곌?/媛뺤궗 ??ㅼ닔媛 ?좏샇?섎뒗 PG:

二쇱슂 湲곕뒫:
?쒋? ?좎슜移대뱶: 5留?500留뚯썝 ?쒕룄
?쒋? 怨꾩쥖?댁껜: 臾댄븳 (?ㅼ쓬???뺤궛)
?쒋? ?대???鍮뚮쭅: KCP留?吏??
?붴? ?좉툑 湲곕뒫: ?먮룞?댁껜 ?곕룞

?곕룞 ?꾨줈?몄뒪:
1. KCP 媛留뱀젏 ID 諛쒓툒
2. API ?????(?섍꼍 蹂??
3. 寃곗젣 ?붾㈃ ?곕룞 (JavaScript)
4. ?뱀씤 ?뚮윭洹??섏떊
5. 二쇨린??留ㅼ텧 ?뺤궛

?섏닔猷?
?쒋? ?좎슜移대뱶: 2.7% + 60??
?쒋? 怨꾩쥖?댁껜: 1,000??(臾댄븳)
?붴? ?대??? 3.5% + 50??

理쒖쥌 ?좏깮: 援ы쁽 媛꾨떒???믪쓬, 援?궡 移쒗솕??

from nhn_kcp import KcpGateway
gateway = KcpGateway(site_code, site_key)
result = gateway.pay(
    order_id="ORD-123",
    amount=100000,
    customer_name="源媛뺤궗",
    good_name="3???섏뾽猷??뺤궛"
)
```

---

#### HomeTax API (?섍툒湲?議고쉶)

```python
# ?덊깮??媛꾪렪 API ?몄텧
from hometax_api import HomeTaxClient

client = HomeTaxClient(
    api_key=settings.HOMETAX_API_KEY,
    cert_path="/etc/ssl/hometax.pem"
)

# 媛뺤궗??誘몄닔???섍툒湲?議고쉶
response = client.get_refund_status(
    user_auth_token=kakao_token,  # ?ъ슜??媛꾪렪?몄쬆 ?좏겙
    tax_years=[2025, 2024, 2023]
)

# ?묐떟:
{
    "2025": {
        "income": 20000000,
        "estimated_tax": 2000000,
        "refund": 1200000,
        "filed": False
    }
}

# ?덉씠?댁떆: 2~3珥?(?ㅽ듃?뚰겕 ?ы븿)
# ?ъ떆?? 3??30遺?(?덊깮???쒕쾭 遺덉븞??
# 罹먯떆: 1?쒓컙 (?ъ슜?먮퀎)
```

---

#### Samcheomsam API (湲고븳 ???좉퀬)

```python
# ?곗찞??湲고븳 ???좉퀬 API
from samcheomsam_api import SamcheomsaamClient

client = SamcheomsaamClient(
    api_key=settings.SAMCHEOMSAM_API_KEY,
    partner_id="edulinks"
)

# ?좉퀬 ????좎껌
filing = client.submit_deferred_filing(
    applicant={
        "name": "源媛뺤궗",
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
        "fee_rate": 0.25,  # 25% ?섏닔猷?
        "cms_auto_withdraw": True,
        "withdraw_date": "2026-04-05"
    }
)

# ?묐떟:
{
    "filing_id": "2026-123456",
    "status": "submitted",
    "submitted_at": "2026-03-22",
    "filing_number": "SAMCHEO-2026-001",
    "expected_approval": "2026-04-10",
    "net_refund": 900000  # 1200000 - (1200000 * 0.25)
}

# 鍮꾩슜: ?좉퀬猷?50,000??+ ?섏닔猷?(?섍툒??횞 20~25%)
# ?깃났瑜? 98% (援?꽭泥??먮룞 ?뱀씤)
# ?낃툑: 2二?(援?꽭泥?泥섎━ + 怨꾩쥖 ?댁껜)
```

---

## 3. ?명봽??& DevOps ?ㅽ깮

### 3.1 而⑦뀒?대꼫 & ?ㅼ??ㅽ듃?덉씠??

| 湲곗닠 | 踰꾩쟾 | ?좎젙 ?댁쑀 |
|-----|------|---------|
| **而⑦뀒?대꼫** | Podman | 3.4+ | - Docker蹂대떎 蹂댁븞 (rootless) <br/> - 硫붾え由??ㅻ쾭?ㅻ뱶 ??쓬 <br/> - Kubernetes ?명솚 |
| **?ㅼ??ㅽ듃?덉씠??* | Kubernetes | 1.28+ | - ?먮룞 ?ㅼ??쇰쭅 <br/> - rolling update (臾댁쨷??諛고룷) <br/> - ?먭? 蹂듦뎄 (Pod ?ㅼ슫 ?먮룞 ?ъ떆?? <br/> - 硫???뚮꼳??寃⑸━ (namespace) |
| **?멸렇?덉뒪** | Caddy | 2.7+ | - ?먮룞 HTTPS (Let's Encrypt) <br/> - 由щ줈??遺덊븘??(?숈쟻 ?ㅼ젙) <br/> - GoLang 湲곕컲 怨좎꽦??|
| **?덉??ㅽ듃由?* | ECR (AWS) | - | - ?꾨씪?대퉿 (湲곕컲 ?쒖꽕 鍮꾩슜) <br/> - ?먮룞 ?ㅼ틪 (痍⑥빟?? <br/> - Kubernetes ?듯빀 |

**Kubernetes 諛고룷 援ъ꽦:**

```yaml
# ?곸쓳???ㅼ??쇰쭅
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

# 濡ㅻ쭅 ?낅뜲?댄듃
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
      maxUnavailable: 0  # 臾댁쨷??諛고룷
  template:
    spec:
      containers:
      - name: api
        image: edulinks/api:v1.2.3
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        readinessProbe:  # ?몃옒???섏떊 以鍮??뺤씤
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:  # ?꾨줈?몄뒪 ?앹〈 ?뺤씤
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 20
```

---

### 3.2 CI/CD ?뚯씠?꾨씪??

| ?ㅽ뀒?댁? | ?꾧뎄 | ?묒뾽 |
|---------|------|------|
| **鍮뚮뱶** | GitHub Actions | - 肄붾뱶 而댄뙆??(TypeScript/Python) <br/> - ?섏〈???ㅼ튂 <br/> - ?뚯뒪???ㅽ뻾 (蹂묐젹 10媛??묒뾽) <br/> - 肄붾뱶 ?ㅼ틪 (SonarQube) <br/> - 而⑦뀒?대꼫 鍮뚮뱶 <br/> - ECR ?몄떆 |
| **諛고룷** | ArgoCD | - GitOps: Git 而ㅻ컠 = 諛고룷 <br/> - blue-green 諛고룷 <br/> - ?먮룞 濡ㅻ갚 (health check ?ㅽ뙣) <br/> - ?섍꼍蹂??ㅼ젙 (dev/staging/prod) |
| **紐⑤땲?곕쭅** | Prometheus + Grafana | - ?ㅼ떆媛?硫뷀듃由??섏쭛 <br/> - 而ㅼ뒪? ??쒕낫??<br/> - ?뚮┝ 洹쒖튃 (Slack ?듬낫) |
| **濡쒓퉭** | ELK Stack | - Elasticsearch: 濡쒓렇 ???<br/> - Logstash: 濡쒓렇 ?뚯떛/蹂??<br/> - Kibana: 寃???쒓컖??|

**諛고룷 ?뚯씠?꾨씪??**

```
1. Git push (develop 釉뚮옖移?
   ??
2. GitHub Actions ?몃━嫄?
   ?쒋? 由고듃 & ?좊떅 ?뚯뒪??(5遺?
   ?쒋? E2E ?뚯뒪??(Staging ?섍꼍) (15遺?
   ?붴? Coverage 由ы룷??(>80% ?꾩닔)
   ??
3. ?듦낵 ??而⑦뀒?대꼫 鍮뚮뱶
   ?쒋? Docker ?대?吏 ?앹꽦
   ?쒋? Trivy 痍⑥빟???ㅼ틪
   ?붴? ECR???몄떆 (?쒓렇: git-sha)
   ??
4. ArgoCD 媛먯?
   ?쒋? Git ??μ냼 ??(1遺?二쇨린)
   ?쒋? Kubernetes manifests 蹂寃?媛먯?
   ?붴? ?대윭?ㅽ꽣??諛고룷 ?좎껌
   ??
5. Kubernetes 濡ㅻ쭅 ?낅뜲?댄듃
   ?쒋? ??Pod ?쒖옉 (readiness ?湲?
   ?쒋? ?몃옒???먯쭊???대룞 (max-surge: 1)
   ?쒋? 湲곗〈 Pod 醫낅즺 (?곌껐 ?쒕젅?? 30珥?
   ?붴? ?꾨즺 ??紐⑤땲?곕쭅 (5遺?
   ??
6. ?ㅽ뙣 ???먮룞 濡ㅻ갚
   ?쒋? Health check ?ㅽ뙣
   ?쒋? ?먮윭??> 10% (Prometheus ?뚮┝)
   ?붴? ?댁쟾 踰꾩쟾 蹂듭썝 (ArgoCD)

珥??뚯슂 ?쒓컙: 媛쒕컻 ?앸????꾨줈?뺤뀡 諛고룷源뚯? 35遺?
?ㅼ슫??? 0遺?(濡ㅻ쭅 ?낅뜲?댄듃)
```

---

### 3.3 紐⑤땲?곕쭅 & 濡쒓퉭

| ?ㅽ깮 | ??븷 | 硫뷀듃由?|
|------|------|--------|
| **Prometheus** | 硫뷀듃由??섏쭛 | - API ?묐떟?쒓컙 (p50, p95, p99) <br/> - ?먮윭??(5xx, 4xx) <br/> - Pod CPU/硫붾え由?<br/> - DB 荑쇰━ ?쒓컙 <br/> - Redis ?덊듃??|
| **Grafana** | ?쒓컖??| - ?ㅼ떆媛???쒕낫??<br/> - ?댁긽 ?먯? (?댁긽 ?믪? 吏?곗떆媛? <br/> - SLA 異붿쟻 (99.99% 紐⑺몴) |
| **Sentry** | ?먮윭 異붿쟻 | - ?덉쇅 諛쒖깮 <br/> - ?ㅽ깮 ?몃젅?댁뒪 <br/> - ?ъ슜???몄뀡 ?ы쁽 <br/> - 由대━利?異붿쟻 |
| **ELK** | 濡쒓렇 ???| - ?묎렐 濡쒓렇 (API ?몄텧) <br/> - ?먮윭 濡쒓렇 (?덉쇅) <br/> - 媛먯떆 濡쒓렇 (蹂댁븞) <br/> - 90??蹂닿? |

---

## 4. 媛쒕컻 ?꾧뎄 & ?섍꼍

### 4.1 濡쒖뺄 媛쒕컻 ?섍꼍

```bash
docker-compose.yml (濡쒖뺄 媛쒕컻)
?쒋? PostgreSQL 15
?쒋? Redis 7
?쒋? OpenSearch 2.0
?쒋? RabbitMQ 3.13
?쒋? Minio (S3 ?명솚 ?ㅽ넗由ъ?)
?붴? LocalStack (AWS ?쒕퉬???쒕??덉씠??

?쒖옉:
$ docker-compose up -d

紐⑤몢 以鍮꾨맖:
$ npm start  # ?꾨줎?몄뿏??
$ poetry run uvicorn main:app --reload  # 諛깆뿏??
```

### 4.2 ?⑦궎吏 愿由?

| ?몄뼱 | ?꾧뎄 | 踰꾩쟾 |
|------|------|------|
| Python | Poetry | 1.7+ |
| Node.js | npm | 10.x |
| 而⑦뀒?대꼫 | Podman | 4.x |
| ?명봽??| Terraform | 1.6+ |

---

## 5. 蹂댁븞 ?ㅽ깮

### 5.1 ?몄쬆 & ?뷀샇??

| ??ぉ | 湲곗닠 | ?ъ뼇 |
|-----|------|------|
| **HTTPS** | TLS 1.3 | - 紐⑤뱺 ?듭떊 ?뷀샇??<br/> - ?먮룞 ?몄쬆??媛깆떊 (Caddy) <br/> - HSTS ?쒖꽦??(1?? |
| **?몄쬆** | OAuth2 + JWT | - 移댁뭅?ㅽ넚 媛꾪렪?몄쬆 <br/> - Access: 1?쒓컙, Refresh: 7??<br/> - HS256 ?쒕챸 |
| **?뷀샇** | Argon2 | - 媛뺤궗 怨꾩젙 鍮꾨?踰덊샇 <br/> - 硫붾え由?吏묒빟??(?덉씤蹂댁슦 ?뚯씠釉?怨듦꺽 諛⑹뼱) |
| **API ?좏겙** | Bearer Token | - ?몃? ?쒕퉬???듯빀 (?덊깮?? ?곗찞?? <br/> - ?섍꼍 蹂?????(?덈? ?섎뱶肄붾뵫 湲덉?) |

### 5.2 ?곗씠??蹂댄샇

- **?꾩넚 以?*: TLS 1.3 ?뷀샇??
- **?????*: ?곗씠?곕쿋?댁뒪 ?뷀샇??(AWS RDS ?먮룞)
- **誘쇨컧 ?뺣낫**: AES-256 ?뷀샇??(怨꾩쥖踰덊샇, SSN)
- **媛먯떆 濡쒓렇**: 1??蹂닿? (媛먯떆踰?

---

**媛쒖꽑 湲고쉶:**

| ??ぉ | ?꾩옱 | ?ν썑 |
|-----|------|------|
| **紐⑤컮??* | React Native | Flutter (??鍮좊Ⅸ ?깅뒫) |
| **寃??* | OpenSearch | Vespa (???뺥솗??異붿쿇 寃?? |
| **ML** | 湲곕낯 ?뚭퀬由ъ쬁 | TensorFlow (媛뺤궗-?숈깮 留ㅼ묶 媛쒖꽑) |
| **?ㅼ떆媛?* | WebSocket | gRPC (?吏???듭떊) |

---

**?ㅼ쓬 臾몄꽌: [6_WBS.md](6_WBS.md) - ?낅Т 遺꾪빐 援ъ“ 諛??쇱젙**


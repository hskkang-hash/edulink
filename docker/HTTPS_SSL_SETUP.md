# HTTPS/SSL 설정 가이드

## 개요

EduLink는 Nginx 리버스 프록시를 통해 HTTPS/SSL 보안 연결을 제공합니다.

**아키텍처:**
```
클라이언트 (HTTPS:443)
    ↓
Nginx 리버스 프록시 (HTTPS 종료)
    ↓
Flask 백엔드 (HTTP:5000 내부)
```

---

## 빠른 시작

### Step 1: 테스트 인증서 생성 (개발용)

```bash
cd docker

# SSL 디렉토리 생성
mkdir -p ssl

# 자체 서명 인증서 생성 (30일 유효)
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 30 -nodes \
  -subj "/C=KR/ST=Seoul/L=Seoul/O=EduLink/CN=localhost"
```

**주의:** 브라우저에서 보안 경고가 나타납니다. 개발 환경에서만 사용하세요.

### Step 2: Docker Compose 실행

```bash
cd docker
docker-compose up -d
```

### Step 3: HTTPS로 접근

```bash
# 자체 서명 인증서 무시하고 접근
curl -k https://localhost/health

# 또는 브라우저에서
https://localhost
```

---

## 프로덕션 배포 (Let's Encrypt)

### Step 1: Certbot 설치

```bash
sudo apt-get install certbot python3-certbot-nginx
```

또는 Docker를 사용하는 경우:

```bash
docker run -it --rm \
  -v $(pwd)/docker/certbot/conf:/etc/letsencrypt \
  -v $(pwd)/docker/certbot/www:/var/www/certbot \
  certbot/certbot certonly --webroot \
  -w /var/www/certbot \
  -d your-domain.com \
  -d www.your-domain.com \
  --email your-email@example.com \
  --agree-tos \
  --non-interactive
```

### Step 2: Nginx 설정 업데이트

`docker/nginx.conf`에서 인증서 경로 변경:

```nginx
ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
```

### Step 3: Docker Compose 업데이트

certbot 볼륨을 추가하려면 docker-compose.yml이 이미 설정되어 있습니다.

### Step 4: 인증서 자동 갱신

Let's Encrypt 인증서는 90일마다 갱신이 필요합니다.

```bash
# 매월 1일 오전 3시에 갱신하는 cron 작업
0 3 1 * * certbot renew --quiet && docker-compose -f docker/docker-compose.yml reload
```

또는 Docker 컨테이너로:

```bash
docker run -d \
  -v $(pwd)/docker/certbot/conf:/etc/letsencrypt \
  -v $(pwd)/docker/certbot/www:/var/www/certbot \
  --name certbot-renew \
  mcuadros/certbot \
  --entrypoint /bin/sh -c \
  'while true; do certbot renew --quiet && sleep 1d; done'
```

---

## SSL 보안 설정 상세

### 지원되는 프로토콜
- TLSv1.2 (최소)
- TLSv1.3 (권장)

### 암호화 알고리즘
```
HIGH:!aNULL:!MD5
```

### HSTS (HTTP Strict Transport Security)
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
```
- 1년 동안 모든 연결을 HTTPS로 강제

### 보안 헤더
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

---

## 인증서 관리

### 현재 인증서 확인

```bash
openssl x509 -in ssl/cert.pem -text -noout
```

### 인증서 유효 기간 확인

```bash
openssl x509 -enddate -noout -in ssl/cert.pem
```

### 인증서 CSR (Certificate Signing Request) 생성

상용 CA에서 인증서를 구입하는 경우:

```bash
openssl req -new -key ssl/key.pem -out ssl/certificate.csr \
  -subj "/C=KR/ST=Seoul/L=Seoul/O=EduLink/CN=your-domain.com"
```

---

## 문제 해결

### "ssl_stapling" 오류
OCSP stapling이 필요한 경우 nginx.conf에 추가:

```nginx
ssl_stapling on;
ssl_stapling_verify on;
ssl_trusted_certificate /etc/letsencrypt/live/your-domain.com/chain.pem;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
```

### "127.0.0.1 rejected by the server cert, but we couldn't verify a chain"

자체 서명 인증서 사용 시 정상입니다. 프로덕션에서는 Let's Encrypt 사용:

```bash
curl -k https://localhost/health  # -k는 비활성화
```

### Nginx 재로드 안 됨

```bash
docker-compose restart nginx
```

### 인증서 갱신 실패

```bash
# 수동 갱신
docker run -it --rm \
  -v $(pwd)/docker/certbot/conf:/etc/letsencrypt \
  -v $(pwd)/docker/certbot/www:/var/www/certbot \
  certbot/certbot renew --force-renewal
```

---

## 성능 최적화

### HTTP/2 지원
```nginx
listen 443 ssl http2;
```

### Gzip 압축
```nginx
gzip on;
gzip_min_length 1000;
gzip_types text/plain text/css application/json;
```

### 세션 캐싱
```nginx
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
```

---

## SSL Labs 테스트

[SSL Labs](https://www.ssllabs.com/ssltest/)에서 등급을 확인할 수 있습니다:

1. 도메인 입력
2. Assess my server 클릭
3. 결과 확인 (A+ 권장)

프로덕션 구성 최적화:
- TLSv1.2 이상만 지원
- 강력한 암호화 알고리즘 사용
- HSTS 활성화
- OCSP stapling 설정

---

## 체크리스트

### 개발 환경 (자체 서명)
- [ ] `docker/ssl/` 디렉토리 생성
- [ ] OpenSSL로 자체 서명 인증서 생성
- [ ] `docker-compose up -d` 실행
- [ ] `curl -k https://localhost/health` 테스트

### 스테이징 환경 (테스트 인증서)
- [ ] Let's Encrypt 테스트 인증서 발급
- [ ] DNS 레코드 확인
- [ ] Nginx 설정 업데이트
- [ ] certificate chain 검증

### 프로덕션 환경 (실제 인증서)
- [ ] Let's Encrypt 정식 인증서 발급
- [ ] HSTS 헤더 활성화
- [ ] 입증서 갱신 스크립트 설정
- [ ] SSL Labs A+ 등급 달성
- [ ] 보안 헤더 모두 설정
- [ ] 로그 모니터링 활성화

---

## 참고 자료

- [Let's Encrypt](https://letsencrypt.org)
- [Nginx SSL 문서](https://nginx.org/en/docs/http/ngx_http_ssl_module.html)
- [OWASP TLS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org)

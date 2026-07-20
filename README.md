# Tiny Second-hand Shopping Platform

WHS 시큐어 코딩 과제를 위한 작은 중고거래 플랫폼입니다. 회원·상품·채팅·신고/자동 제재·가상 잔액 송금·관리자 기능을 Flask로 구현하고, 보안 통제와 자동 테스트 및 재현 가능한 실행 환경을 함께 제공합니다.

## 주요 기능

- 회원가입, 로그인/로그아웃, 공개 프로필, 소개글·비밀번호 변경
- 상품 이미지 등록, 목록/상세/검색, 본인 상품 수정·소프트 삭제
- 3초 AJAX polling 기반 전체 채팅 및 1:1 채팅
- 사용자/상품 신고, 사유 저장, 중복 방지, 3회 누적 자동 휴면/차단
- 원 단위 가상 잔액 송금과 거래 내역
- 사용자·상품·신고 관리, 전체 거래와 관리자 감사 로그

## 기술 스택

- Python 3.12, Flask 3.1, Jinja, Bootstrap 5
- SQLite, SQLAlchemy 2
- Flask-Login, Flask-WTF/CSRF, Werkzeug scrypt, Pillow
- pytest, Gunicorn, Docker Compose

## 프로젝트 구조

```text
app/                  Flask 애플리케이션
  auth/               회원·프로필
  products/           상품·검색·이미지
  chat/               전체/1:1 채팅
  reports/            신고·자동 제재
  transfers/          가상 송금
  admin/              관리자 기능
  templates/ static/  화면과 정적 파일
tests/                pytest 자동 테스트
docs/                 요구사항·설계·추적표·체크리스트·보고서 원고
instance/             SQLite DB(커밋 제외)
uploads/              업로드 이미지(커밋 제외)
```

## 환경 설정

WSL Ubuntu 터미널에서 저장소 루트로 이동합니다. 실제 비밀값을 저장소에 커밋하지 마세요.

```bash
cp .env.example .env
python3 -c "import secrets; print(secrets.token_hex(32))"
```

출력된 무작위 문자열로 `.env`의 `SECRET_KEY`를 교체합니다. HTTPS 역방향 프록시 뒤에서 운영할 때는 `COOKIE_SECURE=true`로 바꿉니다.

## Docker 실행 방법

Docker Desktop의 WSL 2 통합을 켠 다음 실행합니다.

```bash
docker compose up --build
```

브라우저에서 <http://localhost:5000>으로 접속합니다. DB와 업로드는 Docker named volume에 유지됩니다.

샘플 계정과 데이터를 생성하려면 별도 터미널에서 다음을 실행합니다.

```bash
docker compose exec web flask --app run.py seed-demo
```

종료:

```bash
docker compose down
```

`docker compose down -v`는 DB와 업로드 volume까지 삭제하므로 초기화가 정말 필요할 때만 사용합니다.

## Docker 없이 실행

```bash
sudo apt update
sudo apt install -y python3 python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env의 SECRET_KEY를 무작위 값으로 교체
flask --app run.py init-db
flask --app run.py seed-demo   # 선택 사항
flask --app run.py run --debug
```

개발 서버는 로컬 개발에만 사용합니다. 제출 시 Docker는 Gunicorn 1 worker/4 threads로 실행해 SQLite의 다중 프로세스 쓰기 경합을 줄입니다.

## 데이터베이스 초기화

```bash
flask --app run.py init-db
```

기존 DB를 보존한 채 없는 테이블만 만듭니다. 완전 초기화는 서버를 중지하고 `instance/market.db`를 백업한 뒤 직접 제거하고 다시 실행합니다.

## 관리자 계정과 테스트 계정

`.env`의 `DEMO_PASSWORD`를 원하는 강한 임시 비밀번호로 설정한 뒤 다음 명령을 실행합니다.

```bash
flask --app run.py seed-demo
```

생성 계정:

| 아이디 | 역할 | 비밀번호 |
|---|---|---|
| `admin` | 관리자 | `DEMO_PASSWORD` 값 |
| `alice` | 일반 사용자 | `DEMO_PASSWORD` 값 |
| `bob` | 일반 사용자 | `DEMO_PASSWORD` 값 |

공개 배포에서는 샘플 계정을 만들지 않거나 즉시 비밀번호를 변경하세요.

## 테스트 실행

```bash
pytest -q
```

테스트는 임시 SQLite DB와 업로드 폴더를 사용하며 실제 개발 DB를 변경하지 않습니다. 기능/보안 수동 검증 항목은 [기능 체크리스트](docs/functional-checklist.md)와 [보안 체크리스트](docs/security-checklist.md)를 따릅니다.

## 구현한 보안 기능

- scrypt 기반 salted 비밀번호 해시와 최소 10자 검증
- SQLAlchemy ORM/바인딩 질의 및 DB FK/UNIQUE/CHECK 제약
- Jinja 자동 이스케이프와 polling 메시지의 `textContent` 삽입
- 모든 상태 변경 요청의 CSRF 토큰과 POST 사용
- 로그인, 활성 상태, 소유자, 관리자 권한의 서버 측 검사
- 2MB 제한, 이미지 디코딩/크기 검증, UUID 파일명, 재인코딩 저장
- 조건부 잔액 차감과 단일 commit을 통한 송금 원자성
- 중복 신고 DB 유일 제약, 자기 신고·자기 상품 신고 차단
- CSP, nosniff, frame 차단, referrer/permissions 정책, 안전한 쿠키 옵션
- 필수 `SECRET_KEY` 환경변수와 `.env`/DB/업로드 gitignore
- 내부 오류 내용을 노출하지 않는 공통 오류 화면과 관리자 감사 로그

## 요구사항 및 보고서 자료

- [요구사항 분석](docs/requirements.md)
- [시스템 설계](docs/architecture.md)
- [요구사항 추적표](docs/traceability.md)
- [보안 약점 수정 전후](docs/security-changes.md)
- [유지보수 기록](docs/maintenance-log.md)
- [최종 보고서 원고](docs/final-report-draft.md)

## 제한사항

- 실제 결제/은행 시스템이 아닌 학습용 가상 잔액입니다.
- SQLite와 단일 Gunicorn worker는 과제 규모에 맞춘 구성입니다. 대규모 운영은 PostgreSQL, migration, 분산 lock/격리 수준 검토가 필요합니다.
- polling은 WebSocket보다 지연과 요청 수가 많지만 구현 안정성을 우선했습니다.
- 인메모리 로그인 rate limit은 다중 인스턴스에 적합하지 않아 포함하지 않았습니다. 공개 인터넷 배포 시 역방향 프록시 또는 Redis 기반 rate limiting을 추가해야 합니다.
- 공개 GitHub URL과 실행 화면 캡처는 저장소 공개 후 보고서 원고의 표시 위치에 삽입해야 합니다.


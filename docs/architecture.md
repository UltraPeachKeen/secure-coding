# 시스템 설계

## 구조

브라우저가 Flask의 Blueprint 라우트에 요청하면 WTForms가 입력과 CSRF를 검증하고, 서비스/라우트가 권한과 업무 규칙을 확인한 뒤 SQLAlchemy가 SQLite에 접근한다. Jinja 템플릿은 출력 시 사용자 입력을 자동 이스케이프한다.

```text
Browser
  -> Flask (auth, products, chat, reports, transfers, admin)
      -> WTForms / Flask-Login / CSRFProtect
      -> SQLAlchemy transaction
          -> SQLite
      -> Jinja + Bootstrap
```

## 권한

| 작업 | 비회원 | 일반 | 휴면 | 관리자 |
|---|:---:|:---:|:---:|:---:|
| 상품 목록/상세, 프로필 조회 | O | O | O | O |
| 가입/로그인 | O | - | 로그인 거부 | - |
| 상품 작성, 채팅, 신고, 송금 | X | O | X | O |
| 본인 상품 수정/삭제 | X | O | X | O(관리 화면 별도) |
| 관리자 화면/상태 변경 | X | X | X | O |

## URL 초안

| 영역 | URL |
|---|---|
| 인증 | `/auth/register`, `/auth/login`, `/auth/logout` |
| 사용자 | `/users/<username>`, `/account`, `/account/profile`, `/account/password` |
| 상품 | `/`, `/products/new`, `/products/<id>`, `/products/<id>/edit`, `/products/<id>/delete`, `/products/mine` |
| 채팅 | `/chat/global`, `/chat/with/<username>`, `/chat/messages` |
| 신고 | `/reports/product/<id>`, `/reports/user/<id>` |
| 송금 | `/transfers`, `/transfers/send` |
| 관리자 | `/admin`, `/admin/users`, `/admin/products`, `/admin/reports`, `/admin/transfers`, `/admin/audit-logs` |

## 데이터베이스

- `users 1:N products`
- `users 1:N chat_messages`(sender), `users 0:N chat_messages`(receiver)
- `users 1:N reports`(reporter), 신고 대상은 정확히 user 또는 product 하나
- `users 1:N transfers`(sender/receiver)
- 관리 작업은 `audit_logs`에 남긴다.

무결성은 FK/UNIQUE/CHECK와 애플리케이션 검사를 중복 적용한다. SQLite 연결마다 foreign key pragma를 활성화한다.

## 폴더 구조

```text
app/
  __init__.py config.py extensions.py models.py forms.py security.py
  auth/ products/ chat/ reports/ transfers/ admin/
  templates/ static/
tests/
docs/
instance/ uploads/
```


# 개발 중 확인한 보안 약점과 수정 전후

## 1. 평문 비밀번호

- 위험한 형태: 입력 비밀번호를 문자열 컬럼에 그대로 저장.
- 수정: `User.set_password()`에서 Werkzeug scrypt 해시를 저장하고 `check_password_hash` 계열로만 검증.
- 검증: DB 값이 원문과 다르고 정상 비밀번호만 통과하는 pytest.

## 2. 문자열 결합 SQL

- 위험한 형태: 검색어를 f-string SQL에 삽입.
- 수정: SQLAlchemy 표현식과 바인딩을 사용하고 LIKE의 `%`, `_`, `\\`도 escape.
- 검증: SQL Injection 형태 검색어가 오류나 전체 노출을 만들지 않음.

## 3. 저장형/DOM XSS

- 위험한 형태: 상품·채팅 본문을 `safe` 또는 `innerHTML`로 출력.
- 수정: Jinja 자동 이스케이프 유지, polling은 DOM `textContent` 사용, CSP 적용.
- 검증: 스크립트/이벤트 입력이 이스케이프된 문자열로 표시됨.

## 4. CSRF와 GET 상태 변경

- 위험한 형태: 삭제·송금·관리 기능을 링크/토큰 없는 POST로 처리.
- 수정: Flask-WTF 전역 CSRF, 모든 상태 변경 POST, 폼별 토큰.
- 검증: 토큰 없는 가입 요청이 400.

## 5. IDOR/관리자 권한 우회

- 위험한 형태: 화면에서 버튼만 숨기고 URL ID를 신뢰.
- 수정: 상품 수정·삭제 시 `seller_id == current_user.id`, 관리 라우트는 `admin_required`를 서버에서 검사.
- 검증: 타인 상품과 일반 사용자의 `/admin`이 403.

## 6. 위험한 파일 업로드

- 위험한 형태: 원본 파일명/확장자만 확인해 업로드 폴더에 저장.
- 수정: 요청 2MB 제한, 원본 확장자 허용 목록, Pillow 실제 디코딩, 허용 포맷·5000px 제한, UUID명, 이미지 재인코딩.
- 검증: PNG 이름의 비이미지 파일 거부.

## 7. 송금 금액 변조와 부분 반영

- 위험한 형태: 브라우저 잔액을 신뢰하거나 차감/증가/기록을 따로 commit.
- 수정: 정수 범위·대상·상태 검사, `balance >= amount` 조건부 UPDATE, 증가와 이력까지 한 commit, 예외 rollback.
- 검증: 정상 송금은 양쪽과 이력이 함께 변경되고 비정상 송금은 모두 불변.

## 8. 중복 신고 경쟁 조건

- 위험한 형태: 사전 조회만으로 중복 검사.
- 수정: 대상별 `(reporter_id, target_id)` UNIQUE 제약과 `IntegrityError` rollback을 함께 사용.
- 검증: 반복 요청 후 신고 한 건만 존재.

## 9. 비밀키의 저장소 노출

- 위험한 형태: 코드에 고정된 기본 `SECRET_KEY`.
- 수정: 비테스트 실행은 `SECRET_KEY` 없으면 즉시 실패, `.env.example`만 제공, `.env` gitignore.
- 검증: 민감 파일 추적 여부 최종 scan.

## 10. 과도한 오류·브라우저 권한

- 위험한 형태: stack trace 노출, iframe 삽입, MIME sniffing 허용.
- 수정: 일반 오류 화면, rollback, CSP/nosniff/frame/referrer/permissions 헤더, HttpOnly/SameSite 쿠키.
- 검증: 헤더 자동 테스트와 잘못된 ID 수동 점검.

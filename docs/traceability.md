# 요구사항 추적표

| 요구 ID | 설계/구현 위치 | 검증 |
|---|---|---|
| FR-01, SR-01 | `app/auth`, `User.set_password` | `test_auth.py` |
| FR-02 | `app/auth` account/profile routes | `test_auth.py` |
| FR-03, SR-05~07 | `app/products`, upload validator | `test_products.py` |
| FR-04~05 | product index/detail/mine/search | `test_products.py` |
| FR-06, SR-03~05 | `app/chat` polling endpoints | `test_chat.py` |
| FR-07~08, SR-09~10 | `app/reports`, DB unique constraints | `test_reports.py` |
| FR-09, SR-08 | `app/transfers` conditional update | `test_transfers.py` |
| FR-10, SR-05 | `app/admin`, `admin_required` | `test_admin.py` |
| FR-11, NFR-01 | `flask seed-demo`, README | CLI smoke test |
| SR-02~04, SR-11~12 | ORM, CSRF, config, headers | `test_security.py`, repository scan |


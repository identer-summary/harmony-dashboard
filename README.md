# Harmony Watcher Dashboard

공동주택 층간소음의 소음·진동 데이터를 확인하고, 이상 패턴을 검토한 뒤 관리 조치를 결정하기 위한 관제 화면입니다.

## 로컬 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 dashboard.py
```

브라우저에서 `http://127.0.0.1:5001`을 엽니다.

## Render 설정

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn dashboard:app`
- Health Check Path: `/health`
- 권장 환경 변수: `DEMO_MODE=true` (검토 완료 후 실제 데이터 연결 시 `false`)

## 현재 범위

- 기존 `/api/report`, `/api/data`, `/` 경로 유지
- Render 시작 명령 유지
- 센서 미연결 세대는 화면에서 `예시값`으로 구분
- 안내문 승인은 데모 동작이며 실제 메시지를 발송하지 않음
- 데이터는 현재 메모리에 보관되므로 서비스 재시작 시 초기화됨

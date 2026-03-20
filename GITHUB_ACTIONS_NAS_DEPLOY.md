# GitHub Actions로 Synology NAS 자동 배포

## 1) NAS SSH 키 준비

NAS에서 배포용 SSH 키를 생성합니다.

```bash
ssh-keygen -t ed25519 -C "family-news-deploy" -f ~/.ssh/family_news_deploy
cat ~/.ssh/family_news_deploy.pub >> ~/.ssh/authorized_keys
```

- 개인키: `~/.ssh/family_news_deploy`
- 공개키: `~/.ssh/family_news_deploy.pub`

## 2) GitHub Repository Secrets 설정

GitHub 저장소 `Settings > Secrets and variables > Actions > New repository secret`에 아래를 추가합니다.

- `NAS_HOST`: 예) `jakesto.synology.me`
- `NAS_PORT`: 예) `22`
- `NAS_USER`: 예) `root` 또는 배포 사용자
- `NAS_SSH_KEY`: `family_news_deploy` 개인키 전체 내용
- `NAS_APP_DIR`: `/volume1/web/family_news/app` (선택, 미설정 시 기본값으로 사용)

## 3) NAS 사전 준비

- `/volume1/web/family_news/app` 경로에 저장소가 존재해야 함
- `.env` 파일이 준비되어 있어야 함
- Docker / Container Manager 사용 가능 상태

## 4) 동작 방식

`main` 브랜치에 push되면 자동 실행:

1. NAS SSH 접속
2. `git fetch origin main`
3. `git reset --hard origin/main`
4. `docker compose -f docker-compose.nas.yml up -d --build`
5. 상태 확인 `docker compose -f docker-compose.nas.yml ps`

## 5) 수동 실행

GitHub `Actions` 탭에서 `Deploy to Synology NAS` 워크플로를 수동 실행할 수 있습니다.

## 6) PowerShell로 배포 상태 폴링 + 실패 로그 자동 저장

VS Code에서 `gh run watch`가 화면 갱신 때문에 멈춘 것처럼 보일 때, 아래 스크립트를 사용하세요.

```powershell
# 최신 deploy-nas 실행 자동 추적
powershell -ExecutionPolicy Bypass -File .\scripts\watch_nas_deploy.ps1

# 특정 RunId 추적
powershell -ExecutionPolicy Bypass -File .\scripts\watch_nas_deploy.ps1 -RunId 23363304377

# 폴링/타임아웃 조정
powershell -ExecutionPolicy Bypass -File .\scripts\watch_nas_deploy.ps1 -IntervalSeconds 5 -TimeoutMinutes 30

# 실패 로그 패턴 요약(502/504/Health check/fatal 등)
powershell -ExecutionPolicy Bypass -File .\scripts\watch_nas_deploy.ps1 -SummarizeFailedLog
```

실패 시 아래 경로에 로그를 자동 저장합니다.

- `logs/deploy/run_<RunId>_failed_<timestamp>.log`
- `logs/deploy/run_<RunId>_full_<timestamp>.log`

## 7) VS Code Task로 원클릭 실행

- `Terminal > Run Task...`에서 아래를 선택해 실행
- `NAS Deploy: Watch Latest`
- `NAS Deploy: Watch by RunId`

관련 설정 파일:

- `.vscode/tasks.json`

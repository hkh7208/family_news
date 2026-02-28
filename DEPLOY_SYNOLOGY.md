# Synology NAS 배포 가이드

## 1) 폴더 구조 준비
NAS SSH에서 아래처럼 준비합니다.

```bash
mkdir -p /volume1/web/family_news/{app,media,staticfiles,deploy}
cd /volume1/web/family_news/app
git clone https://github.com/hkh7208/family_news.git .
```

## 2) 환경파일 준비
`/volume1/web/family_news/app/.env` 생성 후 `.env.nas.example` 내용을 기반으로 값 수정:

- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `NAS_DB_*`
- `DB_TARGET=nas`

중요:

- `DB_TARGET=nas`
- `NAS_DB_HOST`는 NAS의 LAN IP(예: `192.168.0.250`)를 사용
- `NAS_DB_PORT`는 Synology MariaDB 포트(기본 `3306`)로 설정

## 3) nginx 설정 파일
별도 복사 작업이 필요 없습니다. 레포 안의 파일을 그대로 사용합니다.

- 파일 위치: `/volume1/web/family_news/app/deploy/nginx.nas.conf`

## 4) 컨테이너 실행
```bash
cd /volume1/web/family_news/app
docker compose -f docker-compose.nas.yml up -d --build
```

## 5) 상태 확인
```bash
docker compose -f docker-compose.nas.yml ps
docker compose -f docker-compose.nas.yml logs -f web
```

## 6) 접속
- `http://jakesto.snology.me:8090`

## 참고
- 동영상 압축용 `ffmpeg`는 `web` 이미지에 포함됩니다.
- 정적 파일은 `staticfiles`, 업로드 파일은 `media` 볼륨에 영구 저장됩니다.

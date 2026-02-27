# MariaDB 설정 가이드 (로컬 ↔ NAS 전환)

## 1) 로컬 PC MariaDB 초기화

```powershell
mysql -u root -p < scripts/mariadb_init_local.sql
```

## 2) Synology NAS MariaDB 초기화

NAS MariaDB에서 아래 SQL 실행:

```sql
SOURCE /path/to/mariadb_init_nas.sql;
```

또는 파일 내용을 그대로 복사해서 실행합니다.

## 3) `.env` 값 맞추기

`LOCAL_DB_PASSWORD`, `NAS_DB_PASSWORD`를 실제 비밀번호로 변경하세요.

예시:

```dotenv
DB_TARGET=local
LOCAL_DB_HOST=127.0.0.1
LOCAL_DB_PORT=3306

NAS_DB_HOST=192.168.0.200
NAS_DB_PORT=3307
```

## 4) DB 대상 전환

- 로컬 MariaDB 사용: `DB_TARGET=local`
- NAS MariaDB 사용: `DB_TARGET=nas`

## 5) 마이그레이션 적용

```powershell
python manage.py migrate --settings=config.settings.local
```

## 6) 서버 실행

```powershell
python manage.py runserver --settings=config.settings.local
```

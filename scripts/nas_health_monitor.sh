#!/bin/bash
# NAS 헬스체크 및 자동재시작 스크립트
# Synology DSM 작업 스케줄러에 등록하여 5분마다 실행 권장
#
# 설치 방법:
#   1. NAS에 이 파일을 /volume1/web/family_news/scripts/nas_health_monitor.sh 로 복사
#   2. chmod +x /volume1/web/family_news/scripts/nas_health_monitor.sh
#   3. DSM > 제어판 > 작업 스케줄러 > 생성 > 예약된 작업 > 사용자 정의 스크립트
#      - 사용자: root
#      - 일정: 5분마다
#      - 스크립트: bash /volume1/web/family_news/scripts/nas_health_monitor.sh

set -euo pipefail

COMPOSE_DIR="/volume1/web/family_news/app"
LOG_FILE="/volume1/web/family_news/logs/health_monitor.log"
HEALTH_URL="http://localhost:8090/health/"
MAX_LOG_LINES=500

mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# 로그 파일 크기 제한 (최근 500줄만 유지)
if [ -f "$LOG_FILE" ]; then
    tail -n $MAX_LOG_LINES "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
fi

# HTTP 헬스체크
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "$HEALTH_URL" 2>/dev/null || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    # 정상 - 조용히 종료 (정상 로그는 매 시간 정각에만 기록)
    MINUTE=$(date '+%M')
    if [ "$MINUTE" = "00" ]; then
        log "INFO  healthy (HTTP 200)"
    fi
    exit 0
fi

log "WARN  health check failed (HTTP $HTTP_STATUS) - attempting recovery"

# Docker Compose로 재시작 시도
if [ -f "$COMPOSE_DIR/docker-compose.nas.yml" ]; then
    cd "$COMPOSE_DIR"

    # 컨테이너 상태 기록
    log "INFO  container status before restart:"
    docker ps -a --filter "name=family_news" --format "  {{.Names}}: {{.Status}}" >> "$LOG_FILE" 2>&1 || true

    # web 컨테이너가 exited 상태인지 확인
    WEB_STATUS=$(docker inspect --format='{{.State.Status}}' family_news_web 2>/dev/null || echo "missing")
    NGINX_STATUS=$(docker inspect --format='{{.State.Status}}' family_news_nginx 2>/dev/null || echo "missing")

    log "INFO  web=$WEB_STATUS nginx=$NGINX_STATUS"

    if [ "$WEB_STATUS" = "missing" ] || [ "$NGINX_STATUS" = "missing" ]; then
        log "ACTION containers not found - running docker-compose up"
        docker-compose -f docker-compose.nas.yml up -d >> "$LOG_FILE" 2>&1
    else
        log "ACTION restarting unhealthy containers"
        docker-compose -f docker-compose.nas.yml restart >> "$LOG_FILE" 2>&1
    fi

    # 재시작 후 30초 대기 후 재확인
    sleep 30
    HTTP_STATUS_AFTER=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "$HEALTH_URL" 2>/dev/null || echo "000")
    if [ "$HTTP_STATUS_AFTER" = "200" ]; then
        log "INFO  recovery successful (HTTP 200)"
    else
        log "ERROR recovery failed (HTTP $HTTP_STATUS_AFTER) - manual intervention may be required"
        # 전체 스택 재시작 시도
        log "ACTION attempting full stack restart (down + up)"
        docker-compose -f docker-compose.nas.yml down >> "$LOG_FILE" 2>&1 || true
        sleep 5
        docker-compose -f docker-compose.nas.yml up -d >> "$LOG_FILE" 2>&1 || true
    fi
else
    log "ERROR docker-compose.nas.yml not found at $COMPOSE_DIR"
fi

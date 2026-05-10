# NAS 서버 재시작 스크립트
# 목적: Docker 컨테이너 재시작 및 서비스 상태 확인

param(
    [string]$NasHost = "192.168.0.250",
    [string]$NasUser = "admin"
)

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "NAS 동영상 업로드 서비스 재시작" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

$sshCmd = @"
cd /volume1/web/family_news && \
docker-compose -f docker-compose.nas.yml down && \
sleep 3 && \
docker-compose -f docker-compose.nas.yml up -d && \
sleep 5 && \
docker-compose -f docker-compose.nas.yml ps
"@

Write-Host "`n[1/3] NAS SSH 연결 중..." -ForegroundColor Green
ssh -o ConnectTimeout=10 $NasUser@$NasHost $sshCmd

Write-Host "`n[2/3] 서비스 헬스체크 중 (10초 대기)..." -ForegroundColor Green
Start-Sleep -Seconds 10

$healthCmd = @"
curl -s http://localhost:8090/health-check/ | head -20
"@

Write-Host "`n[3/3] 헬스체크 결과:" -ForegroundColor Green
ssh -o ConnectTimeout=10 $NasUser@$NasHost $healthCmd

Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✓ NAS 서버 재시작 완료" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

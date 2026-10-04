#!/bin/bash

# cron은 /etc/profile.d를 읽지 않으므로 기본값을 직접 지정
AGENT_HOME="${AGENT_HOME:-/home/agent-admin/agent-app}"
AGENT_PORT="${AGENT_PORT:-15034}"
AGENT_LOG_DIR="${AGENT_LOG_DIR:-/var/log/agent-app}"
LOG_FILE="$AGENT_LOG_DIR/monitor.log"
APP_NAME="agent-app-linux-x86"

CPU_LIMIT=20
MEM_LIMIT=10
DISK_LIMIT=80

MAX_SIZE=$((10 * 1024 * 1024))  # 10MB
MAX_FILES=10

PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# 숫자 비교 함수: over 값 기준 → 값 > 기준이면 참 (소수 비교는 bash로 안 돼서 awk 사용)
over() {
    awk -v v="$1" -v l="$2" 'BEGIN { exit !(v > l) }'
}

echo "===== Agent Monitor $(date '+%Y-%m-%d %H:%M:%S') ====="

PID=$(pgrep -f "$APP_NAME" | head -n1)
if [ -z "$PID" ]; then
    echo "[ERROR] Process '$APP_NAME' is not running"
    exit 1
fi
echo "[OK] Process '$APP_NAME' running (PID: $PID)"

if ! ss -tln "sport = :$AGENT_PORT" | grep -q LISTEN; then
    echo "[ERROR] Port $AGENT_PORT is not LISTENING"
    exit 1
fi
echo "[OK] Port $AGENT_PORT is LISTENING"

if grep -q '^ENABLED=yes' /etc/ufw/ufw.conf 2>/dev/null; then
    echo "[OK] Firewall (UFW) is active"
else
    echo "[WARNING] Firewall (UFW) is inactive"
fi

# CPU: /proc/stat을 1초 간격으로 두 번 읽어서 그 사이 사용률 계산
read -r _ u1 n1 s1 i1 w1 q1 sq1 st1 _ < /proc/stat
sleep 1
read -r _ u2 n2 s2 i2 w2 q2 sq2 st2 _ < /proc/stat
TOTAL=$(( (u2+n2+s2+i2+w2+q2+sq2+st2) - (u1+n1+s1+i1+w1+q1+sq1+st1) ))
IDLE=$(( (i2+w2) - (i1+w1) ))
CPU=$(awk -v t="$TOTAL" -v i="$IDLE" 'BEGIN { if (t > 0) printf "%.1f", (t - i) * 100 / t; else print "0.0" }')

# MEM: 사용량 / 전체
MEM=$(free | awk '/^Mem:/ { printf "%.1f", $3 / $2 * 100 }')

# DISK: 루트(/) 파티션 사용률
DISK=$(df -P / | awk 'NR==2 { gsub("%", "", $5); print $5 }')

echo "[INFO] CPU: ${CPU}%  MEM: ${MEM}%  DISK_USED: ${DISK}%"

over "$CPU"  "$CPU_LIMIT"  && echo "[WARNING] CPU usage ${CPU}% > ${CPU_LIMIT}%"
over "$MEM"  "$MEM_LIMIT"  && echo "[WARNING] Memory usage ${MEM}% > ${MEM_LIMIT}%"
over "$DISK" "$DISK_LIMIT" && echo "[WARNING] Disk usage ${DISK}% > ${DISK_LIMIT}%"

rotate_log() {
    [ -f "$LOG_FILE" ] || return 0
    local size
    size=$(stat -c %s "$LOG_FILE")
    [ "$size" -lt "$MAX_SIZE" ] && return 0

    rm -f "$LOG_FILE.$((MAX_FILES - 1))"
    for ((i = MAX_FILES - 2; i >= 1; i--)); do
        [ -f "$LOG_FILE.$i" ] && mv "$LOG_FILE.$i" "$LOG_FILE.$((i + 1))"
    done
    mv "$LOG_FILE" "$LOG_FILE.1"
    echo "[INFO] monitor.log rotated (size: $size bytes)"
}

if [ ! -w "$AGENT_LOG_DIR" ]; then
    echo "[ERROR] Cannot write to $AGENT_LOG_DIR"
    exit 1
fi
rotate_log

echo "[$(date '+%Y-%m-%d %H:%M:%S')] PID:$PID CPU:${CPU}% MEM:${MEM}% DISK_USED:${DISK}%" >> "$LOG_FILE"
echo "[OK] Logged to $LOG_FILE"

exit 0
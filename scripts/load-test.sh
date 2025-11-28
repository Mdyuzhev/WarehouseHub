#!/bin/bash
# =============================================================================
# Load Test Script for Warehouse API
# Потому что иногда нужно проверить, выдержит ли API толпу голодных пользователей
# =============================================================================

set -e

# Конфигурация (можно переопределить через переменные окружения)
LOCUST_HOST="${LOCUST_HOST:-http://192.168.1.74:30089}"
TARGET_HOST="${TARGET_HOST:-http://warehouse-api-service.warehouse.svc.cluster.local:8080}"
USERS="${USERS:-100}"
SPAWN_RATE="${SPAWN_RATE:-10}"
DURATION="${DURATION:-900}"  # 15 минут в секундах

echo "=============================================="
echo "   Load Test для Warehouse API"
echo "   Приготовьтесь, сейчас будет жарко!"
echo "=============================================="
echo ""
echo "Параметры теста:"
echo "  - Locust Master: $LOCUST_HOST"
echo "  - Target API: $TARGET_HOST"
echo "  - Пользователей: $USERS"
echo "  - Spawn rate: $SPAWN_RATE users/sec"
echo "  - Длительность: $((DURATION / 60)) минут"
echo ""

# Проверка доступности Locust
echo "[1/5] Проверка доступности Locust..."
if ! curl -sf "$LOCUST_HOST" > /dev/null 2>&1; then
    echo "ОШИБКА: Locust недоступен на $LOCUST_HOST"
    echo "Может он ушёл на обед?"
    exit 1
fi
echo "OK - Locust на месте и готов к труду!"

# Остановка предыдущего теста (если был)
echo ""
echo "[2/5] Остановка предыдущего теста..."
curl -sf "$LOCUST_HOST/stop" > /dev/null 2>&1 || true
sleep 2

# Сброс статистики
echo "[3/5] Сброс статистики (начинаем с чистого листа)..."
curl -sf "$LOCUST_HOST/stats/reset" > /dev/null 2>&1 || true
sleep 1

# Запуск теста
echo ""
echo "[4/5] Запуск нагрузочного теста..."
echo "      Поехали! Держитесь крепче!"
RESPONSE=$(curl -sf -X POST "$LOCUST_HOST/swarm" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "user_count=$USERS&spawn_rate=$SPAWN_RATE&host=$TARGET_HOST")

if echo "$RESPONSE" | grep -q '"success": true'; then
    echo "OK - Тест запущен успешно!"
else
    echo "ОШИБКА: Не удалось запустить тест"
    echo "Ответ: $RESPONSE"
    exit 1
fi

# Ожидание выполнения теста
echo ""
echo "[5/5] Ожидание завершения теста..."
echo "      Время на кофе: $((DURATION / 60)) минут"
echo ""

START_TIME=$(date +%s)
END_TIME=$((START_TIME + DURATION))

while [ $(date +%s) -lt $END_TIME ]; do
    ELAPSED=$(($(date +%s) - START_TIME))
    REMAINING=$((END_TIME - $(date +%s)))

    # Получаем текущую статистику
    STATS=$(curl -sf "$LOCUST_HOST/stats/requests" 2>/dev/null || echo '{}')
    CURRENT_USERS=$(echo "$STATS" | jq -r '.user_count // 0')
    CURRENT_RPS=$(echo "$STATS" | jq -r '.total_rps // 0' | cut -d. -f1)
    FAIL_RATIO=$(echo "$STATS" | jq -r '.fail_ratio // 0')
    TOTAL_REQUESTS=$(echo "$STATS" | jq -r '.stats[] | select(.name == "Aggregated") | .num_requests // 0' 2>/dev/null || echo "0")

    # Красивый вывод прогресса
    printf "\r  [%3d/%3d мин] Users: %3d | RPS: %4d | Requests: %6s | Errors: %.1f%%   " \
        $((ELAPSED / 60)) $((DURATION / 60)) "$CURRENT_USERS" "$CURRENT_RPS" "$TOTAL_REQUESTS" "$(echo "$FAIL_RATIO * 100" | bc -l 2>/dev/null || echo 0)"

    sleep 10
done

echo ""
echo ""

# Остановка теста
echo "Останавливаем тест..."
curl -sf "$LOCUST_HOST/stop" > /dev/null 2>&1 || true
sleep 3

# Получение финальной статистики
echo ""
echo "=============================================="
echo "   РЕЗУЛЬТАТЫ НАГРУЗОЧНОГО ТЕСТА"
echo "=============================================="

FINAL_STATS=$(curl -sf "$LOCUST_HOST/stats/requests")

# Общая статистика
echo ""
echo "=== ОБЩАЯ СТАТИСТИКА ==="
echo "$FINAL_STATS" | jq -r '
    .stats[] | select(.name == "Aggregated") |
    "Всего запросов:      \(.num_requests)
Ошибок:              \(.num_failures) (\(if .num_requests > 0 then ((.num_failures / .num_requests * 100) | floor) else 0 end)%)
Среднее время:       \(.avg_response_time | floor) ms
Медиана:             \(.median_response_time // "N/A") ms
Мин. время:          \(.min_response_time | floor) ms
Макс. время:         \(.max_response_time | floor) ms"'

echo ""
echo "=== СТАТИСТИКА ПО ЭНДПОИНТАМ ==="
echo "$FINAL_STATS" | jq -r '
    .stats[] | select(.name != "Aggregated") |
    "\(.method) \(.name):
    Запросов: \(.num_requests), Ошибок: \(.num_failures), Avg: \(.avg_response_time | floor)ms, Max: \(.max_response_time | floor)ms"'

# Проверка на ошибки
ERRORS=$(echo "$FINAL_STATS" | jq '.errors | length')
if [ "$ERRORS" -gt 0 ]; then
    echo ""
    echo "=== ОШИБКИ ==="
    echo "$FINAL_STATS" | jq -r '.errors[] | "[\(.method)] \(.name): \(.occurrences)x - \(.error)"'
fi

# Вердикт
echo ""
echo "=============================================="
FAIL_RATIO=$(echo "$FINAL_STATS" | jq -r '.fail_ratio // 0')
FAIL_PERCENT=$(echo "$FAIL_RATIO * 100" | bc -l 2>/dev/null | cut -d. -f1 || echo "0")

if [ "${FAIL_PERCENT:-0}" -lt 1 ]; then
    echo "   ВЕРДИКТ: PASSED"
    echo "   API выдержал нагрузку как чемпион!"
    EXIT_CODE=0
elif [ "${FAIL_PERCENT:-0}" -lt 5 ]; then
    echo "   ВЕРДИКТ: WARNING"
    echo "   API немного вспотел, но справился"
    EXIT_CODE=0
else
    echo "   ВЕРДИКТ: FAILED"
    echo "   API не выдержал... Нужна оптимизация!"
    EXIT_CODE=1
fi
echo "=============================================="

# Сохраняем результаты в файл для артефактов
mkdir -p target/load-test-results
echo "$FINAL_STATS" > target/load-test-results/stats.json
echo "$FINAL_STATS" | jq -r '
    "# Load Test Results\n" +
    "## Summary\n" +
    "- Total Requests: \(.stats[] | select(.name == "Aggregated") | .num_requests)\n" +
    "- Failed Requests: \(.stats[] | select(.name == "Aggregated") | .num_failures)\n" +
    "- Avg Response Time: \(.stats[] | select(.name == "Aggregated") | .avg_response_time | floor)ms\n" +
    "- Max Response Time: \(.stats[] | select(.name == "Aggregated") | .max_response_time | floor)ms\n"
' > target/load-test-results/summary.md

exit $EXIT_CODE

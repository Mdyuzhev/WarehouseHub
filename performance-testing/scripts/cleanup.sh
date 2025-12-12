#!/bin/bash
#
# cleanup.sh - Очистка стенда перед/после нагрузочного тестирования
# WH-103: A/B нагрузочное тестирование Redis + Kafka
#

set -e

NAMESPACE="warehouse"
LOADTEST_NS="loadtest"

echo "=========================================="
echo "  ОЧИСТКА СТЕНДА"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# 1. Остановка Locust (сброс текущей нагрузки)
echo ""
echo "[1/5] Сброс Locust..."
LOCUST_MASTER=$(kubectl get pods -n $LOADTEST_NS -l app=locust,component=master -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -n "$LOCUST_MASTER" ]; then
    # Отправка команды stop через API
    kubectl exec -n $LOADTEST_NS $LOCUST_MASTER -- curl -s -X GET "http://localhost:8089/stop" > /dev/null 2>&1 || true
    echo "  ✓ Locust остановлен"
else
    echo "  ⚠ Locust master не найден"
fi

# 2. Очистка кэша Redis
echo ""
echo "[2/5] Очистка Redis кэша..."
REDIS_POD=$(kubectl get pods -n $NAMESPACE -l app=redis -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -n "$REDIS_POD" ]; then
    kubectl exec -n $NAMESPACE $REDIS_POD -- redis-cli FLUSHALL > /dev/null 2>&1 || true
    echo "  ✓ Redis кэш очищен (FLUSHALL)"
else
    echo "  ⚠ Redis pod не найден"
fi

# 3. Рестарт API для сброса состояния (опционально)
echo ""
echo "[3/5] Рестарт warehouse-api..."
kubectl rollout restart deployment/warehouse-api -n $NAMESPACE
kubectl rollout status deployment/warehouse-api -n $NAMESPACE --timeout=120s
echo "  ✓ warehouse-api перезапущен"

# 4. Очистка завершённых Locust pods
echo ""
echo "[4/5] Удаление завершённых pods..."
kubectl delete pods -n $LOADTEST_NS --field-selector=status.phase=Succeeded 2>/dev/null || true
kubectl delete pods -n $LOADTEST_NS --field-selector=status.phase=Failed 2>/dev/null || true
echo "  ✓ Завершённые pods удалены"

# 5. Проверка состояния стенда
echo ""
echo "[5/5] Проверка состояния..."
echo ""
echo "=== warehouse namespace ==="
kubectl get pods -n $NAMESPACE -o wide
echo ""
echo "=== loadtest namespace ==="
kubectl get pods -n $LOADTEST_NS -o wide

# Проверка health API
echo ""
echo "=== API Health Check ==="
API_URL="https://api.wh-lab.ru"
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/actuator/health" --connect-timeout 5 || echo "000")
if [ "$HEALTH" = "200" ]; then
    echo "  ✓ API healthy (HTTP 200)"
else
    echo "  ⚠ API вернул HTTP $HEALTH"
fi

echo ""
echo "=========================================="
echo "  ОЧИСТКА ЗАВЕРШЕНА"
echo "=========================================="

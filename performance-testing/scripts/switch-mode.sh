#!/bin/bash
#
# switch-mode.sh - Переключение режимов Redis/Kafka для A/B тестирования
# WH-103: A/B нагрузочное тестирование Redis + Kafka
#
# Использование:
#   ./switch-mode.sh baseline  - Отключить Redis и Kafka
#   ./switch-mode.sh optimized - Включить Redis и Kafka
#   ./switch-mode.sh status    - Показать текущий режим
#

set -e

NAMESPACE="warehouse"
DEPLOYMENT="warehouse-api"

usage() {
    echo "Использование: $0 {baseline|optimized|status}"
    echo ""
    echo "  baseline  - Режим без Redis/Kafka (spring.cache.type=none)"
    echo "  optimized - Режим с Redis/Kafka (spring.cache.type=redis)"
    echo "  status    - Показать текущие настройки"
    exit 1
}

show_status() {
    echo "=========================================="
    echo "  ТЕКУЩИЙ РЕЖИМ API"
    echo "=========================================="
    echo ""
    echo "Переменные окружения warehouse-api:"
    kubectl get deployment $DEPLOYMENT -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].env[*]}' | tr ',' '\n' | grep -E "SPRING_CACHE|KAFKA" || echo "  (не заданы)"
    echo ""
    echo "Проверка /actuator/health:"
    curl -s "https://api.wh-lab.ru/actuator/health" | jq -r '.components | to_entries[] | "\(.key): \(.value.status)"' 2>/dev/null || echo "  ⚠ Не удалось получить health"
}

switch_baseline() {
    echo "=========================================="
    echo "  ПЕРЕКЛЮЧЕНИЕ В РЕЖИМ BASELINE"
    echo "  (без Redis кэширования, без Kafka)"
    echo "=========================================="
    echo ""

    # Отключаем Redis кэширование
    echo "[1/3] Отключаю Redis кэширование..."
    kubectl set env deployment/$DEPLOYMENT -n $NAMESPACE SPRING_CACHE_TYPE=none

    # Убираем Kafka bootstrap servers
    echo "[2/3] Отключаю Kafka..."
    kubectl set env deployment/$DEPLOYMENT -n $NAMESPACE SPRING_KAFKA_BOOTSTRAP_SERVERS-

    # Ждём rollout
    echo "[3/3] Ожидаю перезапуск API..."
    kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=120s

    echo ""
    echo "  ✓ Режим BASELINE активирован"
    echo "  - Redis кэширование: ОТКЛЮЧЕНО"
    echo "  - Kafka: ОТКЛЮЧЕНА"

    # Проверка
    echo ""
    show_status
}

switch_optimized() {
    echo "=========================================="
    echo "  ПЕРЕКЛЮЧЕНИЕ В РЕЖИМ OPTIMIZED"
    echo "  (Redis кэширование + Kafka)"
    echo "=========================================="
    echo ""

    # Включаем Redis кэширование
    echo "[1/3] Включаю Redis кэширование..."
    kubectl set env deployment/$DEPLOYMENT -n $NAMESPACE SPRING_CACHE_TYPE=redis

    # Включаем Kafka
    echo "[2/3] Включаю Kafka..."
    kubectl set env deployment/$DEPLOYMENT -n $NAMESPACE SPRING_KAFKA_BOOTSTRAP_SERVERS=kafka:9092

    # Ждём rollout
    echo "[3/3] Ожидаю перезапуск API..."
    kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=120s

    echo ""
    echo "  ✓ Режим OPTIMIZED активирован"
    echo "  - Redis кэширование: ВКЛЮЧЕНО"
    echo "  - Kafka: ВКЛЮЧЕНА"

    # Проверка
    echo ""
    show_status
}

# Main
case "${1:-}" in
    baseline)
        switch_baseline
        ;;
    optimized)
        switch_optimized
        ;;
    status)
        show_status
        ;;
    *)
        usage
        ;;
esac

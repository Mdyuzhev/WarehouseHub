#!/bin/bash
# Скрипт для тестирования GitLab webhook локально
# Отправляет тестовые payload на endpoint бота

BOT_URL="${BOT_URL:-http://localhost:8000}"
WEBHOOK_ENDPOINT="${BOT_URL}/webhook/gitlab"

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 GitLab Webhook Tester"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Endpoint: ${WEBHOOK_ENDPOINT}"
echo ""

# Функция для отправки payload
send_payload() {
    local name=$1
    local file=$2

    echo -n "📨 Отправляем: ${name}... "

    response=$(curl -s -w "\n%{http_code}" -X POST "${WEBHOOK_ENDPOINT}" \
        -H "Content-Type: application/json" \
        -d "@${file}")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✅ OK${NC} (HTTP ${http_code})"
        echo "   Response: ${body}"
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP ${http_code})"
        echo "   Response: ${body}"
    fi
    echo ""
}

# Проверяем что бот запущен
echo "🔍 Проверяем доступность бота..."
if curl -s "${BOT_URL}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Бот доступен${NC}"
    echo ""
else
    echo -e "${RED}❌ Бот недоступен на ${BOT_URL}${NC}"
    echo "   Убедись что бот запущен или укажи правильный URL:"
    echo "   export BOT_URL=http://your-bot-url:8000"
    echo ""
    exit 1
fi

# Меню выбора
echo "Выбери тест:"
echo "  1) Pipeline Success"
echo "  2) Pipeline Failed"
echo "  3) Job Success"
echo "  4) Job Failed"
echo "  5) Все тесты"
echo "  q) Выход"
echo ""
read -p "Твой выбор: " choice

case $choice in
    1)
        send_payload "Pipeline Success" "test_payloads/pipeline_success.json"
        ;;
    2)
        send_payload "Pipeline Failed" "test_payloads/pipeline_failed.json"
        ;;
    3)
        send_payload "Job Success" "test_payloads/job_success.json"
        ;;
    4)
        send_payload "Job Failed" "test_payloads/job_failed.json"
        ;;
    5)
        echo "🚀 Запускаю все тесты..."
        echo ""
        send_payload "Pipeline Success" "test_payloads/pipeline_success.json"
        send_payload "Pipeline Failed" "test_payloads/pipeline_failed.json"
        send_payload "Job Success" "test_payloads/job_success.json"
        send_payload "Job Failed" "test_payloads/job_failed.json"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "${GREEN}✅ Все тесты завершены!${NC}"
        echo "Проверь Telegram на наличие уведомлений 📱"
        ;;
    q|Q)
        echo "Пока! 👋"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Неверный выбор${NC}"
        exit 1
        ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 Проверь Telegram на наличие уведомлений!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

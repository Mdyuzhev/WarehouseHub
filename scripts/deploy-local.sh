#!/bin/bash
# =============================================================================
# Скрипт локального деплоя warehouse-api в K3s
# Использование: ./scripts/deploy-local.sh
# =============================================================================

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# =============================================================================
# Проверка окружения
# =============================================================================
info "Проверка окружения..."

command -v docker >/dev/null 2>&1 || error "Docker не установлен"
command -v kubectl >/dev/null 2>&1 || error "kubectl не установлен"

export KUBECONFIG=~/.kube/config

# =============================================================================
# Сборка Docker образа
# =============================================================================
echo ""
info "Сборка Docker образа..."

docker build -t warehouse-api:latest .

success "Образ warehouse-api:latest собран"

# =============================================================================
# Экспорт и импорт в K3s
# =============================================================================
echo ""
info "Экспорт образа в файл..."

docker save warehouse-api:latest -o /tmp/warehouse-api.tar

success "Образ экспортирован в /tmp/warehouse-api.tar"

info "Импорт образа в K3s (containerd)..."

sudo k3s ctr images import /tmp/warehouse-api.tar

success "Образ импортирован в K3s"

# Очистка временного файла
rm -f /tmp/warehouse-api.tar

# =============================================================================
# Применение манифестов
# =============================================================================
echo ""
info "Применение Kubernetes манифестов..."

kubectl apply -f k8s/warehouse/api-configmap.yaml
kubectl apply -f k8s/warehouse/api-deployment.yaml
kubectl apply -f k8s/warehouse/api-service.yaml
kubectl apply -f k8s/warehouse/api-pdb.yaml 2>/dev/null || true

success "Манифесты применены"

# =============================================================================
# Перезапуск деплоймента (для обновления образа)
# =============================================================================
echo ""
info "Перезапуск деплоймента для применения нового образа..."

kubectl rollout restart deployment/warehouse-api -n warehouse

# =============================================================================
# Ожидание готовности
# =============================================================================
echo ""
info "Ожидание запуска пода (до 120 секунд)..."

kubectl wait --for=condition=Ready pod -l app=warehouse-api -n warehouse --timeout=120s

success "Pod запущен и готов!"

# =============================================================================
# Проверка статуса
# =============================================================================
echo ""
info "Статус ресурсов:"
echo ""

kubectl get pods -n warehouse -l app=warehouse-api
echo ""
kubectl get svc -n warehouse -l app=warehouse-api

# =============================================================================
# Проверка health endpoint
# =============================================================================
echo ""
info "Проверка health endpoint..."

sleep 5

HEALTH_RESPONSE=$(curl -s http://localhost:30080/actuator/health 2>/dev/null || echo "FAILED")

if echo "$HEALTH_RESPONSE" | grep -q "UP"; then
    success "Health check пройден!"
    echo "$HEALTH_RESPONSE" | head -5
else
    warn "Health check не пройден или приложение ещё запускается"
    echo "Попробуйте через 30 секунд: curl http://192.168.1.74:30080/actuator/health"
fi

# =============================================================================
# Итоговая информация
# =============================================================================
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     warehouse-api успешно развёрнут!                          ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Точки доступа:"
echo "  Health:     http://192.168.1.74:30080/actuator/health"
echo "  Swagger UI: http://192.168.1.74:30080/swagger-ui.html"
echo "  API Docs:   http://192.168.1.74:30080/api-docs"
echo ""
echo "Полезные команды:"
echo "  kubectl logs -n warehouse -l app=warehouse-api -f"
echo "  kubectl describe pod -n warehouse -l app=warehouse-api"
echo ""

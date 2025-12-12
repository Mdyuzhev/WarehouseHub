#!/bin/bash
# =============================================================================
# Скрипт деплоя warehouse-frontend в K3s
# =============================================================================

set -e

echo "Deploying warehouse-frontend..."

# Сборка Docker образа
echo "Building Docker image..."
docker build -t warehouse-frontend:latest .

# Экспорт и импорт в K3s
echo "Exporting image..."
docker save warehouse-frontend:latest -o /tmp/warehouse-frontend.tar

echo "Importing to K3s..."
sudo k3s ctr images import /tmp/warehouse-frontend.tar
sudo rm -f /tmp/warehouse-frontend.tar

# Применение манифестов
echo "Applying K8s manifests..."
export KUBECONFIG=~/.kube/config
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Перезапуск деплоймента
echo "Restarting deployment..."
kubectl rollout restart deployment/warehouse-frontend -n warehouse
kubectl rollout status deployment/warehouse-frontend -n warehouse --timeout=60s

echo "Frontend deployed successfully!"
echo ""
echo "Access points:"
echo "   http://warehouse.local (via Ingress, requires /etc/hosts entry)"
echo ""
echo "Add to /etc/hosts:"
echo "   192.168.1.74 warehouse.local"

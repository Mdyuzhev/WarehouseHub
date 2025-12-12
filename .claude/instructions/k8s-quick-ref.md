# K8s Quick Reference

## Namespaces
| Namespace | Содержимое |
|-----------|------------|
| warehouse | Production API + Frontend |
| warehouse-dev | Dev API + Frontend |
| notifications | Telegram bot |
| monitoring | Grafana, Prometheus, Loki |
| kube-system | K3s system |

## Частые команды
```bash
# Статус подов
kubectl get pods -n warehouse
kubectl get pods -n warehouse-dev

# Логи
kubectl logs -n warehouse deployment/warehouse-api --tail=100 -f
kubectl logs -n warehouse deployment/warehouse-frontend --tail=50

# Restart
kubectl rollout restart deployment/warehouse-api -n warehouse
kubectl rollout restart deployment/warehouse-frontend -n warehouse

# Secrets
kubectl get secrets -n warehouse
kubectl get secret postgres-credentials -n warehouse -o jsonpath='{.data.password}' | base64 -d

# Events
kubectl get events -n warehouse --sort-by='.lastTimestamp'

# Exec
kubectl exec -it deployment/warehouse-api -n warehouse -- bash
```

## Services / Ports
| Service | NodePort Prod | NodePort Dev |
|---------|---------------|--------------|
| API | 30080 | 31080 |
| Frontend | 30081 | 31081 |
| PostgreSQL | 30432 | 31432 |
| Redis | 30379 | 31379 |

## Deployments
```
warehouse/
├── warehouse-api        # replicas: 1
├── warehouse-frontend   # replicas: 1
├── postgres             # StatefulSet
└── redis                # StatefulSet
```

## Манифесты
```
k8s/
├── warehouse/           # Prod манифесты
├── warehouse-dev/       # Dev манифесты
├── notifications/       # Telegram bot
└── monitoring/          # Grafana stack
```

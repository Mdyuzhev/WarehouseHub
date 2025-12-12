Деплой Frontend в K3s:

```bash
cd /home/flomaster/warehouse-frontend

# 1. Build
docker build --no-cache -t warehouse-frontend:latest .

# 2. Import в K3s
sudo k3s ctr images rm docker.io/library/warehouse-frontend:latest 2>/dev/null || true
docker save warehouse-frontend:latest | sudo k3s ctr images import -

# 3. Restart
kubectl rollout restart deployment/warehouse-frontend -n warehouse
kubectl rollout status deployment/warehouse-frontend -n warehouse --timeout=120s

# 4. Verify
kubectl logs -n warehouse deployment/warehouse-frontend --tail=20
curl -s -o /dev/null -w "%{http_code}" http://192.168.1.74:30081
```

Выполни команды и сообщи результат.

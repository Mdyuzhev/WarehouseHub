Деплой API в K3s:

```bash
cd /home/flomaster/warehouse-api

# 1. Build
docker build --no-cache -t warehouse-api:latest .

# 2. Import в K3s
sudo k3s ctr images rm docker.io/library/warehouse-api:latest 2>/dev/null || true
docker save warehouse-api:latest | sudo k3s ctr images import -

# 3. Restart
kubectl rollout restart deployment/warehouse-api -n warehouse
kubectl rollout status deployment/warehouse-api -n warehouse --timeout=120s

# 4. Verify
kubectl logs -n warehouse deployment/warehouse-api --tail=30
curl -s http://192.168.1.74:30080/actuator/health | jq
```

Выполни команды и сообщи результат.

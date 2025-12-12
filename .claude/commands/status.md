Проверь статус всех компонентов:

```bash
echo "=== K8s Pods ==="
kubectl get pods -n warehouse -o wide 2>/dev/null || echo "K8s недоступен"

echo -e "\n=== Health Checks ==="
echo "Prod API: $(curl -s http://192.168.1.74:30080/actuator/health 2>/dev/null | jq -r .status || echo 'DOWN')"
echo "Prod UI: $(curl -s -o /dev/null -w '%{http_code}' http://192.168.1.74:30081 2>/dev/null || echo 'DOWN')"
echo "Yandex API: $(curl -s https://api.wh-lab.ru/actuator/health 2>/dev/null | jq -r .status || echo 'DOWN')"
echo "Yandex UI: $(curl -s -o /dev/null -w '%{http_code}' https://wh-lab.ru 2>/dev/null || echo 'DOWN')"

echo -e "\n=== RAM ==="
free -h | grep Mem
```

Выполни и покажи результат.

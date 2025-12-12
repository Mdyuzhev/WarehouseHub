Статус тестовой инфраструктуры:

```bash
echo "=== Testing Infrastructure ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "selenoid|allure" || echo "❌ Не запущена"

echo -e "\n=== Health Checks ==="
echo "Selenoid UI: $(curl -s -o /dev/null -w '%{http_code}' http://192.168.1.74:8090 2>/dev/null || echo 'DOWN')"
echo "Selenoid API: $(curl -s -o /dev/null -w '%{http_code}' http://192.168.1.74:4444/status 2>/dev/null || echo 'DOWN')"
echo "Allure UI: $(curl -s -o /dev/null -w '%{http_code}' http://192.168.1.74:5252 2>/dev/null || echo 'DOWN')"
echo "Allure API: $(curl -s -o /dev/null -w '%{http_code}' http://192.168.1.74:5050/allure-docker-service/version 2>/dev/null || echo 'DOWN')"

echo -e "\n=== URLs ==="
echo "Selenoid UI: http://192.168.1.74:8090"
echo "Allure UI:   http://192.168.1.74:5252"
```

Выполни и покажи результат.

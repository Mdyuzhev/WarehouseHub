Запуск тестовой инфраструктуры:

```bash
echo "🧪 Starting testing infrastructure..."

# Selenoid (UI тесты)
cd /home/flomaster/warehouse-testing/infrastructure/selenoid
docker-compose up -d
echo "Selenoid: http://192.168.1.74:8090"

# Allure (отчёты)
cd /home/flomaster/warehouse-testing/infrastructure/allure
docker-compose up -d
echo "Allure: http://192.168.1.74:5252"

# Проверка
sleep 3
echo -e "\n=== Status ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "selenoid|allure"
```

Выполни и сообщи результат.

**После работы:** не забудь `/stop-testing`

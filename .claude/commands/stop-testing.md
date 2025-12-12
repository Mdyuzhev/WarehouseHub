Остановка тестовой инфраструктуры:

```bash
echo "🛑 Stopping testing infrastructure..."

# Selenoid
cd /home/flomaster/warehouse-testing/infrastructure/selenoid
docker-compose down

# Allure
cd /home/flomaster/warehouse-testing/infrastructure/allure
docker-compose down

# Проверка
echo -e "\n=== Освобождено ==="
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "selenoid|allure" || echo "✅ Тестовая инфра остановлена"

echo -e "\n=== RAM ==="
free -h | grep Mem
```

Выполни и сообщи результат.

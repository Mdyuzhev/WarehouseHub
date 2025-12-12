# API Endpoints Reference

## Base URLs
- **Dev:** http://192.168.1.74:31080/api/v1
- **Prod:** http://192.168.1.74:30080/api/v1
- **Yandex:** https://api.wh-lab.ru/api/v1

## Auth
```bash
# Login (получить JWT)
curl -X POST http://192.168.1.74:30080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Response: {"token":"eyJ...","user":{...}}
```

## Products
```bash
# Список
curl -H "Authorization: Bearer $TOKEN" http://192.168.1.74:30080/api/v1/products

# Создать
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  http://192.168.1.74:30080/api/v1/products \
  -d '{"name":"Test","sku":"SKU001"}'
```

## Stock
```bash
# Остатки
curl -H "Authorization: Bearer $TOKEN" http://192.168.1.74:30080/api/v1/stock

# По facility
curl -H "Authorization: Bearer $TOKEN" http://192.168.1.74:30080/api/v1/stock?facilityId=1
```

## Facilities
```bash
curl -H "Authorization: Bearer $TOKEN" http://192.168.1.74:30080/api/v1/facilities
```

## Documents
```bash
# Приходные
curl -H "Authorization: Bearer $TOKEN" http://192.168.1.74:30080/api/v1/receipt-documents

# Расходные
curl -H "Authorization: Bearer $TOKEN" http://192.168.1.74:30080/api/v1/shipment-documents

# Акты инвентаризации
curl -H "Authorization: Bearer $TOKEN" http://192.168.1.74:30080/api/v1/inventory-acts

# Акты списания
curl -H "Authorization: Bearer $TOKEN" http://192.168.1.74:30080/api/v1/issue-acts
```

## Health
```bash
curl http://192.168.1.74:30080/actuator/health
curl http://192.168.1.74:30080/actuator/info
curl http://192.168.1.74:30080/actuator/metrics
```

## Quick Test Script
```bash
#!/bin/bash
HOST=${1:-"http://192.168.1.74:30080"}
TOKEN=$(curl -s -X POST "$HOST/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r .token)

echo "Products: $(curl -s -H "Authorization: Bearer $TOKEN" "$HOST/api/v1/products" | jq length)"
echo "Stock: $(curl -s -H "Authorization: Bearer $TOKEN" "$HOST/api/v1/stock" | jq length)"
echo "Facilities: $(curl -s -H "Authorization: Bearer $TOKEN" "$HOST/api/v1/facilities" | jq length)"
```

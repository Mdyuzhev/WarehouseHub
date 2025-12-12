# WarehouseHub

**Warehouse Management System** — система управления складом с поддержкой распределённых центров (DC → WH → PP).

## Статус проекта

| Компонент | Статус | Описание |
|-----------|--------|----------|
| **Backend API** | ✅ Ready | REST API, документооборот, Kafka интеграция |
| **Frontend** | ✅ Ready | 22 экрана для DC/WH/PP, facility selector |
| **Testing** | ✅ Ready | E2E, UI, Load tests |
| **Infrastructure** | ✅ Ready | K8s, CI/CD, Monitoring |

**Завершённые фазы:**
- Phase 1: Core API (Products, Stock, Facilities)
- Phase 2: Документооборот (Receipt, Shipment, Issue, Inventory Acts) + Kafka
- Phase 3: Frontend (Navigation, Documents, Facility Screens)

## Monorepo Structure

```
WaregouseHub/
├── api/                    # Java 17 + Spring Boot 3.2
│   └── src/main/java/com/warehouse/
│       ├── controller/     # REST endpoints
│       ├── service/        # Business logic
│       ├── model/          # JPA entities
│       └── config/         # Security, Redis, Kafka
│
├── frontend/               # Vue.js 3.4 + Vite 5
│   └── src/
│       ├── views/          # dc/, wh/, pp/ screens
│       ├── components/     # UI components
│       └── stores/         # Pinia state
│
├── testing/                # Tests
│   ├── e2e-tests/          # RestAssured + JUnit5 + Allure
│   ├── ui-tests/           # Selenide + JUnit5
│   ├── loadtest/           # Locust
│   └── k6-kafka/           # K6 Kafka tests
│
├── k8s/                    # Kubernetes manifests
│   ├── warehouse/          # Production
│   ├── warehouse-dev/      # Development
│   └── monitoring/         # Prometheus + Grafana
│
├── production/             # Yandex Cloud (docker-compose)
├── docs/                   # Documentation
├── telegram-bot/           # Notification bot
└── .claude/                # AI agent config
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Java 17, Spring Boot 3.2, Spring Security, JPA |
| Frontend | Vue.js 3.4, Vite 5, Pinia, Axios |
| Database | PostgreSQL 15, Flyway migrations |
| Cache | Redis 7.4 |
| Messaging | Kafka (KRaft mode) |
| Container | K3s (containerd) |
| CI/CD | GitLab CI + GitHub Actions |
| Monitoring | Prometheus, Grafana, Loki |
| Testing | JUnit5, RestAssured, Selenide, k6, Locust |

## Environments

| Env | API | Frontend | Deploy |
|-----|-----|----------|--------|
| Dev | http://192.168.1.74:31080 | http://192.168.1.74:31081 | Auto (develop) |
| Prod | http://192.168.1.74:30080 | http://192.168.1.74:30081 | Manual (main) |
| Cloud | https://api.wh-lab.ru | https://wh-lab.ru | GitHub Actions |

## Features

### Logistics Flow
```
Supplier → DC (Distribution Center) → WH (Warehouse) → PP (Pickup Point) → Customer
```

- **Receipt Documents** — приход товаров (supplier → DC, DC → WH, WH → PP)
- **Shipment Documents** — отгрузка товаров (DC → WH, WH → PP)
- **Issue Acts** — выдача клиентам (PP only)
- **Inventory Acts** — инвентаризация и корректировка остатков

### Kafka Integration
- Auto-create Receipt при отправке Shipment
- Auto-update Shipment.DELIVERED при подтверждении Receipt

### Frontend Features
- Facility selector с группировкой DC/WH/PP
- Color themes по типу facility
- Document workflows с статусами
- Stock management

## Quick Start

```bash
# Clone
git clone https://github.com/Mdyuzhev/WaregouseHub.git
cd WaregouseHub

# Run API
cd api && ./mvnw spring-boot:run

# Run Frontend
cd frontend && npm install && npm run dev

# Or deploy to K8s
kubectl apply -f k8s/warehouse/
```

## API Endpoints

| Group | Base Path | Description |
|-------|-----------|-------------|
| Auth | /api/v1/auth | Login, register, me |
| Products | /api/v1/products | CRUD товаров |
| Facilities | /api/v1/facilities | DC, WH, PP управление |
| Stock | /api/v1/stock | Остатки, резервы |
| Receipts | /api/v1/receipt-documents | Приходные накладные |
| Shipments | /api/v1/shipment-documents | Расходные накладные |
| Issues | /api/v1/issue-acts | Акты выдачи |
| Inventory | /api/v1/inventory-acts | Акты инвентаризации |

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Components](docs/COMPONENTS.md)
- [Deploy Guide](docs/DEPLOY_GUIDE.md)
- [Testing](docs/TESTING.md)
- [Troubleshooting](docs/TROUBLESHOOTING_GUIDE.md)

## License

Private repository. All rights reserved.

---

**Maintainer:** [@Mdyuzhev](https://github.com/Mdyuzhev)

# Warehouse Project — Claude Code Config

## Роль
Технический исполнитель. Задача → Решение → Проверка. Без вариантов и философии.

---

## 🗺️ Карта проекта (Monorepo)

```
warehouse-master/              # GitHub: WaregouseHub
├── api/                       # Java 17 + Spring Boot 3.2
│   └── src/main/java/com/warehouse/
│       ├── controller/        # REST endpoints
│       ├── service/           # Бизнес-логика
│       ├── model/             # JPA entities
│       └── config/            # Security, Redis, Kafka
│
├── frontend/                  # Vue.js 3.4 + Vite 5
│   └── src/
│       ├── views/             # dc/, pp/, wh/ screens
│       ├── components/        # UI компоненты
│       └── stores/            # Pinia state
│
├── testing/                   # Тесты
│   ├── e2e-tests/             # RestAssured + JUnit5
│   ├── ui-tests/              # Selenide + JUnit5
│   ├── loadtest/              # Locust
│   └── k6-kafka/              # K6 Kafka tests
│
├── k8s/                       # K8s манифесты
├── production/                # Yandex Cloud docker-compose
├── docs/                      # Документация
├── telegram-bot/              # Notification bot
└── .claude/                   # Agent config
```

**GitHub:** https://github.com/Mdyuzhev/WaregouseHub

---

## ⚡ Окружения

| Env | API | Frontend | Namespace | Deploy |
|-----|-----|----------|-----------|--------|
| **Dev** | :31080 | :31081 | warehouse-dev | auto (develop) |
| **Prod** | :30080 | :30081 | warehouse | MR → main |
| **Yandex** | api.wh-lab.ru | wh-lab.ru | docker-compose | manual |

**Host:** 192.168.1.74

---

## 🔑 Учётки

| Env | User | Password |
|-----|------|----------|
| Dev/Prod | admin | admin123 |
| Prod | employee | password123 |

---

## 🚨 Критические правила

| ❌ НЕ делать | ✅ Делать |
|-------------|----------|
| `docker push` | `docker save \| sudo k3s ctr import -` |
| `git push origin main` | MR через GitLab |
| Docker build локально | Build в CI или на dev |
| Flyway без проверки | `ls db/migration/` перед созданием |

---

## 🛠️ Шаблоны команд

### K3s деплой
```bash
docker build --no-cache -t IMAGE:TAG .
sudo k3s ctr images rm docker.io/library/IMAGE:TAG 2>/dev/null || true
docker save IMAGE:TAG | sudo k3s ctr images import -
kubectl rollout restart deployment/NAME -n NAMESPACE
kubectl logs -n NAMESPACE deployment/NAME --tail=50
```

### Health check
```bash
curl -s http://192.168.1.74:30080/actuator/health | jq .status
```

### GitHub Issues
```bash
gh issue list --repo Mdyuzhev/WaregouseHub
gh issue create --repo Mdyuzhev/WaregouseHub --title "X" --body "Y"
gh issue close 123 --repo Mdyuzhev/WaregouseHub
```

### Lab control (RAM management)
```bash
lab start-warehouse   # ПЕРЕД работой
lab stop-warehouse    # ПОСЛЕ работы
lab status            # Проверка
```

### Testing infra (только когда нужно!)
```bash
/start-testing        # Selenoid + Allure (~500MB RAM)
/stop-testing         # Освободить RAM
/testing-status       # Проверить статус
```

---

## 📝 Паттерны кода

### Backend (Java)
```java
// Controller
@RestController @RequestMapping("/api/v1/products")
@RequiredArgsConstructor
public class ProductController {
    @GetMapping @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<List<ProductDTO>> getAll() {...}
}

// Service
@Service @RequiredArgsConstructor
public class ProductService {
    @Transactional
    public Product save(Product p) {...}
}
```

**Lombok:** `@Data`, `@RequiredArgsConstructor`, `@Builder`
**Образцы:** `StockController.java`, `StockService.java`

### Frontend (Vue)
```vue
<script setup>
import { ref, onMounted } from 'vue'
import { useProductStore } from '@/stores/product'
const store = useProductStore()
</script>
```

**Образцы:** `views/wh/`, `components/`

### Flyway
```sql
-- V{N}__{description}.sql
-- Проверь версию: ls db/migration/
```

---

## 📁 Документация

| Задача | Файл |
|--------|------|
| Деплой | docs/DEPLOY_GUIDE.md |
| Архитектура | docs/ARCHITECTURE.md |
| Компоненты | docs/COMPONENTS.md |
| Тесты | docs/TESTING.md |
| Проблемы | docs/TROUBLESHOOTING_GUIDE.md |

---

## 🔄 Git Workflow

| Ветка | Порты | Триггер |
|-------|-------|---------|
| develop | 31xxx | Auto deploy |
| main | 30xxx | MR only |

**Коммит:** `type: описание` (feat, fix, refactor, docs, chore)

---

## ✅ Чеклист

- [ ] Аналог в проекте? → Копируй паттерн
- [ ] K3s? → `docker save | k3s ctr import`
- [ ] Flyway? → `ls db/migration/` сначала
- [ ] Команда проверки указана?

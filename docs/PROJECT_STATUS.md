# Warehouse API - Project Status Report

**Last Updated**: 2025-11-27
**Version**: 0.0.1-SNAPSHOT
**Task**: WH-25

---

## 1. General Information

| Parameter | Value |
|-----------|-------|
| **Project** | warehouse-api |
| **Version** | 0.0.1-SNAPSHOT |
| **Java** | 17 |
| **Spring Boot** | 3.2.0 |
| **GitLab** | http://192.168.1.74:8080 |
| **K8s API** | http://192.168.1.74:30080 |
| **Latest Commit** | bc56497 (#WH-25) |

---

## 2. Project Structure

```
warehouse-api/
├── .gitlab-ci.yml          # CI/CD pipeline
├── .claude/
│   └── memory.md           # Claude memory
├── k8s/
│   ├── configmap.yaml      # ConfigMap
│   ├── deployment.yaml     # Deployment
│   ├── service.yaml        # NodePort Service (30080)
│   └── servicemonitor.yaml # Prometheus ServiceMonitor
├── pom.xml
├── Dockerfile
└── src/
    ├── main/java/com/warehouse/
    │   ├── WarehouseApiApplication.java
    │   ├── config/
    │   │   ├── DataInitializer.java
    │   │   ├── MetricsConfig.java
    │   │   └── SecurityConfig.java
    │   ├── controller/
    │   │   ├── AuthController.java
    │   │   └── ProductController.java
    │   ├── dto/
    │   │   ├── AuthRequest.java
    │   │   ├── AuthResponse.java
    │   │   └── RegisterRequest.java
    │   ├── model/
    │   │   ├── Product.java
    │   │   ├── Role.java
    │   │   └── User.java
    │   ├── repository/
    │   │   ├── ProductRepository.java
    │   │   └── UserRepository.java
    │   ├── security/
    │   │   ├── JwtAuthenticationFilter.java
    │   │   └── JwtService.java
    │   └── service/
    │       ├── CustomUserDetailsService.java
    │       └── ProductService.java
    └── main/resources/
        ├── application.properties
        └── application-k8s.properties
```

---

## 3. Dependencies (pom.xml)

| Dependency | Purpose | Status |
|------------|---------|--------|
| spring-boot-starter-data-jpa | JPA/Hibernate | OK |
| spring-boot-starter-validation | Validation | OK |
| spring-boot-starter-web | REST API | OK |
| spring-boot-starter-actuator | Health/Metrics | OK |
| spring-boot-starter-security | Spring Security | OK |
| jjwt-api/impl/jackson (0.11.5) | JWT tokens | OK |
| springdoc-openapi (2.3.0) | Swagger UI | OK |
| postgresql | PostgreSQL DB | OK |
| lombok (1.18.30) | Boilerplate | OK |
| micrometer-registry-prometheus | Prometheus metrics | OK |
| h2 (test) | Tests | OK |
| rest-assured (test) | API tests | OK |

---

## 4. Security Configuration

### 4.1 Public Endpoints
- `/api/auth/**` - authentication
- `/actuator/health` - health check
- `/actuator/prometheus` - metrics
- `/swagger-ui/**`, `/v3/api-docs/**` - documentation

### 4.2 Roles and Access

| Role | Permissions |
|------|-------------|
| **SUPER_USER** | Full access |
| **ADMIN** | User management, actuator |
| **MANAGER** | View products, reports |
| **EMPLOYEE** | CRUD products |

### 4.3 JWT Configuration
- Algorithm: HS256
- Expiration: 86400000 ms (24 hours)
- Stateless session

---

## 5. API Endpoints

### 5.1 Authentication
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/register` | Register |
| GET | `/api/auth/me` | Current user |

### 5.2 Products
| Method | Path | Roles |
|--------|------|-------|
| GET | `/api/products` | All authenticated |
| POST | `/api/products` | SUPER_USER, EMPLOYEE |
| DELETE | `/api/products/{id}` | SUPER_USER, EMPLOYEE |

### 5.3 Actuator
| Path | Access |
|------|--------|
| `/actuator/health` | Public |
| `/actuator/prometheus` | Public |
| `/actuator/*` | SUPER_USER, ADMIN |

---

## 6. Monitoring (WH-25)

### 6.1 Prometheus Metrics
- **Endpoint**: `/actuator/prometheus`
- **Tags**: `application=warehouse-api`, `environment=production`
- **Scrape interval**: 15s

### 6.2 Custom Metrics
- `warehouse.products.created` - products created counter
- `warehouse.products.deleted` - products deleted counter

### 6.3 Grafana Dashboard
- **URL**: http://192.168.1.74:3000/d/warehouse-api/warehouse-api-monitoring
- **Credentials**: admin / admin123

**Panels:**
1. Uptime (stat)
2. JVM Heap Memory (gauge, thresholds 70%/90%)
3. HTTP Request Rate (timeseries)
4. HTTP Response Time p95 (timeseries)
5. Database Connection Pool (timeseries)
6. Products Created (stat)

---

## 7. Kubernetes Manifests

### 7.1 deployment.yaml
- Replicas: 1
- Image: `warehouse-api:latest` (imagePullPolicy: Never)
- Resources: 256Mi-512Mi RAM, 200m-500m CPU
- Probes: readiness (30s), liveness (60s)

### 7.2 service.yaml
- Type: NodePort
- Port: 8080 → 30080

### 7.3 configmap.yaml
- Profile: `k8s`
- Logging: DEBUG for com.warehouse

### 7.4 servicemonitor.yaml
- Namespace: monitoring
- Labels: `release: prometheus`
- Interval: 15s

---

## 8. CI/CD Pipeline

**Stages:**
1. `validate` - mvn validate
2. `build` - mvn compile
3. `test` - mvn test
4. `image` - Docker build + k3s import
5. `deploy` - kubectl apply + rollout restart

**Important (from memory.md):**
- Clean Docker cache BEFORE build
- Unique tar filename with `$CI_COMMIT_SHORT_SHA`
- sudo rm old images from k3s

---

## 9. Health Check Status

| Component | Status | Notes |
|-----------|--------|-------|
| Health | UP | PostgreSQL connected |
| Login API | OK | JWT generated |
| Products API | OK | Products in DB |
| Swagger UI | 200 | Documentation available |
| Prometheus | OK | Metrics exported |
| Grafana | OK | v12.3.0, dashboard created |

---

## 10. Test Users

| Username | Password | Role |
|----------|----------|------|
| superuser | super123 | SUPER_USER |
| admin | admin123 | ADMIN |
| manager | manager123 | MANAGER |
| employee | employee123 | EMPLOYEE |

---

## 11. Known Issues

| ID | Description | Status |
|----|-------------|--------|
| WH-24 | Test `shouldReturnBadRequestWhenNameIsEmpty` returns 403 instead of 400 | @Disabled |

---

## 12. Links

| Resource | URL |
|----------|-----|
| API | http://192.168.1.74:30080 |
| Swagger | http://192.168.1.74:30080/swagger-ui.html |
| Prometheus | http://192.168.1.74:30080/actuator/prometheus |
| Grafana | http://192.168.1.74:3000 |
| GitLab | http://192.168.1.74:8080 |
| YouTrack | http://192.168.1.74:8088 |

---

## 13. Recent Commits (WH-25)

```
bc56497 #WH-25 Add ServiceMonitor for Prometheus scraping
57517d0 #WH-25 Enable Prometheus metrics in k8s profile
19602b4 #WH-25 Add Prometheus metrics export for Grafana monitoring
561ed5f #WH-22 Add documentation and Claude memory
```

---

**SUMMARY**: The warehouse-api project is fully functional and ready for use. Monitoring via Prometheus/Grafana is configured and working.

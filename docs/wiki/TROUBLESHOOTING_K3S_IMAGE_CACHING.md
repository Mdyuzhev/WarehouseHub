# Troubleshooting: K3s Image Caching Issues in CI/CD

## Проблема

После добавления новых контроллеров (AuthController) в Spring Boot приложение, endpoint'ы возвращали 404, хотя:
- Код компилировался успешно (видно в логах: "Compiling 18 source files")
- JAR файл создавался корректно
- Docker образ собирался с `--no-cache`
- Pipeline проходил успешно
- Старые контроллеры (ProductController) продолжали работать

## Симптомы

1. Новые REST endpoints возвращают 404
2. Старые endpoints работают нормально
3. `/actuator/mappings` не показывает новые контроллеры
4. В логах сборки видно правильное количество скомпилированных файлов
5. Hash образа в k3s containerd остаётся одинаковым между сборками

## Корневая причина

**Tar-файл Docker образа не перезаписывался между сборками.**

При выполнении:
```bash
docker save warehouse-api:latest -o /tmp/warehouse-api.tar
```

Если файл `/tmp/warehouse-api.tar` уже существует и у процесса нет прав на его удаление/перезапись, `docker save` может:
- Завершиться с ошибкой (которая игнорируется с `|| true`)
- Не перезаписать файл полностью
- Оставить старый файл без изменений

В результате в k3s containerd импортируется **старый образ** со старым кодом.

## Диагностика

### 1. Проверить hash образа в k3s
```bash
sudo k3s ctr images list | grep warehouse-api
```
Если hash не меняется между деплоями - проблема с образом.

### 2. Проверить логи build-image job
Искать:
```
rm: cannot remove '/tmp/warehouse-api.tar': Operation not permitted
```

### 3. Проверить actuator mappings
```bash
curl http://host:port/actuator/mappings | grep -i "YourController"
```
Если контроллер отсутствует - образ устаревший.

## Решение

### Правильная конфигурация CI/CD

```yaml
build-image:
  stage: image
  script:
    # 1. Очистка старых tar файлов В НАЧАЛЕ с sudo
    - sudo rm -f /tmp/warehouse-api*.tar || true

    # 2. Сборка образа без кэша
    - docker build --no-cache -t $IMAGE_NAME:$IMAGE_TAG .

    # 3. Экспорт с УНИКАЛЬНЫМ именем файла
    - docker save $IMAGE_NAME:$IMAGE_TAG -o /tmp/$IMAGE_NAME-$CI_COMMIT_SHORT_SHA.tar

    # 4. Удаление старого образа из k3s
    - sudo k3s ctr images rm docker.io/library/$IMAGE_NAME:$IMAGE_TAG || true

    # 5. Импорт нового образа
    - sudo k3s ctr images import /tmp/$IMAGE_NAME-$CI_COMMIT_SHORT_SHA.tar

    # 6. Очистка с sudo
    - sudo rm -f /tmp/$IMAGE_NAME-$CI_COMMIT_SHORT_SHA.tar || true
```

### Ключевые моменты:

1. **Очистка в начале с sudo** - удаляет любые застрявшие файлы от предыдущих сборок
2. **Уникальное имя файла** с `$CI_COMMIT_SHORT_SHA` - гарантирует отсутствие конфликтов
3. **sudo для cleanup** - права gitlab-runner могут отличаться от прав создателя файла
4. **Удаление образа из k3s перед импортом** - гарантирует загрузку нового образа

## Альтернативные решения

### 1. Использовать tmpfs для tar файлов
```bash
docker save ... -o /dev/shm/$IMAGE_NAME.tar
```
Файлы в /dev/shm не сохраняются между перезагрузками.

### 2. Использовать уникальные теги образов
```yaml
- docker build -t $IMAGE_NAME:$CI_COMMIT_SHORT_SHA .
- kubectl set image deployment/app container=$IMAGE_NAME:$CI_COMMIT_SHORT_SHA
```

### 3. Docker registry вместо прямого импорта
Использовать локальный Docker registry в k3s вместо экспорта/импорта tar файлов.

## Связанные проблемы

- Если меняется Spring Security конфигурация, но endpoints не обновляются - та же причина
- Если изменения в application.properties не применяются - та же причина
- Если новые зависимости в pom.xml не подключаются - та же причина

## Дополнительные настройки для отладки

### application.properties
```properties
# Включить debug logging для Spring Security
logging.level.org.springframework.security=DEBUG
logging.level.com.warehouse=DEBUG

# Включить actuator endpoints для диагностики
management.endpoints.web.exposure.include=health,info,mappings,beans
```

### SecurityConfig.java
```java
// Разрешить доступ к диагностическим endpoints
.requestMatchers("/actuator/mappings").permitAll()
.requestMatchers("/actuator/beans").permitAll()
```

## Проверка исправления

После применения исправления:
1. Hash образа должен меняться при каждой сборке
2. Количество скомпилированных файлов должно соответствовать количеству .java файлов
3. Новые endpoints должны появиться в `/actuator/mappings`
4. Все контроллеры должны быть доступны

---

**Дата:** 2025-11-27
**Issue:** WH-22
**Автор:** Claude Code

# CI/CD Pipeline с автоматическим деплоем

## Обзор

Данный документ описывает настройку CI/CD pipeline для автоматической сборки, тестирования и деплоя warehouse-api в Kubernetes при каждом пуше в ветку main.

## Требования к окружению

Перед настройкой CI/CD pipeline необходимо выполнить следующие настройки на сервере, где работает GitLab Runner.

### Права Docker для gitlab-runner

Пользователь gitlab-runner должен иметь доступ к Docker daemon. Для этого добавьте его в группу docker:

```bash
sudo usermod -aG docker gitlab-runner
sudo systemctl restart gitlab-runner
```

### Права sudo для K3s

Создайте файл sudoers для разрешения импорта образов в K3s без пароля:

```bash
sudo bash -c 'cat > /etc/sudoers.d/cicd-automation << EOF
# CI/CD automation for gitlab-runner
gitlab-runner ALL=(ALL) NOPASSWD: /usr/local/bin/k3s ctr images import *
gitlab-runner ALL=(ALL) NOPASSWD: /usr/local/bin/k3s ctr images list
gitlab-runner ALL=(ALL) NOPASSWD: /usr/local/bin/k3s ctr images rm *
gitlab-runner ALL=(ALL) NOPASSWD: /bin/rm -f /tmp/warehouse-api.tar
EOF'

sudo chmod 440 /etc/sudoers.d/cicd-automation
```

### Kubeconfig для gitlab-runner

Скопируйте kubeconfig K3s для пользователя gitlab-runner:

```bash
sudo mkdir -p /home/gitlab-runner/.kube
sudo cp /etc/rancher/k3s/k3s.yaml /home/gitlab-runner/.kube/config
sudo chown -R gitlab-runner:gitlab-runner /home/gitlab-runner/.kube
sudo chmod 600 /home/gitlab-runner/.kube/config
```

## Архитектура Pipeline

Pipeline состоит из пяти последовательных стадий, каждая из которых выполняется только при успешном завершении предыдущей.

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ validate │───►│  build   │───►│   test   │───►│  image   │───►│  deploy  │
│          │    │          │    │          │    │          │    │          │
│  mvnw    │    │  mvnw    │    │  mvnw    │    │  docker  │    │ kubectl  │
│ validate │    │ compile  │    │  test    │    │  build   │    │  apply   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                     │               │
                                                     └───────────────┘
                                                      только main branch
```

## Стадии Pipeline

### validate

Проверяет корректность структуры проекта и pom.xml. Выполняется для всех веток.

### build

Компилирует исходный код Java. Артефакты (target/) передаются в следующие стадии. Выполняется для всех веток.

### test

Запускает unit-тесты и интеграционные тесты. Результаты тестов сохраняются как JUnit reports в GitLab. Выполняется для всех веток.

### image

Собирает Docker образ приложения и импортирует его в K3s containerd. Выполняется только для ветки main. Этапы работы: сборка образа через docker build, экспорт в tar-файл, импорт в K3s через sudo k3s ctr images import.

### deploy

Применяет Kubernetes манифесты и выполняет rolling update деплоймента. Выполняется только для ветки main. Ожидает успешного завершения rollout и проверяет health endpoint.

## Конфигурация

### Переменные Pipeline

| Переменная | Значение | Описание |
|------------|----------|----------|
| IMAGE_NAME | warehouse-api | Имя Docker образа |
| IMAGE_TAG | latest | Тег образа |
| K8S_NAMESPACE | warehouse | Kubernetes namespace |

### Требования к Runner

Pipeline использует Shell executor на сервере 192.168.1.74. Runner должен иметь доступ к docker, kubectl и sudo для k3s ctr images import (настроено через /etc/sudoers.d/cicd-automation).

## Процесс деплоя

При пуше в ветку main происходит следующее:

1. GitLab запускает pipeline
2. Стадии validate, build, test выполняются последовательно
3. При успешных тестах запускается сборка Docker образа
4. Образ импортируется в K3s containerd
5. Применяются K8s манифесты
6. Deployment перезапускается для использования нового образа
7. Pipeline ожидает готовности пода
8. Выполняется проверка health endpoint

## Мониторинг Pipeline

### Просмотр статуса

В GitLab перейдите в репозиторий → CI/CD → Pipelines. Каждый pipeline показывает статус всех стадий.

### Логи стадий

Нажмите на конкретную стадию для просмотра логов выполнения.

### Статус в Kubernetes

```bash
kubectl get pods -n warehouse -l app=warehouse-api
kubectl describe deployment warehouse-api -n warehouse
```

## Откат изменений

Если деплой привёл к проблемам, можно откатиться на предыдущую версию.

```bash
kubectl rollout undo deployment/warehouse-api -n warehouse
```

Или откатиться на конкретную ревизию:

```bash
kubectl rollout history deployment/warehouse-api -n warehouse
kubectl rollout undo deployment/warehouse-api -n warehouse --to-revision=2
```

## Troubleshooting

### Pipeline падает на стадии image

Проверьте, что Docker daemon запущен и доступен:

```bash
docker ps
```

Проверьте права sudo для k3s ctr:

```bash
sudo k3s ctr images list
```

### Pipeline падает на стадии deploy

Проверьте доступность kubectl:

```bash
export KUBECONFIG=~/.kube/config
kubectl get nodes
```

Проверьте логи пода:

```bash
kubectl logs -n warehouse -l app=warehouse-api
```

### Pod не переходит в Ready

Проверьте, что PostgreSQL доступен:

```bash
kubectl get pods -n warehouse -l app.kubernetes.io/name=postgresql
```

Проверьте логи приложения на ошибки подключения к БД.

---

*Задача: WH-20*
*Автор: Flomaster*
*Дата: 26 ноября 2025*

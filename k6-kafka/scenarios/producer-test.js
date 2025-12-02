// k6-kafka/scenarios/producer-test.js
// Сценарий нагрузочного тестирования Kafka Producer
// Симулирует поведение warehouse-api при отправке событий аудита
// WH-210

import { Writer } from 'k6/x/kafka';
import { check, sleep } from 'k6';
import { Counter, Trend, Rate } from 'k6/metrics';
import encoding from 'k6/encoding';

// ═══════════════════════════════════════════════════════════════════════
// КОНФИГУРАЦИЯ
// ═══════════════════════════════════════════════════════════════════════

const KAFKA_BROKERS = __ENV.KAFKA_BROKERS || 'kafka.warehouse.svc.cluster.local:9092';
const TOPIC_AUDIT = 'warehouse.audit';
const TOPIC_NOTIFICATIONS = 'warehouse.notifications';

// ═══════════════════════════════════════════════════════════════════════
// КАСТОМНЫЕ МЕТРИКИ (отправляются в Prometheus)
// ═══════════════════════════════════════════════════════════════════════

const kafkaProduceLatency = new Trend('kafka_produce_latency_ms', true);
const kafkaProduceErrors = new Counter('kafka_produce_errors_total');
const kafkaMessagesProduced = new Counter('kafka_messages_produced_total');
const kafkaProduceSuccess = new Rate('kafka_produce_success_rate');

// ═══════════════════════════════════════════════════════════════════════
// НАСТРОЙКИ ТЕСТОВЫХ СЦЕНАРИЕВ
// ═══════════════════════════════════════════════════════════════════════

export const options = {
    scenarios: {
        // Сценарий: Постоянная нагрузка для baseline
        constant_load: {
            executor: 'constant-vus',
            vus: parseInt(__ENV.K6_VUS) || 10,
            duration: __ENV.K6_DURATION || '2m',
            exec: 'produceEvents',
            tags: { scenario: 'constant' },
        },
    },
    // Пороговые значения для автоматического pass/fail
    thresholds: {
        'kafka_produce_latency_ms': ['p(95)<100', 'p(99)<500'],
        'kafka_produce_success_rate': ['rate>0.99'],
        'kafka_produce_errors_total': ['count<10'],
    },
};

// ═══════════════════════════════════════════════════════════════════════
// ИНИЦИАЛИЗАЦИЯ KAFKA WRITER
// ═══════════════════════════════════════════════════════════════════════

const writer = new Writer({
    brokers: KAFKA_BROKERS.split(','),
    topic: TOPIC_AUDIT,
    autoCreateTopic: true,    // Автосоздание топика если не существует
    // requiredAcks: 1 = leader only (быстрее для тестов)
    requiredAcks: 1,
    batchSize: 16384,         // 16KB batch
    batchTimeout: 10,         // 10ms linger
    compression: 'none',      // Без сжатия для честного теста
});

const notificationWriter = new Writer({
    brokers: KAFKA_BROKERS.split(','),
    topic: TOPIC_NOTIFICATIONS,
    autoCreateTopic: true,
    requiredAcks: 1,
    batchSize: 16384,
    batchTimeout: 10,
});

// ═══════════════════════════════════════════════════════════════════════
// ГЕНЕРАТОРЫ ТЕСТОВЫХ ДАННЫХ
// ═══════════════════════════════════════════════════════════════════════

// Типы событий аудита (как в warehouse-api AuditService)
const EVENT_TYPES = ['CREATE', 'UPDATE', 'DELETE'];
const CATEGORIES = ['ELECTRONICS', 'FOOD', 'CLOTHING', 'TOOLS', 'OTHER'];

function generateAuditEvent(vu, iter) {
    const eventType = EVENT_TYPES[Math.floor(Math.random() * EVENT_TYPES.length)];
    const category = CATEGORIES[Math.floor(Math.random() * CATEGORIES.length)];

    return {
        eventType: eventType,
        entityType: 'Product',
        entityId: `prod-${vu}-${iter}-${Date.now()}`,
        userId: `user-${vu}`,
        timestamp: Date.now(),
        details: {
            name: `Test Product ${iter}`,
            category: category,
            quantity: Math.floor(Math.random() * 100) + 1,
            price: Math.round(Math.random() * 10000) / 100,
        },
    };
}

function generateNotificationEvent(vu, iter) {
    const types = ['LOW_STOCK', 'OUT_OF_STOCK'];
    const type = types[Math.floor(Math.random() * types.length)];

    return {
        type: type,
        productId: `prod-${vu}-${iter}`,
        productName: `Test Product ${iter}`,
        currentQuantity: type === 'OUT_OF_STOCK' ? 0 : Math.floor(Math.random() * 10),
        threshold: 10,
        timestamp: Date.now(),
    };
}

// ═══════════════════════════════════════════════════════════════════════
// ОСНОВНАЯ ФУНКЦИЯ ТЕСТА
// ═══════════════════════════════════════════════════════════════════════

// default export для совместимости с K6_VUS/K6_DURATION env переменными
export default function() {
    produceEvents();
}

export function produceEvents() {
    const startTime = Date.now();
    let success = false;

    try {
        // 70% событий аудита, 30% уведомлений (как в реальной нагрузке)
        if (Math.random() < 0.7) {
            // Отправка события аудита
            const event = generateAuditEvent(__VU, __ITER);

            writer.produce({
                messages: [{
                    key: encoding.b64encode(event.entityId),
                    value: encoding.b64encode(JSON.stringify(event)),
                }],
            });
        } else {
            // Отправка уведомления
            const event = generateNotificationEvent(__VU, __ITER);

            notificationWriter.produce({
                messages: [{
                    key: encoding.b64encode(event.productId),
                    value: encoding.b64encode(JSON.stringify(event)),
                }],
            });
        }

        success = true;
        kafkaMessagesProduced.add(1);

    } catch (error) {
        kafkaProduceErrors.add(1);
        console.error(`Produce error: ${error.message}`);
    }

    // Записываем метрики
    const latency = Date.now() - startTime;
    kafkaProduceLatency.add(latency);
    kafkaProduceSuccess.add(success ? 1 : 0);

    // Проверки для отчёта
    check(success, {
        'message produced successfully': (s) => s === true,
    });

    check(latency, {
        'latency < 50ms': (l) => l < 50,
        'latency < 100ms': (l) => l < 100,
    });

    // Небольшая пауза между сообщениями (10ms = ~100 msg/sec per VU)
    sleep(0.01);
}

// ═══════════════════════════════════════════════════════════════════════
// TEARDOWN
// ═══════════════════════════════════════════════════════════════════════

export function teardown(data) {
    writer.close();
    notificationWriter.close();
    console.log('Kafka writers closed');
}

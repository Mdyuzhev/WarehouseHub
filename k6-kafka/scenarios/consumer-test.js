// k6-kafka/scenarios/consumer-test.js
// Сценарий нагрузочного тестирования Kafka Consumer
// Симулирует поведение analytics-service при чтении событий
// WH-211

import { Reader } from 'k6/x/kafka';
import { check, sleep } from 'k6';
import { Counter, Trend, Gauge } from 'k6/metrics';

// ═══════════════════════════════════════════════════════════════════════
// КОНФИГУРАЦИЯ
// ═══════════════════════════════════════════════════════════════════════

const KAFKA_BROKERS = __ENV.KAFKA_BROKERS || 'kafka.warehouse.svc.cluster.local:9092';
const TOPIC_AUDIT = 'warehouse.audit';
const TOPIC_NOTIFICATIONS = 'warehouse.notifications';
const CONSUMER_GROUP = __ENV.CONSUMER_GROUP || 'k6-consumer-group';

// ═══════════════════════════════════════════════════════════════════════
// КАСТОМНЫЕ МЕТРИКИ
// ═══════════════════════════════════════════════════════════════════════

const kafkaConsumeLatency = new Trend('kafka_consume_latency_ms', true);
const kafkaMessagesConsumed = new Counter('kafka_messages_consumed_total');
const kafkaConsumeErrors = new Counter('kafka_consume_errors_total');
const kafkaBatchSize = new Trend('kafka_batch_size');
const kafkaConsumerLag = new Gauge('kafka_consumer_lag');

// ═══════════════════════════════════════════════════════════════════════
// НАСТРОЙКИ ТЕСТОВЫХ СЦЕНАРИЕВ
// ═══════════════════════════════════════════════════════════════════════

export const options = {
    scenarios: {
        // Consumer работает в нескольких потоках
        consume_audit: {
            executor: 'constant-vus',
            vus: parseInt(__ENV.K6_VUS) || 3,
            duration: __ENV.K6_DURATION || '2m',
            exec: 'consumeAuditEvents',
            tags: { scenario: 'audit_consumer' },
        },
        consume_notifications: {
            executor: 'constant-vus',
            vus: 1,
            duration: __ENV.K6_DURATION || '2m',
            exec: 'consumeNotifications',
            tags: { scenario: 'notification_consumer' },
        },
    },
    thresholds: {
        'kafka_consume_latency_ms': ['p95<200', 'p99<1000'],
        'kafka_consume_errors_total': ['count<5'],
    },
};

// ═══════════════════════════════════════════════════════════════════════
// ИНИЦИАЛИЗАЦИЯ KAFKA READERS
// ═══════════════════════════════════════════════════════════════════════

const auditReader = new Reader({
    brokers: KAFKA_BROKERS.split(','),
    topic: TOPIC_AUDIT,
    groupID: `${CONSUMER_GROUP}-audit-${__VU}`,
    startOffset: 'latest',
    // Настройки как в analytics-service
    maxWait: '1s',
    minBytes: 1,
    maxBytes: 10485760, // 10MB
});

const notificationReader = new Reader({
    brokers: KAFKA_BROKERS.split(','),
    topic: TOPIC_NOTIFICATIONS,
    groupID: `${CONSUMER_GROUP}-notifications`,
    startOffset: 'latest',
    maxWait: '500ms',
});

// ═══════════════════════════════════════════════════════════════════════
// ФУНКЦИИ ПОТРЕБЛЕНИЯ
// ═══════════════════════════════════════════════════════════════════════

export function consumeAuditEvents() {
    const startTime = Date.now();
    const batchSize = parseInt(__ENV.BATCH_SIZE) || 10;

    try {
        // Читаем batch сообщений
        const messages = auditReader.consume({
            limit: batchSize,
        });

        const latency = Date.now() - startTime;
        kafkaConsumeLatency.add(latency);

        if (messages && messages.length > 0) {
            kafkaMessagesConsumed.add(messages.length);
            kafkaBatchSize.add(messages.length);

            // Симулируем обработку как в analytics-service
            messages.forEach(msg => {
                try {
                    const event = JSON.parse(msg.value);
                    // Здесь была бы логика агрегации статистики
                    // В реальном analytics-service это обновление Redis
                } catch (parseError) {
                    console.warn(`Failed to parse message: ${parseError.message}`);
                }
            });

            check(messages, {
                'received messages': (msgs) => msgs.length > 0,
                'batch not empty': (msgs) => msgs.length >= 1,
            });

            check(latency, {
                'consume latency < 100ms': (l) => l < 100,
                'consume latency < 500ms': (l) => l < 500,
            });
        }

    } catch (error) {
        kafkaConsumeErrors.add(1);
        console.error(`Consume error: ${error.message}`);
    }

    // Пауза между poll'ами (как в реальном consumer)
    sleep(0.1); // 100ms между poll
}

export function consumeNotifications() {
    const startTime = Date.now();

    try {
        const messages = notificationReader.consume({
            limit: 5,
        });

        const latency = Date.now() - startTime;
        kafkaConsumeLatency.add(latency);

        if (messages && messages.length > 0) {
            kafkaMessagesConsumed.add(messages.length);

            messages.forEach(msg => {
                try {
                    const notification = JSON.parse(msg.value);
                    // Симуляция обработки уведомления
                    if (notification.type === 'OUT_OF_STOCK') {
                        // В реальности здесь был бы алерт
                    }
                } catch (parseError) {
                    // Ignore parse errors
                }
            });
        }

    } catch (error) {
        kafkaConsumeErrors.add(1);
    }

    sleep(0.2);
}

// ═══════════════════════════════════════════════════════════════════════
// TEARDOWN
// ═══════════════════════════════════════════════════════════════════════

export function teardown(data) {
    auditReader.close();
    notificationReader.close();
    console.log('Kafka readers closed');
}

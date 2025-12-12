// k6-kafka/scenarios/ramp-test-200vu.js
// Финальный нагрузочный тест: 200 VU с пошаговым ростом на 30 минут
// Профиль: Ramp-up → Sustain → Ramp-down

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
// КАСТОМНЫЕ МЕТРИКИ
// ═══════════════════════════════════════════════════════════════════════

const kafkaProduceLatency = new Trend('kafka_produce_latency_ms', true);
const kafkaProduceErrors = new Counter('kafka_produce_errors_total');
const kafkaMessagesProduced = new Counter('kafka_messages_produced_total');
const kafkaProduceSuccess = new Rate('kafka_produce_success_rate');

// ═══════════════════════════════════════════════════════════════════════
// ПРОФИЛЬ НАГРУЗКИ: 200 VU на 30 минут
// ═══════════════════════════════════════════════════════════════════════

export const options = {
    scenarios: {
        ramp_load: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                // Фаза 1: Прогрев (5 минут) — плавный рост до 50 VU
                { duration: '2m', target: 20 },
                { duration: '3m', target: 50 },

                // Фаза 2: Рост (5 минут) — до 100 VU
                { duration: '2m', target: 75 },
                { duration: '3m', target: 100 },

                // Фаза 3: Пиковая нагрузка (5 минут) — до 150 VU
                { duration: '2m', target: 125 },
                { duration: '3m', target: 150 },

                // Фаза 4: Максимум (5 минут) — до 200 VU
                { duration: '2m', target: 175 },
                { duration: '3m', target: 200 },

                // Фаза 5: Удержание (5 минут) — стабильные 200 VU
                { duration: '5m', target: 200 },

                // Фаза 6: Остывание (5 минут) — плавное снижение
                { duration: '2m', target: 100 },
                { duration: '2m', target: 50 },
                { duration: '1m', target: 0 },
            ],
            gracefulRampDown: '30s',
            exec: 'produceEvents',
        },
    },
    thresholds: {
        'kafka_produce_latency_ms': ['p(95)<200', 'p(99)<1000'],
        'kafka_produce_success_rate': ['rate>0.95'],
        'kafka_produce_errors_total': ['count<1000'],
    },
};

// ═══════════════════════════════════════════════════════════════════════
// KAFKA WRITERS
// ═══════════════════════════════════════════════════════════════════════

const writer = new Writer({
    brokers: KAFKA_BROKERS.split(','),
    topic: TOPIC_AUDIT,
    autoCreateTopic: true,
    requiredAcks: 1,
    batchSize: 16384,
    batchTimeout: 10,
    compression: 'none',
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
// ГЕНЕРАТОРЫ ДАННЫХ
// ═══════════════════════════════════════════════════════════════════════

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
// ОСНОВНАЯ ФУНКЦИЯ
// ═══════════════════════════════════════════════════════════════════════

export default function() {
    produceEvents();
}

export function produceEvents() {
    const startTime = Date.now();
    let success = false;

    try {
        if (Math.random() < 0.7) {
            const event = generateAuditEvent(__VU, __ITER);

            writer.produce({
                messages: [{
                    key: encoding.b64encode(event.entityId),
                    value: encoding.b64encode(JSON.stringify(event)),
                }],
            });
        } else {
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

    const latency = Date.now() - startTime;
    kafkaProduceLatency.add(latency);
    kafkaProduceSuccess.add(success ? 1 : 0);

    check(success, {
        'message produced successfully': (s) => s === true,
    });

    check(latency, {
        'latency < 100ms': (l) => l < 100,
        'latency < 500ms': (l) => l < 500,
    });

    // Интервал между сообщениями
    sleep(0.01);
}

// ═══════════════════════════════════════════════════════════════════════
// TEARDOWN
// ═══════════════════════════════════════════════════════════════════════

export function teardown(data) {
    writer.close();
    notificationWriter.close();
    console.log('=== ФИНАЛЬНЫЙ ТЕСТ ЗАВЕРШЁН ===');
    console.log('200 VU / 30 минут / пошаговый рост');
}

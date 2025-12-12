// k6-kafka/scenarios/distributed-300vu.js
// Распределённый тест: 300 VU на 6 воркерах (по 50 VU на каждом)
// Ramp-up: 0 → 300 VU с шагом 30 каждые 5 минут
// WH-217

import { Writer } from 'k6/x/kafka';
import { check, sleep } from 'k6';
import { Counter, Trend, Rate } from 'k6/metrics';
import encoding from 'k6/encoding';

// Конфигурация
const KAFKA_BROKERS = __ENV.KAFKA_BROKERS || 'kafka.warehouse.svc.cluster.local:9092';
const TOPIC_AUDIT = 'warehouse.audit';
const TOPIC_NOTIFICATIONS = 'warehouse.notifications';

// Кастомные метрики
const kafkaProduceLatency = new Trend('kafka_produce_latency_ms', true);
const kafkaProduceErrors = new Counter('kafka_produce_errors_total');
const kafkaMessagesProduced = new Counter('kafka_messages_produced_total');
const kafkaProduceSuccess = new Rate('kafka_produce_success_rate');

// Распределённый ramp-up сценарий: 0 → 300 VU
// 6 воркеров, нагрузка распределяется автоматически
export const options = {
    scenarios: {
        distributed_ramp: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '5m', target: 30 },   // 0 → 30 VU (5 VU на воркер)
                { duration: '5m', target: 60 },   // 30 → 60 VU (10 VU на воркер)
                { duration: '5m', target: 90 },   // 60 → 90 VU (15 VU на воркер)
                { duration: '5m', target: 120 },  // 90 → 120 VU (20 VU на воркер)
                { duration: '5m', target: 150 },  // 120 → 150 VU (25 VU на воркер)
                { duration: '5m', target: 180 },  // 150 → 180 VU (30 VU на воркер)
                { duration: '5m', target: 210 },  // 180 → 210 VU (35 VU на воркер)
                { duration: '5m', target: 240 },  // 210 → 240 VU (40 VU на воркер)
                { duration: '5m', target: 270 },  // 240 → 270 VU (45 VU на воркер)
                { duration: '5m', target: 300 },  // 270 → 300 VU (50 VU на воркер)
                { duration: '5m', target: 300 },  // Держим 300 VU 5 минут
            ],
            gracefulRampDown: '30s',
        },
    },
    thresholds: {
        'kafka_produce_latency_ms': ['p(95)<200', 'p(99)<1000'],
        'kafka_produce_success_rate': ['rate>0.95'],
        'kafka_produce_errors_total': ['count<100'],
    },
};

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

export default function() {
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
        'latency < 50ms': (l) => l < 50,
        'latency < 100ms': (l) => l < 100,
        'latency < 200ms': (l) => l < 200,
    });

    // Пауза между сообщениями
    sleep(0.01);
}

export function teardown(data) {
    writer.close();
    notificationWriter.close();
    console.log('Kafka writers closed');
}

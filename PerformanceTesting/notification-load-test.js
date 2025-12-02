import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const notificationDuration = new Trend('notification_duration');

const BASE_URL = __ENV.BASE_URL || 'http://192.168.1.74:31080';

export const options = {
    stages: [
        { duration: '30s', target: 10 },
        { duration: '1m', target: 50 },
        { duration: '30s', target: 0 },
    ],
    thresholds: {
        http_req_duration: ['p(95)<500'],
        errors: ['rate<0.1'],
    },
};

export function setup() {
    const loginRes = http.post(`${BASE_URL}/api/auth/login`,
        JSON.stringify({ username: 'admin', password: 'admin123' }),
        { headers: { 'Content-Type': 'application/json' } }
    );
    return { token: JSON.parse(loginRes.body).token };
}

export default function(data) {
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${data.token}`,
    };

    // IN_MEMORY чтобы не спамить Telegram
    const payload = JSON.stringify({
        channel: 'IN_MEMORY',
        subject: `Load Test ${__VU}-${__ITER}`,
        message: `Тест от VU ${__VU}, итерация ${__ITER}`,
        priority: Math.floor(Math.random() * 10) + 1,
    });

    const start = Date.now();
    const res = http.post(`${BASE_URL}/api/notifications`, payload, { headers });
    notificationDuration.add(Date.now() - start);

    errorRate.add(!check(res, {
        'status 2xx': (r) => r.status >= 200 && r.status < 300,
        'has id': (r) => JSON.parse(r.body).id !== undefined,
    }));

    sleep(0.5);
}

export function teardown(data) {
    const headers = { 'Authorization': `Bearer ${data.token}` };
    const stats = http.get(`${BASE_URL}/api/notifications/stats`, { headers });
    console.log('Final stats:', stats.body);
}

-- Миграция для создания таблицы notifications
-- WH-383: Notification Service

CREATE TABLE notifications (
    id BIGSERIAL PRIMARY KEY,
    channel VARCHAR(20) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    subject VARCHAR(255),
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    priority INTEGER NOT NULL DEFAULT 5,
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    error_message VARCHAR(1000),

    CONSTRAINT chk_channel CHECK (channel IN ('TELEGRAM', 'EMAIL', 'WEBHOOK', 'IN_MEMORY')),
    CONSTRAINT chk_status CHECK (status IN ('PENDING', 'SENDING', 'SENT', 'FAILED', 'DEAD')),
    CONSTRAINT chk_priority CHECK (priority BETWEEN 1 AND 10)
);

-- Индекс для эффективной выборки pending уведомлений по приоритету
CREATE INDEX idx_notifications_status_priority ON notifications (status, priority, created_at)
    WHERE status = 'PENDING';

-- Индекс для поиска по времени создания
CREATE INDEX idx_notifications_created_at ON notifications (created_at);

-- Комментарии к таблице и полям
COMMENT ON TABLE notifications IS 'Таблица для хранения уведомлений различных типов';
COMMENT ON COLUMN notifications.channel IS 'Канал отправки: TELEGRAM, EMAIL, WEBHOOK, IN_MEMORY';
COMMENT ON COLUMN notifications.status IS 'Статус: PENDING, SENDING, SENT, FAILED, DEAD';
COMMENT ON COLUMN notifications.priority IS 'Приоритет от 1 (lowest) до 10 (highest)';
COMMENT ON COLUMN notifications.retry_count IS 'Количество попыток отправки';

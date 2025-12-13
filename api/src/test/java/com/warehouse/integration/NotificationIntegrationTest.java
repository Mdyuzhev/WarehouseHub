package com.warehouse.integration;

import com.warehouse.config.TestSchedulingConfig;
import com.warehouse.dto.NotificationRequest;
import com.warehouse.model.Notification;
import com.warehouse.model.NotificationChannel;
import com.warehouse.model.NotificationStatus;
import com.warehouse.repository.NotificationRepository;
import com.warehouse.service.NotificationService;
import com.warehouse.service.notification.InMemoryNotificationSender;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.ActiveProfiles;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Integration тесты для Notification Service
 * Проверяют end-to-end работу сервиса с реальной БД
 *
 * Тесты вызывают processQueue() синхронно без @Transactional,
 * что позволяет данным коммититься и быть видимыми для processor.
 */
@SpringBootTest
@Import(TestSchedulingConfig.class)
@ActiveProfiles("test")
@DisplayName("Notification Integration Tests")
class NotificationIntegrationTest {

    @Autowired
    private NotificationService notificationService;

    @Autowired
    private NotificationRepository notificationRepository;

    @Autowired
    private InMemoryNotificationSender inMemorySender;

    @Autowired
    private com.warehouse.service.notification.NotificationQueueProcessor queueProcessor;

    @BeforeEach
    void setUp() {
        // Очистить in-memory sender перед каждым тестом
        inMemorySender.clear();
    }

    @AfterEach
    void tearDown() {
        // Очистить тестовые данные из БД
        notificationRepository.deleteAll();
    }

    @Test
    @DisplayName("End-to-end: Уведомление должно быть обработано и отправлено")
    void shouldProcessNotificationEndToEnd() {
        // Given: Создаём запрос на уведомление
        NotificationRequest request = NotificationRequest.builder()
                .channel(NotificationChannel.IN_MEMORY)
                .recipient("integration-test-user")
                .subject("Integration Test")
                .message("This is an integration test message")
                .priority(8)
                .build();

        // When: Отправляем уведомление
        Notification created = notificationService.send(request);
        assertThat(created.getId()).isNotNull();
        assertThat(created.getStatus()).isEqualTo(NotificationStatus.PENDING);

        // Вызываем processQueue() вручную
        queueProcessor.processQueue();

        // Then: Проверяем что уведомление обработано
        Long createdId = java.util.Objects.requireNonNull(created.getId());
        Notification processed = notificationRepository.findById(createdId).orElseThrow();
        assertThat(processed.getStatus()).isEqualTo(NotificationStatus.SENT);
        assertThat(processed.getSentAt()).isNotNull();
        assertThat(processed.getErrorMessage()).isNull();

        // Проверяем что уведомление попало в InMemorySender
        List<Notification> sentNotifications = inMemorySender.getSentNotifications();
        assertThat(sentNotifications).hasSize(1);
        assertThat(sentNotifications.get(0).getRecipient()).isEqualTo("integration-test-user");
    }

    @Test
    @DisplayName("Должен обработать уведомления с высоким приоритетом первыми")
    void shouldProcessHighPriorityFirst() {
        // Given: Создаём 3 уведомления с разным приоритетом
        NotificationRequest lowPriority = NotificationRequest.builder()
                .channel(NotificationChannel.IN_MEMORY)
                .recipient("low-priority-user")
                .message("Low priority message")
                .priority(1)
                .build();

        NotificationRequest mediumPriority = NotificationRequest.builder()
                .channel(NotificationChannel.IN_MEMORY)
                .recipient("medium-priority-user")
                .message("Medium priority message")
                .priority(5)
                .build();

        NotificationRequest highPriority = NotificationRequest.builder()
                .channel(NotificationChannel.IN_MEMORY)
                .recipient("high-priority-user")
                .message("High priority message")
                .priority(10)
                .build();

        // When: Отправляем в порядке: low, medium, high
        notificationService.send(lowPriority);
        notificationService.send(mediumPriority);
        notificationService.send(highPriority);

        // Вызываем processQueue() вручную несколько раз чтобы обработать все
        queueProcessor.processQueue();
        queueProcessor.processQueue();
        queueProcessor.processQueue();

        // Проверяем порядок: high должен быть первым
        List<Notification> sentNotifications = inMemorySender.getSentNotifications();
        assertThat(sentNotifications).hasSizeGreaterThanOrEqualTo(3);

        // Находим наши уведомления
        Notification sentHigh = sentNotifications.stream()
                .filter(n -> n.getRecipient().equals("high-priority-user"))
                .findFirst()
                .orElseThrow();

        Notification sentLow = sentNotifications.stream()
                .filter(n -> n.getRecipient().equals("low-priority-user"))
                .findFirst()
                .orElseThrow();

        // Высокий приоритет должен быть отправлен раньше низкого
        assertThat(sentHigh.getSentAt()).isBefore(sentLow.getSentAt());
    }

    @Test
    @DisplayName("Должен создать несколько уведомлений и обработать их")
    void shouldProcessMultipleNotifications() {
        // Given: Создаём 5 уведомлений
        for (int i = 0; i < 5; i++) {
            NotificationRequest request = NotificationRequest.builder()
                    .channel(NotificationChannel.IN_MEMORY)
                    .recipient("user-" + i)
                    .message("Message " + i)
                    .priority(5)
                    .build();
            notificationService.send(request);
        }

        // Вызываем processQueue() несколько раз для обработки всех уведомлений
        for (int i = 0; i < 5; i++) {
            queueProcessor.processQueue();
        }

        // Проверяем статистику
        var stats = notificationService.getStats();
        assertThat(stats.get("SENT")).isGreaterThanOrEqualTo(5L);
    }
}

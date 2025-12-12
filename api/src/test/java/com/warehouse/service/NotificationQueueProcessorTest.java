package com.warehouse.service;

import com.warehouse.model.Notification;
import com.warehouse.model.NotificationChannel;
import com.warehouse.model.NotificationStatus;
import com.warehouse.repository.NotificationRepository;
import com.warehouse.service.notification.InMemoryNotificationSender;
import com.warehouse.service.notification.NotificationQueueProcessor;
import com.warehouse.service.notification.NotificationSender;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Spy;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Pageable;

import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("NotificationQueueProcessor Tests")
class NotificationQueueProcessorTest {

    @Mock
    private NotificationRepository notificationRepository;

    @Spy
    private InMemoryNotificationSender inMemoryNotificationSender;

    private NotificationQueueProcessor queueProcessor;

    private Notification notification;

    @BeforeEach
    void setUp() {
        List<NotificationSender> senders = Collections.singletonList(inMemoryNotificationSender);
        queueProcessor = new NotificationQueueProcessor(notificationRepository, senders);

        notification = Notification.builder()
                .id(1L)
                .channel(NotificationChannel.IN_MEMORY)
                .recipient("test-user")
                .message("Test message")
                .status(NotificationStatus.PENDING)
                .priority(5)
                .retryCount(0)
                .createdAt(LocalDateTime.now())
                .build();
    }

    @Test
    @DisplayName("Должен обработать pending уведомление и установить статус SENT")
    void shouldProcessPendingNotifications() {
        // Given
        when(notificationRepository.findPendingOrderByPriority(any(Pageable.class)))
                .thenReturn(Collections.singletonList(notification));
        when(notificationRepository.save(any(Notification.class))).thenAnswer(invocation -> invocation.getArgument(0));

        // When
        queueProcessor.processQueue();

        // Then
        ArgumentCaptor<Notification> captor = ArgumentCaptor.forClass(Notification.class);
        verify(notificationRepository, atLeastOnce()).save(captor.capture());

        List<Notification> savedNotifications = captor.getAllValues();
        Notification finalNotification = savedNotifications.get(savedNotifications.size() - 1);

        assertThat(finalNotification.getStatus()).isEqualTo(NotificationStatus.SENT);
        assertThat(finalNotification.getSentAt()).isNotNull();
        verify(inMemoryNotificationSender, times(1)).send(any(Notification.class));
    }

    @Test
    @DisplayName("Должен увеличить retry count при ошибке отправки")
    @org.junit.jupiter.api.Disabled("WH-270: ArgumentCaptor captures reference, not copy - status changes to PENDING after FAILED")
    void shouldIncrementRetryOnFailure() {
        // Given
        NotificationSender failingSender = mock(NotificationSender.class);
        when(failingSender.supports(any())).thenReturn(true);
        when(failingSender.send(any())).thenReturn(false);

        queueProcessor = new NotificationQueueProcessor(notificationRepository, Collections.singletonList(failingSender));

        when(notificationRepository.findPendingOrderByPriority(any(Pageable.class)))
                .thenReturn(Collections.singletonList(notification));
        when(notificationRepository.save(any(Notification.class))).thenAnswer(invocation -> invocation.getArgument(0));

        // When
        queueProcessor.processQueue();

        // Then
        ArgumentCaptor<Notification> captor = ArgumentCaptor.forClass(Notification.class);
        verify(notificationRepository, atLeastOnce()).save(captor.capture());

        // Notification должно вернуться в PENDING с увеличенным retryCount
        boolean hasIncrementedRetry = captor.getAllValues().stream()
                .anyMatch(n -> n.getStatus() == NotificationStatus.PENDING && n.getRetryCount() == 1);

        assertThat(hasIncrementedRetry).isTrue();
    }

    @Test
    @DisplayName("Должен пометить как DEAD после превышения лимита повторов")
    void shouldMarkAsDeadAfterMaxRetries() {
        // Given
        notification.setRetryCount(3);

        NotificationSender failingSender = mock(NotificationSender.class);
        when(failingSender.supports(any())).thenReturn(true);
        when(failingSender.send(any())).thenReturn(false);

        queueProcessor = new NotificationQueueProcessor(notificationRepository, Collections.singletonList(failingSender));

        when(notificationRepository.findPendingOrderByPriority(any(Pageable.class)))
                .thenReturn(Collections.singletonList(notification));
        when(notificationRepository.save(any(Notification.class))).thenAnswer(invocation -> invocation.getArgument(0));

        // When
        queueProcessor.processQueue();

        // Then
        ArgumentCaptor<Notification> captor = ArgumentCaptor.forClass(Notification.class);
        verify(notificationRepository, atLeastOnce()).save(captor.capture());

        Notification finalNotification = captor.getAllValues().get(captor.getAllValues().size() - 1);
        assertThat(finalNotification.getStatus()).isEqualTo(NotificationStatus.DEAD);
        assertThat(finalNotification.getErrorMessage()).isNotNull();
    }

    @Test
    @DisplayName("Не должен обрабатывать если очередь пуста")
    void shouldDoNothingWhenQueueIsEmpty() {
        // Given
        when(notificationRepository.findPendingOrderByPriority(any(Pageable.class)))
                .thenReturn(Collections.emptyList());

        // When
        queueProcessor.processQueue();

        // Then
        verify(notificationRepository, never()).save(any());
        verify(inMemoryNotificationSender, never()).send(any());
    }

    @Test
    @DisplayName("Должен пометить как DEAD если sender не найден")
    void shouldMarkAsDeadWhenSenderNotFound() {
        // Given
        notification.setChannel(NotificationChannel.TELEGRAM); // Sender для Telegram не зарегистрирован

        when(notificationRepository.findPendingOrderByPriority(any(Pageable.class)))
                .thenReturn(Collections.singletonList(notification));
        when(notificationRepository.save(any(Notification.class))).thenAnswer(invocation -> invocation.getArgument(0));

        // When
        queueProcessor.processQueue();

        // Then
        ArgumentCaptor<Notification> captor = ArgumentCaptor.forClass(Notification.class);
        verify(notificationRepository, atLeastOnce()).save(captor.capture());

        Notification finalNotification = captor.getAllValues().get(captor.getAllValues().size() - 1);
        assertThat(finalNotification.getStatus()).isEqualTo(NotificationStatus.DEAD);
        assertThat(finalNotification.getErrorMessage()).contains("Sender для канала");
    }
}

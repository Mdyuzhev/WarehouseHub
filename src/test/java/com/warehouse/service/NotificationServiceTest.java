package com.warehouse.service;

import com.warehouse.dto.NotificationRequest;
import com.warehouse.model.Notification;
import com.warehouse.model.NotificationChannel;
import com.warehouse.model.NotificationStatus;
import com.warehouse.repository.NotificationRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Map;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("NotificationService Tests")
class NotificationServiceTest {

    @Mock
    private NotificationRepository notificationRepository;

    @InjectMocks
    private NotificationService notificationService;

    private NotificationRequest request;
    private Notification notification;

    @BeforeEach
    void setUp() {
        request = NotificationRequest.builder()
                .channel(NotificationChannel.IN_MEMORY)
                .recipient("test-user")
                .subject("Test Subject")
                .message("Test message")
                .priority(5)
                .build();

        notification = Notification.builder()
                .id(1L)
                .channel(NotificationChannel.IN_MEMORY)
                .recipient("test-user")
                .subject("Test Subject")
                .message("Test message")
                .status(NotificationStatus.PENDING)
                .priority(5)
                .retryCount(0)
                .build();
    }

    @Test
    @DisplayName("Должен создать уведомление со статусом PENDING")
    void shouldCreateNotificationWithPendingStatus() {
        // Given
        when(notificationRepository.save(any(Notification.class))).thenReturn(notification);

        // When
        Notification result = notificationService.send(request);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getStatus()).isEqualTo(NotificationStatus.PENDING);
        assertThat(result.getChannel()).isEqualTo(NotificationChannel.IN_MEMORY);
        assertThat(result.getRecipient()).isEqualTo("test-user");
        verify(notificationRepository, times(1)).save(any(Notification.class));
    }

    @Test
    @DisplayName("Должен установить приоритет по умолчанию 5 если не указан")
    void shouldSetDefaultPriority() {
        // Given
        request.setPriority(null);
        when(notificationRepository.save(any(Notification.class))).thenAnswer(invocation -> {
            Notification saved = invocation.getArgument(0);
            saved.setId(1L);
            return saved;
        });

        // When
        Notification result = notificationService.send(request);

        // Then
        assertThat(result).isNotNull();
        assertThat(result.getPriority()).isEqualTo(5);
        verify(notificationRepository, times(1)).save(any(Notification.class));
    }

    @Test
    @DisplayName("Должен найти уведомление по ID")
    void shouldFindNotificationById() {
        // Given
        when(notificationRepository.findById(1L)).thenReturn(Optional.of(notification));

        // When
        Optional<Notification> result = notificationService.findById(1L);

        // Then
        assertThat(result).isPresent();
        assertThat(result.get().getId()).isEqualTo(1L);
        verify(notificationRepository, times(1)).findById(1L);
    }

    @Test
    @DisplayName("Должен вернуть пустой Optional если уведомление не найдено")
    void shouldReturnEmptyOptionalWhenNotFound() {
        // Given
        when(notificationRepository.findById(999L)).thenReturn(Optional.empty());

        // When
        Optional<Notification> result = notificationService.findById(999L);

        // Then
        assertThat(result).isEmpty();
        verify(notificationRepository, times(1)).findById(999L);
    }

    @Test
    @DisplayName("Должен вернуть статистику по всем статусам")
    void shouldReturnStatsForAllStatuses() {
        // Given
        when(notificationRepository.countByStatus(NotificationStatus.PENDING)).thenReturn(5L);
        when(notificationRepository.countByStatus(NotificationStatus.SENDING)).thenReturn(2L);
        when(notificationRepository.countByStatus(NotificationStatus.SENT)).thenReturn(10L);
        when(notificationRepository.countByStatus(NotificationStatus.FAILED)).thenReturn(1L);
        when(notificationRepository.countByStatus(NotificationStatus.DEAD)).thenReturn(0L);
        when(notificationRepository.count()).thenReturn(18L);

        // When
        Map<String, Long> stats = notificationService.getStats();

        // Then
        assertThat(stats).isNotNull();
        assertThat(stats.get("PENDING")).isEqualTo(5L);
        assertThat(stats.get("SENDING")).isEqualTo(2L);
        assertThat(stats.get("SENT")).isEqualTo(10L);
        assertThat(stats.get("FAILED")).isEqualTo(1L);
        assertThat(stats.get("DEAD")).isEqualTo(0L);
        assertThat(stats.get("TOTAL")).isEqualTo(18L);
    }
}

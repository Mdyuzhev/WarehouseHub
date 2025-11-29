package com.warehouse.service;

import com.warehouse.config.KafkaConfig;
import com.warehouse.dto.AuditEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.UUID;

/**
 * Audit Service - sends all CRUD operations to Kafka audit topic.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class AuditService {

    private final KafkaTemplate<String, Object> kafkaTemplate;

    @Async
    public void logProductCreate(Long productId, String productName, String username) {
        sendAuditEvent(AuditEvent.builder()
                .eventId(UUID.randomUUID().toString())
                .eventType("CREATE")
                .entityType("PRODUCT")
                .entityId(productId)
                .entityName(productName)
                .username(username)
                .action("Product created")
                .details("New product added to inventory")
                .timestamp(Instant.now())
                .build());
    }

    @Async
    public void logProductUpdate(Long productId, String productName, String username) {
        sendAuditEvent(AuditEvent.builder()
                .eventId(UUID.randomUUID().toString())
                .eventType("UPDATE")
                .entityType("PRODUCT")
                .entityId(productId)
                .entityName(productName)
                .username(username)
                .action("Product updated")
                .details("Product information modified")
                .timestamp(Instant.now())
                .build());
    }

    @Async
    public void logProductDelete(Long productId, String username) {
        sendAuditEvent(AuditEvent.builder()
                .eventId(UUID.randomUUID().toString())
                .eventType("DELETE")
                .entityType("PRODUCT")
                .entityId(productId)
                .username(username)
                .action("Product deleted")
                .details("Product removed from inventory")
                .timestamp(Instant.now())
                .build());
    }

    @Async
    public void logUserLogin(String username, boolean success) {
        sendAuditEvent(AuditEvent.builder()
                .eventId(UUID.randomUUID().toString())
                .eventType("LOGIN")
                .entityType("USER")
                .entityName(username)
                .username(username)
                .action(success ? "Login successful" : "Login failed")
                .details(success ? "User authenticated" : "Authentication failed")
                .timestamp(Instant.now())
                .build());
    }

    @Async
    public void logUserLogout(String username) {
        sendAuditEvent(AuditEvent.builder()
                .eventId(UUID.randomUUID().toString())
                .eventType("LOGOUT")
                .entityType("USER")
                .entityName(username)
                .username(username)
                .action("User logged out")
                .details("Session terminated")
                .timestamp(Instant.now())
                .build());
    }

    private void sendAuditEvent(AuditEvent event) {
        try {
            kafkaTemplate.send(KafkaConfig.AUDIT_TOPIC, event.getEntityType(), event)
                    .whenComplete((result, ex) -> {
                        if (ex != null) {
                            log.error("Failed to send audit event: {}", ex.getMessage());
                        } else {
                            log.debug("Audit event sent: {} - {}", event.getEventType(), event.getEntityType());
                        }
                    });
        } catch (Exception e) {
            log.error("Error sending audit event: {}", e.getMessage());
        }
    }
}

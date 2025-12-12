package com.warehouse.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;

/**
 * Audit event for Kafka warehouse.audit topic.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AuditEvent {
    private String eventId;
    private String eventType;  // CREATE, UPDATE, DELETE, LOGIN, LOGOUT
    private String entityType; // PRODUCT, USER
    private Long entityId;
    private String entityName;
    private String username;
    private String action;
    private String details;
    private Instant timestamp;
}

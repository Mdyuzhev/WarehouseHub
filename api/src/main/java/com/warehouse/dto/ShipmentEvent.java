package com.warehouse.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Kafka event для shipment transitions
 * WH-274: Kafka Auto-Documents - Блок 2
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ShipmentEvent {

    /**
     * Тип события
     */
    private String eventType; // DISPATCHED, DELIVERED

    /**
     * ID отправки
     */
    private Long shipmentId;

    /**
     * Номер документа
     */
    private String documentNumber;

    /**
     * Объект-источник
     */
    private Long sourceFacilityId;

    /**
     * Объект-назначение
     */
    private Long destinationFacilityId;

    /**
     * Позиции
     */
    private List<ShipmentItemDTO> items;

    /**
     * Временная метка
     */
    @Builder.Default
    private LocalDateTime timestamp = LocalDateTime.now();
}

package com.warehouse.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * Расходная накладная (отгрузка товара)
 * WH-273: Shipment Documents
 *
 * State Machine: DRAFT → APPROVED → SHIPPED → DELIVERED
 * - APPROVED: резервирует stock (stock.reserved += quantity)
 * - SHIPPED: списывает stock (stock.quantity -= quantity, stock.reserved -= quantity)
 */
@Entity
@Table(name = "shipment_documents")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ShipmentDocument {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * Номер документа
     * Формат: SHP-{sourceFacilityCode}-{YYYYMMDD}-{seq}
     * Пример: SHP-WH-C-001-20251211-001
     */
    @Column(name = "document_number", unique = true, nullable = false, length = 50)
    private String documentNumber;

    /**
     * Объект-источник (откуда отгружается товар)
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "source_facility_id", nullable = false)
    private Facility sourceFacility;

    /**
     * Объект-получатель (куда отгружается, если внутри сети)
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "destination_facility_id")
    private Facility destinationFacility;

    /**
     * Адрес доставки (если внешний клиент, не объект сети)
     */
    @Column(name = "destination_address", length = 500)
    private String destinationAddress;

    /**
     * Статус документа
     */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private ShipmentStatus status = ShipmentStatus.DRAFT;

    /**
     * Примечания
     */
    @Column(columnDefinition = "TEXT")
    private String notes;

    /**
     * Создан пользователем
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "created_by")
    private User createdBy;

    /**
     * Дата создания
     */
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    /**
     * Дата последнего изменения
     */
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    /**
     * Утверждён пользователем
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "approved_by")
    private User approvedBy;

    /**
     * Дата утверждения (stock резервируется)
     */
    @Column(name = "approved_at")
    private LocalDateTime approvedAt;

    /**
     * Отгружен пользователем
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "shipped_by")
    private User shippedBy;

    /**
     * Дата отгрузки (stock списывается)
     */
    @Column(name = "shipped_at")
    private LocalDateTime shippedAt;

    /**
     * Дата доставки
     */
    @Column(name = "delivered_at")
    private LocalDateTime deliveredAt;

    /**
     * Позиции документа
     */
    @OneToMany(mappedBy = "shipmentDocument", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private List<ShipmentItem> items = new ArrayList<>();

    @PrePersist
    protected void onCreate() {
        LocalDateTime now = LocalDateTime.now();
        if (createdAt == null) {
            createdAt = now;
        }
        updatedAt = now;
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }

    /**
     * Helper method to add item
     */
    public void addItem(ShipmentItem item) {
        items.add(item);
        item.setShipmentDocument(this);
    }

    /**
     * Helper method to remove item
     */
    public void removeItem(ShipmentItem item) {
        items.remove(item);
        item.setShipmentDocument(null);
    }
}

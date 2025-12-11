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
 * Приходная накладная
 * WH-272: Receipt Documents
 *
 * State Machine: DRAFT → APPROVED → CONFIRMED → COMPLETED
 */
@Entity
@Table(name = "receipt_documents")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReceiptDocument {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * Номер документа
     * Формат: RCP-{facilityCode}-{YYYYMMDD}-{seq}
     * Пример: RCP-WH-C-001-20251211-001
     */
    @Column(name = "document_number", unique = true, nullable = false, length = 50)
    private String documentNumber;

    /**
     * Объект, на который приходит товар
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "facility_id", nullable = false)
    private Facility facility;

    /**
     * Исходная отправка (для авто-созданных поступлений через Kafka)
     * WH-274: Kafka Auto-Documents
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "source_shipment_id")
    private ShipmentDocument sourceShipment;

    /**
     * Название поставщика
     */
    @Column(name = "supplier_name", length = 255)
    private String supplierName;

    /**
     * Статус документа
     */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private ReceiptStatus status = ReceiptStatus.DRAFT;

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
     * Утвержден пользователем
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "approved_by")
    private User approvedBy;

    /**
     * Дата утверждения
     */
    @Column(name = "approved_at")
    private LocalDateTime approvedAt;

    /**
     * Подтвержден пользователем (товар принят)
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "confirmed_by")
    private User confirmedBy;

    /**
     * Дата подтверждения
     */
    @Column(name = "confirmed_at")
    private LocalDateTime confirmedAt;

    /**
     * Позиции документа
     */
    @OneToMany(mappedBy = "receiptDocument", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private List<ReceiptItem> items = new ArrayList<>();

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
    public void addItem(ReceiptItem item) {
        items.add(item);
        item.setReceiptDocument(this);
    }

    /**
     * Helper method to remove item
     */
    public void removeItem(ReceiptItem item) {
        items.remove(item);
        item.setReceiptDocument(null);
    }
}

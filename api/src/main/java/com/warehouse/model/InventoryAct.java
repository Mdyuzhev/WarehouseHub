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
 * Акт инвентаризации
 * WH-275: Inventory Acts
 *
 * State Machine: DRAFT → COMPLETED
 * - COMPLETED: stock correction based on difference (actual - expected)
 */
@Entity
@Table(name = "inventory_acts")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class InventoryAct {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * Номер документа
     * Формат: INV-{facilityCode}-{YYYYMMDD}-{seq}
     * Пример: INV-WH-C-001-20251211-001
     */
    @Column(name = "document_number", unique = true, nullable = false, length = 50)
    private String documentNumber;

    /**
     * Склад/ПВЗ
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "facility_id", nullable = false)
    private Facility facility;

    /**
     * Статус документа
     */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private InventoryStatus status = InventoryStatus.DRAFT;

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
     * Завершен пользователем
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "completed_by")
    private User completedBy;

    /**
     * Дата завершения
     */
    @Column(name = "completed_at")
    private LocalDateTime completedAt;

    /**
     * Позиции документа
     */
    @OneToMany(mappedBy = "inventoryAct", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    @Builder.Default
    private List<InventoryActItem> items = new ArrayList<>();

    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = LocalDateTime.now();
        }
    }

    /**
     * Добавить позицию
     */
    public void addItem(InventoryActItem item) {
        items.add(item);
        item.setInventoryAct(this);
    }

    /**
     * Удалить позицию
     */
    public void removeItem(InventoryActItem item) {
        items.remove(item);
        item.setInventoryAct(null);
    }
}

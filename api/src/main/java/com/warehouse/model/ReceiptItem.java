package com.warehouse.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * Позиция приходной накладной
 * WH-272: Receipt Documents
 */
@Entity
@Table(name = "receipt_items")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReceiptItem {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * Родительский документ
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "receipt_id", nullable = false)
    private ReceiptDocument receiptDocument;

    /**
     * Товар
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "product_id", nullable = false)
    private Product product;

    /**
     * Ожидаемое количество
     */
    @Column(name = "expected_quantity", nullable = false)
    private Integer expectedQuantity;

    /**
     * Фактически принятое количество
     */
    @Column(name = "actual_quantity")
    @Builder.Default
    private Integer actualQuantity = 0;

    /**
     * Дата создания
     */
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = LocalDateTime.now();
        }
    }
}

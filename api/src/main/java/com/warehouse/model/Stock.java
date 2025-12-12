package com.warehouse.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

/**
 * Остатки товаров на объектах логистической сети
 * WH-270: Product/Stock Separation
 */
@Entity
@Table(name = "stock", uniqueConstraints = {
    @UniqueConstraint(columnNames = {"product_id", "facility_id"})
})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Stock {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "product_id", nullable = false)
    private Product product;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "facility_id", nullable = false)
    private Facility facility;

    @Column(nullable = false)
    private Integer quantity;

    @Column(nullable = false)
    @Builder.Default
    private Integer reserved = 0;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }

    /**
     * Вычисляемое поле: доступно для резервирования
     */
    public Integer getAvailable() {
        return quantity - reserved;
    }
}

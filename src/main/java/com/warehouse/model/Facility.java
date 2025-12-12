package com.warehouse.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * Сущность объекта логистической сети
 *
 * Иерархия:
 * - DC (Distribution Center) - корневой уровень, parentId = null
 * - WH (Warehouse) - привязан к DC
 * - PP (Pickup Point) - привязан к WH
 */
@Entity
@Table(name = "facilities")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Facility {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * Уникальный код объекта
     * Формат:
     * - DC: DC-001, DC-002, ...
     * - WH: WH-C-001, WH-N-002, ... (регион + номер)
     * - PP: PP-C-001-01, PP-N-002-03, ... (регион + склад + номер)
     */
    @Column(unique = true, nullable = false, length = 20)
    private String code;

    /**
     * Тип объекта: DC, WH, PP
     */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 10)
    private FacilityType type;

    /**
     * Название объекта
     */
    @Column(nullable = false, length = 255)
    private String name;

    /**
     * ID родительского объекта
     * - DC: null (корневой)
     * - WH: ID распределительного центра
     * - PP: ID склада
     */
    @Column(name = "parent_id")
    private Long parentId;

    /**
     * Адрес объекта
     */
    @Column(length = 500)
    private String address;

    /**
     * Статус: ACTIVE, INACTIVE, CLOSED
     */
    @Column(nullable = false, length = 20)
    private String status;

    /**
     * Дата и время создания
     */
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    /**
     * Автоматическая установка значений при создании
     */
    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = LocalDateTime.now();
        }
        if (status == null) {
            status = "ACTIVE";
        }
    }
}
